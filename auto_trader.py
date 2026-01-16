"""
Automated Trade Executor
Executes trades automatically based on bot signals
Integrated with 4-Pillar System (Entry Strategies, Risk Management, Journal)
"""
from typing import Dict, Optional, List
from datetime import datetime
from utils.logger import logger
from auto_config import AutoTradingConfig
from paper_trading import PaperTradingSimulator
from safety_manager import SafetyManager
from entry_strategies import EntryStrategies, StrategyType
from market_regime_filter import MarketRegime

class AutoTradeExecutor:
    """Automatically executes trades based on signals"""
    
    def __init__(self, simulator: PaperTradingSimulator, 
                 safety_manager: SafetyManager,
                 config: AutoTradingConfig,
                 notification_controller=None):
        """
        Initialize auto trade executor
        """
        self.simulator = simulator
        self.safety = safety_manager
        self.config = config
        self.notifier = notification_controller
        
        # Strategies
        self.entry_strategies = EntryStrategies()
        
        # Track highest prices for trailing stop
        self.highest_prices = {}
    
    def execute_signal(self, analysis: Dict, current_price: float, market_data: Dict) -> bool:
        """
        Execute trade based on 4-pillar analysis
        """
        symbol = analysis['symbol']
        regime = analysis.get('regime')
        
        # Update entry strategies history
        entry_signal = self.entry_strategies.analyze_entry(
            symbol, market_data, regime
        )
        
        # Check for BUY opportunities
        if entry_signal.is_valid and analysis['decision'] == "🟢 MUA (SIGNAL)":
            return self._process_buy_signal(symbol, current_price, entry_signal, regime)
            
        # Check for SELL opportunities
        if symbol in self.simulator.positions:
            # Sell if signal is explicitly SELL or regime is dangerous
            if analysis['decision'] == "🔴 BÁN/CẮT" or regime == MarketRegime.VOLATILE_SHOCK.value:
                return self._execute_sell(symbol, current_price, 100, "Exit signal or dangerous regime")
                
        return False
    
    def _process_buy_signal(self, symbol: str, price: float, 
                           signal: 'EntrySignal', regime: str) -> bool:
        """Process a valid buy signal"""
        # Calculate safe position size (Trụ 3: Risk Management)
        current_capital = self.simulator.get_portfolio_value({symbol: price}) # Estimate
        cash_available = self.simulator.cash
        
        shares, pos_value, risk_amount = self.safety.calculate_position_size(
            price, signal.stop_loss, current_capital
        )
        
        # Check if we have enough cash
        if pos_value > cash_available:
            logger.warning(f"Insufficient cash for {symbol}: Needed {pos_value:,.0f}, Have {cash_available:,.0f}")
            return False
            
        # Validate with safety manager
        num_positions = len(self.simulator.positions)
        is_valid, validation_msg = self.safety.validate_trade(
            symbol, 'BUY', shares, num_positions, current_capital
        )
        
        if not is_valid:
            logger.warning(f"❌ Trade rejected: {validation_msg}")
            return False
        
        # Execute Buy
        reason = f"{signal.strategy.value.upper()} Entry (Conf: {signal.confidence}%)"
        success = self.simulator.buy(symbol, price, pos_value, reason)
        
        if success:
            # Set SL/TP in Safety Manager
            self.safety.set_stop_loss(symbol, signal.stop_loss)
            self.safety.set_take_profit(symbol, signal.take_profit_1, signal.take_profit_2)
            
            # Initialize trailing
            self.highest_prices[symbol] = price
            
            # Record in Journal (Trụ 4)
            data = {
                'time': datetime.now(),
                'symbol': symbol,
                'action': 'BUY',
                'price': price,
                'shares': shares,
                'total': pos_value,
                'reason': reason
            }
            
            self.safety.record_entry(
                trade_data=data,
                strategy=signal.strategy.value,
                regime=regime,
                sl=signal.stop_loss,
                tp1=signal.take_profit_1,
                tp2=signal.take_profit_2,
                rr=signal.risk_reward,
                risk=risk_amount
            )
            
            # Notify (Critical)
            if self.notifier:
                data['strategy'] = signal.strategy.value
                self.notifier.send_trade_alert(data)
                
            logger.info(f"✅ BUY {symbol}: {shares} shares @ {price:,.0f} (Risk: {risk_amount:,.0f})")
            return True
            
        return False
    
    def _execute_sell(self, symbol: str, price: float, percentage: float, reason: str) -> bool:
        """Execute sell order"""
        if symbol not in self.simulator.positions:
            return False
        
        # Execute sell
        success = self.simulator.sell(symbol, price, percentage, reason)
        
        if success:
            last_trade = self.simulator.trades[-1]
            pnl = last_trade.get('pnl', 0)
            pnl_pct = last_trade.get('pnl_percentage', 0)
            
            # Record Exit in Journal
            self.safety.record_exit(symbol, last_trade)
            
            # Remove safety tracking if fully sold
            if symbol not in self.simulator.positions:
                if symbol in self.safety.stop_losses:
                    del self.safety.stop_losses[symbol]
                if symbol in self.safety.take_profits:
                    del self.safety.take_profits[symbol]
                if symbol in self.highest_prices:
                    del self.highest_prices[symbol]
            
            # Notify
            if self.notifier:
                self.notifier.send_trade_alert(last_trade)
                
            logger.info(f"✅ SELL {symbol}: {reason} (P&L: {pnl:+,.0f})")
            return True
        
        return False
    
    def check_and_execute_stop_losses(self, current_prices: Dict[str, float]) -> List[str]:
        """Check stop-losses"""
        triggered = self.safety.check_stop_losses(self.simulator.positions, current_prices)
        
        executed = []
        for trigger in triggered:
            symbol = trigger['symbol']
            price = current_prices[symbol]
            
            success = self._execute_sell(symbol, price, 100, f"STOP-LOSS (Reason: {trigger['reason']})")
            if success:
                executed.append(symbol)
                # Notify specific SL alert
                if self.notifier:
                    last_trade = self.simulator.trades[-1]
                    self.notifier.send_stop_loss_alert(symbol, price, last_trade.get('pnl', 0))
        
        return executed
    
    def update_trailing_stops(self, current_prices: Dict[str, float]):
        """Update trailing stops based on logic in SafetyManager"""
        for symbol in self.simulator.positions.keys():
            if symbol not in current_prices:
                continue
            
            current_price = current_prices[symbol]
            
            # Update highest price
            if symbol not in self.highest_prices:
                self.highest_prices[symbol] = current_price
            elif current_price > self.highest_prices[symbol]:
                self.highest_prices[symbol] = current_price
            
            # Ask safety manager to update stops if applicable
            self.safety.update_trailing_stop(symbol, current_price, self.highest_prices[symbol])
    
    def check_take_profit(self, current_prices: Dict[str, float]) -> List[str]:
        """Check take profit levels (Partial scaling out)"""
        # This implementation can be enhanced to support partial TP
        # For now, simplistic approach or delegate to advanced logic if needed
        return [] # TODO: Implement partial TP logic

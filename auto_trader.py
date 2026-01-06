"""
Automated Trade Executor
Executes trades automatically based on bot signals
"""
from typing import Dict, Optional, List
from datetime import datetime
from utils.logger import logger
from auto_config import AutoTradingConfig
from paper_trading import PaperTradingSimulator
from safety_manager import SafetyManager

class AutoTradeExecutor:
    """Automatically executes trades based on signals"""
    
    def __init__(self, simulator: PaperTradingSimulator, 
                 safety_manager: SafetyManager,
                 config: AutoTradingConfig):
        """
        Initialize auto trade executor
        
        Args:
            simulator: Paper trading simulator
            safety_manager: Safety manager
            config: Trading configuration
        """
        self.simulator = simulator
        self.safety = safety_manager
        self.config = config
        
        # Track highest prices for trailing stop
        self.highest_prices = {}
    
    def execute_signal(self, analysis: Dict, current_price: float) -> bool:
        """
        Execute trade based on analysis signal
        
        Args:
            analysis: Analysis result from 3-Agent
            current_price: Current market price
            
        Returns:
            True if trade executed
        """
        symbol = analysis['symbol']
        confidence = analysis['confidence']
        decision = analysis['decision']
        
        logger.info(f"🤖 Processing signal for {symbol}: {decision} (Confidence: {confidence}%)")
        logger.info(f"   📊 Bullish signals: {len(analysis.get('bullish_case', []))}, Bearish: {len(analysis.get('bearish_case', []))}")
        
        # Determine action based on decision
        if '🟢' in decision and confidence >= self.config.MIN_CONFIDENCE_TO_BUY:
            return self._execute_buy(symbol, current_price, confidence, "Strong buy signal")
        
        elif '🟡' in decision and confidence >= self.config.MIN_CONFIDENCE_TO_ACCUMULATE:
            return self._execute_buy(symbol, current_price, confidence, "Accumulation signal")
        
        elif '🔴' in decision or confidence < self.config.MIN_CONFIDENCE_TO_SELL:
            # Sell if we have a position
            if symbol in self.simulator.positions:
                return self._execute_sell(symbol, current_price, 100, "Exit signal - low confidence")
        else:
            logger.debug(f"   ⏸️  No action: Confidence {confidence}% below thresholds (Buy: {self.config.MIN_CONFIDENCE_TO_BUY}%, Accumulate: {self.config.MIN_CONFIDENCE_TO_ACCUMULATE}%)")
        
        return False
    
    def _execute_buy(self, symbol: str, price: float, confidence: int, reason: str) -> bool:
        """Execute buy order"""
        try:
            # Calculate position size based on confidence
            confidence_factor = min(confidence / 100, 0.75)  # Max 75%
            base_allocation = self.config.MAX_POSITION_SIZE * confidence_factor
            
            # Ensure minimum allocation
            allocation = max(base_allocation, self.config.MIN_POSITION_SIZE)
            allocation = min(allocation, self.config.MAX_POSITION_SIZE)
            
            position_value = self.simulator.cash * allocation
            
            # Validate with safety manager
            num_positions = len(self.simulator.positions)
            current_capital = self.simulator.get_portfolio_value({symbol: price})
            
            is_valid, validation_msg = self.safety.validate_trade(
                symbol, 'BUY', position_value, num_positions, current_capital
            )
            
            if not is_valid:
                logger.warning(f"❌ Trade rejected: {validation_msg}")
                return False
            
            # Execute buy
            success = self.simulator.buy(symbol, price, position_value, reason)
            
            if success:
                # Set stop-loss
                avg_price = self.simulator.positions[symbol]['avg_price']
                self.safety.set_stop_loss(symbol, avg_price)
                
                # Initialize highest price for trailing stop
                self.highest_prices[symbol] = price
                
                # Record trade
                self.safety.record_trade(symbol, 'BUY')
                
                logger.info(f"✅ BUY executed: {symbol} @ {price:,.0f} VND")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error executing buy for {symbol}: {e}")
            return False
    
    def _execute_sell(self, symbol: str, price: float, percentage: float, reason: str) -> bool:
        """Execute sell order"""
        try:
            if symbol not in self.simulator.positions:
                return False
            
            # Execute sell
            success = self.simulator.sell(symbol, price, percentage, reason)
            
            if success:
                # Get P&L from last trade
                last_trade = self.simulator.trades[-1]
                pnl = last_trade.get('pnl', 0)
                
                # Record trade with P&L
                self.safety.record_trade(symbol, 'SELL', pnl)
                
                # Remove stop-loss if fully sold
                if symbol not in self.simulator.positions and symbol in self.safety.stop_losses:
                    del self.safety.stop_losses[symbol]
                    del self.highest_prices[symbol]
                
                logger.info(f"✅ SELL executed: {symbol} @ {price:,.0f} VND (P&L: {pnl:+,.0f})")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error executing sell for {symbol}: {e}")
            return False
    
    def check_and_execute_stop_losses(self, current_prices: Dict[str, float]) -> List[str]:
        """Check stop-losses and execute sells if triggered"""
        triggered = self.safety.check_stop_losses(self.simulator.positions, current_prices)
        
        for symbol in triggered:
            price = current_prices[symbol]
            self._execute_sell(symbol, price, 100, "STOP-LOSS TRIGGERED")
        
        return triggered
    
    def update_trailing_stops(self, current_prices: Dict[str, float]):
        """Update trailing stops for all positions"""
        for symbol in self.simulator.positions.keys():
            if symbol not in current_prices:
                continue
            
            current_price = current_prices[symbol]
            
            # Update highest price
            if symbol not in self.highest_prices:
                self.highest_prices[symbol] = current_price
            elif current_price > self.highest_prices[symbol]:
                self.highest_prices[symbol] = current_price
            
            # Update trailing stop
            self.safety.update_trailing_stop(symbol, current_price, self.highest_prices[symbol])
    
    def check_take_profit(self, current_prices: Dict[str, float]) -> List[str]:
        """Check and execute take profit orders"""
        executed = []
        
        for symbol, pos in self.simulator.positions.items():
            if symbol not in current_prices:
                continue
            
            current_price = current_prices[symbol]
            avg_price = pos['avg_price']
            
            # Calculate gain
            gain_pct = ((current_price / avg_price) - 1)
            
            # Take profit if gain >= threshold
            if gain_pct >= self.config.TAKE_PROFIT_PCT:
                # Sell 50% of position
                self._execute_sell(symbol, current_price, 50, 
                                  f"TAKE PROFIT (+{gain_pct * 100:.1f}%)")
                executed.append(symbol)
        
        return executed

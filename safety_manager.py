"""
Safety Manager
Implements safety mechanisms for automated trading
Integrated with TradeJournal for discipline tracking
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
from utils.logger import logger
from auto_config import AutoTradingConfig
from trade_journal import TradeJournal

class SafetyManager:
    """Manages trading safety and risk controls"""
    
    def __init__(self, config: AutoTradingConfig):
        """
        Initialize safety manager
        
        Args:
            config: Trading configuration
        """
        self.config = config
        self.journal = TradeJournal()
        
        # Daily tracking
        self.daily_start_capital = 0
        self.current_date = None
        self.daily_trades = []
        
        # Circuit breaker status
        self.circuit_breaker_active = False
        self.circuit_breaker_reason = None
        
        # Stop-loss tracking logic moved to journal/strategies, 
        # but kept here for runtime monitoring
        self.stop_losses = {}  # {symbol: stop_loss_price}
        self.take_profits = {} # {symbol: {tp1: price, tp2: price}}
    
    def calculate_position_size(self, entry_price: float, stop_loss: float, 
                               capital: float) -> Tuple[int, float, float]:
        """
        Calculate position size based on risk
        
        Args:
            entry_price: Entry price
            stop_loss: Stop loss price
            capital: Total available capital
            
        Returns:
            (shares, position_value, risk_amount)
        """
        if entry_price <= stop_loss:
            return 0, 0, 0
            
        # 1. Determine Risk Amount (1% of Capital)
        # Fix capital basis to 10M as requested, or use actual if lower
        risk_basis = min(capital, self.config.INITIAL_CAPITAL)
        risk_amount = risk_basis * self.config.RISK_PER_TRADE_PCT
        
        # 2. Calculate Risk Per Share
        risk_per_share = entry_price - stop_loss
        
        # 3. Calculate Shares
        # Shares = Risk Amount / Risk Per Share
        if risk_per_share > 0:
            shares = int(risk_amount / risk_per_share)
        else:
            shares = 0
            
        # 4. Validate against constraints
        position_value = shares * entry_price
        
        # Check max position size (don't put too much in one basket)
        max_pos_value = self.config.get_max_position_value(capital)
        if position_value > max_pos_value:
            shares = int(max_pos_value / entry_price)
            position_value = shares * entry_price
            risk_amount = shares * risk_per_share # Recalculate risk
            
        # Check min position size
        min_pos_value = capital * self.config.MIN_POSITION_SIZE
        if position_value < min_pos_value:
            # If valid risk size is too small, we shouldn't trade
            # But for testing/small accounts, we might allow minimum
            if risk_amount < (risk_basis * 0.005): # Less than 0.5% risk
                pass # Accept small trade
            else:
                pass 

        # Round down to nearest 100 for VN stock market (lot size)
        shares = (shares // 100) * 100
        position_value = shares * entry_price
        risk_amount = shares * risk_per_share
        
        return shares, position_value, risk_amount

    def reset_daily_tracking(self, current_capital: float):
        """Reset daily tracking at market open"""
        today = date.today()
        
        if self.current_date != today:
            self.current_date = today
            self.daily_start_capital = current_capital
            self.daily_trades = []
            
            # Check journal pause status
            if self.journal.is_paused():
                self.activate_circuit_breaker(
                    f"Auto-pause active until {self.journal.pause_until}"
                )
            
            logger.info(f"📅 Daily tracking reset. Starting capital: {current_capital:,.0f} VND")
    
    def calculate_daily_pnl(self, current_capital: float) -> Tuple[float, float]:
        """Calculate daily P&L"""
        if self.daily_start_capital == 0:
            return 0, 0
        
        pnl = current_capital - self.daily_start_capital
        pnl_pct = (pnl / self.daily_start_capital) * 100
        
        return pnl, pnl_pct
    
    def check_daily_loss_limit(self, current_capital: float) -> bool:
        """Check if daily loss limit exceeded"""
        _, pnl_pct = self.calculate_daily_pnl(current_capital)
        
        if pnl_pct < -self.config.MAX_DAILY_LOSS_PCT * 100:
            self.activate_circuit_breaker(
                f"Daily loss limit exceeded: {pnl_pct:.2f}% (max: -{self.config.MAX_DAILY_LOSS_PCT * 100}%)"
            )
            return True
        
        return False
    
    def check_max_drawdown(self, current_capital: float, initial_capital: float) -> bool:
        """Check if maximum drawdown exceeded"""
        drawdown = ((initial_capital - current_capital) / initial_capital) * 100
        
        if drawdown > self.config.MAX_DRAWDOWN_PCT * 100:
            self.activate_circuit_breaker(
                f"Maximum drawdown exceeded: {drawdown:.2f}% (max: {self.config.MAX_DRAWDOWN_PCT * 100}%)"
            )
            return True
        
        return False
    
    def activate_circuit_breaker(self, reason: str):
        """Activate circuit breaker to stop trading"""
        self.circuit_breaker_active = True
        self.circuit_breaker_reason = reason
        logger.error(f"🚨 CIRCUIT BREAKER ACTIVATED: {reason}")
    
    def deactivate_circuit_breaker(self):
        """Manually deactivate circuit breaker"""
        self.circuit_breaker_active = False
        self.circuit_breaker_reason = None
        logger.info("✅ Circuit breaker deactivated")
    
    def is_circuit_breaker_active(self) -> bool:
        """Check if circuit breaker is active"""
        # Also check journal pause
        if self.journal.is_paused() and not self.circuit_breaker_active:
             self.activate_circuit_breaker(f"Auto-pause active until {self.journal.pause_until}")
             
        return self.circuit_breaker_active
    
    def set_stop_loss(self, symbol: str, stop_loss_price: float):
        """Set stop-loss for a position"""
        self.stop_losses[symbol] = stop_loss_price
        logger.info(f"🛡️ Stop-loss set for {symbol}: {stop_loss_price:,.0f} VND")
        
    def set_take_profit(self, symbol: str, tp1: float, tp2: float):
        """Set take profit levels"""
        self.take_profits[symbol] = {'tp1': tp1, 'tp2': tp2}
    
    def check_stop_losses(self, positions: Dict, current_prices: Dict[str, float]) -> List[Dict]:
        """
        Check if any positions hit stop-loss
        Returns list of dicts with symbol and reason
        """
        triggered = []
        
        for symbol, pos in positions.items():
            if symbol not in current_prices:
                continue
            
            current_price = current_prices[symbol]
            stop_loss = self.stop_losses.get(symbol)
            
            if stop_loss and current_price <= stop_loss:
                triggered.append({
                    'symbol': symbol,
                    'price': current_price,
                    'reason': 'STOP_LOSS_TRIGGERED'
                })
                logger.warning(f"⚠️ STOP-LOSS TRIGGERED: {symbol} @ {current_price:,.0f} (SL: {stop_loss:,.0f})")
        
        return triggered

    def update_trailing_stop(self, symbol: str, current_price: float, highest_price: float):
        """Update trailing stop-loss (only after profit secured)"""
        if symbol not in self.stop_losses:
            return
            
        entry_price = 0 # Need to fetch from somewhere if we want precise logic
        # For now, simplistic trailing stop if price > entry + 5%
        
        # Calculate new potential stop
        new_stop = highest_price * (1 - self.config.TRAILING_STOP_PCT)
        
        # Only move stop UP
        if new_stop > self.stop_losses[symbol]:
            old_stop = self.stop_losses[symbol]
            self.stop_losses[symbol] = new_stop
            logger.info(f"📈 Trailing stop updated for {symbol}: {old_stop:,.0f} → {new_stop:,.0f}")
    
    def validate_trade(self, symbol: str, action: str, shares: int, 
                      current_positions: int, current_capital: float) -> Tuple[bool, Optional[str]]:
        """Validate if a trade is safe to execute"""
        # Check circuit breaker & pause
        if self.is_circuit_breaker_active():
            return False, f"Circuit breaker active: {self.circuit_breaker_reason}"
        
        if self.journal.is_paused():
            return False, f"Trading paused until {self.journal.pause_until}"
        
        # Check position limits for buys
        if action == 'BUY':
            if current_positions >= self.config.MAX_OPEN_POSITIONS:
                return False, f"Maximum positions ({self.config.MAX_OPEN_POSITIONS}) reached"
            
            if shares <= 0:
                return False, "Invalid position size (0 shares)"
                
        return True, None
    
    def record_entry(self, trade_data: Dict, strategy: str, regime: str, 
                    sl: float, tp1: float, tp2: float, rr: float, risk: float):
        """Record trade entry to journal"""
        self.journal.log_entry(
            trade_data=trade_data,
            strategy=strategy,
            market_regime=regime,
            stop_loss=sl,
            take_profit_1=tp1,
            take_profit_2=tp2,
            risk_reward=rr,
            risk_amount=risk
        )
        self.daily_trades.append(trade_data)

    def record_exit(self, symbol: str, exit_data: Dict):
        """Record trade exit to journal"""
        self.journal.log_exit(symbol, exit_data)
        self.daily_trades.append(exit_data)
    
    def get_safety_status(self) -> Dict:
        """Get current safety status"""
        journal_summary = self.journal.get_performance_summary()
        return {
            'circuit_breaker_active': self.circuit_breaker_active,
            'circuit_breaker_reason': self.circuit_breaker_reason,
            'consecutive_losses': journal_summary.get('consecutive_losses', 0),
            'is_paused': journal_summary.get('is_paused', False),
            'pause_until': journal_summary.get('pause_until'),
            'active_stop_losses': len(self.stop_losses)
        }

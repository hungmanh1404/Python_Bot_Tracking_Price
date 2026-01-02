"""
Safety Manager
Implements safety mechanisms for automated trading
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime, date
from utils.logger import logger
from auto_config import AutoTradingConfig

class SafetyManager:
    """Manages trading safety and risk controls"""
    
    def __init__(self, config: AutoTradingConfig):
        """
        Initialize safety manager
        
        Args:
            config: Trading configuration
        """
        self.config = config
        
        # Daily tracking
        self.daily_start_capital = 0
        self.current_date = None
        self.daily_trades = []
        self.consecutive_losses = 0
        
        # Circuit breaker status
        self.circuit_breaker_active = False
        self.circuit_breaker_reason = None
        
        # Stop-loss tracking
        self.stop_losses = {}  # {symbol: stop_loss_price}
    
    def reset_daily_tracking(self, current_capital: float):
        """Reset daily tracking at market open"""
        today = date.today()
        
        if self.current_date != today:
            self.current_date = today
            self.daily_start_capital = current_capital
            self.daily_trades = []
            self.consecutive_losses = 0
            
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
    
    def check_consecutive_losses(self) -> bool:
        """Check consecutive losses"""
        if self.consecutive_losses >= self.config.MAX_CONSECUTIVE_LOSSES:
            self.activate_circuit_breaker(
                f"Too many consecutive losses: {self.consecutive_losses}"
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
        return self.circuit_breaker_active
    
    def set_stop_loss(self, symbol: str, entry_price: float):
        """Set stop-loss for a position"""
        stop_loss_price = entry_price * (1 - self.config.STOP_LOSS_PCT)
        self.stop_losses[symbol] = stop_loss_price
        
        logger.info(f"🛡️ Stop-loss set for {symbol}: {stop_loss_price:,.0f} VND (-{self.config.STOP_LOSS_PCT * 100}%)")
    
    def check_stop_losses(self, positions: Dict, current_prices: Dict[str, float]) -> List[str]:
        """
        Check if any positions hit stop-loss
        
        Returns:
            List of symbols that hit stop-loss
        """
        triggered = []
        
        for symbol, pos in positions.items():
            if symbol not in current_prices:
                continue
            
            current_price = current_prices[symbol]
            stop_loss = self.stop_losses.get(symbol)
            
            if stop_loss and current_price <= stop_loss:
                triggered.append(symbol)
                logger.warning(f"⚠️ STOP-LOSS TRIGGERED: {symbol} @ {current_price:,.0f} (SL: {stop_loss:,.0f})")
        
        return triggered
    
    def update_trailing_stop(self, symbol: str, current_price: float, highest_price: float):
        """Update trailing stop-loss"""
        if symbol not in self.stop_losses:
            return
        
        # Calculate new trailing stop
        new_stop = highest_price * (1 - self.config.TRAILING_STOP_PCT)
        
        # Only update if new stop is higher than current
        if new_stop > self.stop_losses[symbol]:
            old_stop = self.stop_losses[symbol]
            self.stop_losses[symbol] = new_stop
            logger.info(f"📈 Trailing stop updated for {symbol}: {old_stop:,.0f} → {new_stop:,.0f}")
    
    def validate_trade(self, symbol: str, action: str, amount: float, 
                      current_positions: int, current_capital: float) -> Tuple[bool, Optional[str]]:
        """
        Validate if a trade is safe to execute
        
        Returns:
            (is_valid, reason)
        """
        # Check circuit breaker
        if self.circuit_breaker_active:
            return False, f"Circuit breaker active: {self.circuit_breaker_reason}"
        
        # Check position limits for buys
        if action == 'BUY':
            if current_positions >= self.config.MAX_OPEN_POSITIONS:
                return False, f"Maximum positions ({self.config.MAX_OPEN_POSITIONS}) reached"
            
            max_position_value = self.config.get_max_position_value(current_capital)
            if amount > max_position_value:
                return False, f"Position size ({amount:,.0f}) exceeds maximum ({max_position_value:,.0f})"
        
        return True, None
    
    def record_trade(self, symbol: str, action: str, pnl: Optional[float] = None):
        """Record a trade for tracking"""
        trade = {
            'time': datetime.now(),
            'symbol': symbol,
            'action': action,
            'pnl': pnl
        }
        
        self.daily_trades.append(trade)
        
        # Update consecutive losses
        if action == 'SELL' and pnl is not None:
            if pnl < 0:
                self.consecutive_losses += 1
            else:
                self.consecutive_losses = 0  # Reset on profit
    
    def get_safety_status(self) -> Dict:
        """Get current safety status"""
        return {
            'circuit_breaker_active': self.circuit_breaker_active,
            'circuit_breaker_reason': self.circuit_breaker_reason,
            'consecutive_losses': self.consecutive_losses,
            'daily_trades_count': len(self.daily_trades),
            'active_stop_losses': len(self.stop_losses)
        }

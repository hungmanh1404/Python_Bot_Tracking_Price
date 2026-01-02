"""
Paper Trading Simulator
Simulates real trading with 10 million VND capital
Based on 3-Agent bot signals
"""
from typing import Dict, List, Tuple
from datetime import datetime
from utils.logger import logger

class PaperTradingSimulator:
    """Simulates trading with virtual capital"""
    
    def __init__(self, initial_capital: float = 10_000_000):
        """
        Initialize simulator
        
        Args:
            initial_capital: Starting capital in VND
        """
        self.initial_capital = initial_capital
        self.cash = initial_capital
        self.positions = {}  # {symbol: {'shares': int, 'avg_price': float}}
        self.trades = []  # History of all trades
        self.portfolio_value_history = []
    
    def get_portfolio_value(self, current_prices: Dict[str, float]) -> float:
        """Calculate total portfolio value"""
        stock_value = sum(
            pos['shares'] * current_prices.get(symbol, pos['avg_price'])
            for symbol, pos in self.positions.items()
        )
        return self.cash + stock_value
    
    def buy(self, symbol: str, price: float, amount: float, reason: str = "") -> bool:
        """
        Buy stock
        
        Args:
            symbol: Stock symbol
            price: Current price
            amount: Amount in VND to invest
            reason: Reason for buying
            
        Returns:
            True if successful
        """
        if amount > self.cash:
            logger.warning(f"Insufficient cash to buy {symbol}. Need {amount:,.0f}, have {self.cash:,.0f}")
            return False
        
        # Calculate shares (round down to avoid fractional shares)
        shares = int(amount / price)
        actual_cost = shares * price
        
        if shares <= 0:
            logger.warning(f"Amount too small to buy even 1 share of {symbol}")
            return False
        
        # Execute buy
        self.cash -= actual_cost
        
        if symbol in self.positions:
            # Update average price
            old_shares = self.positions[symbol]['shares']
            old_avg = self.positions[symbol]['avg_price']
            new_shares = old_shares + shares
            new_avg = ((old_shares * old_avg) + actual_cost) / new_shares
            
            self.positions[symbol] = {
                'shares': new_shares,
                'avg_price': new_avg
            }
        else:
            self.positions[symbol] = {
                'shares': shares,
                'avg_price': price
            }
        
        # Record trade
        trade = {
            'time': datetime.now(),
            'action': 'BUY',
            'symbol': symbol,
            'shares': shares,
            'price': price,
            'total': actual_cost,
            'reason': reason
        }
        self.trades.append(trade)
        
        logger.info(f"✅ BUY {shares} {symbol} @ {price:,.0f} = {actual_cost:,.0f} VND. Cash left: {self.cash:,.0f}")
        return True
    
    def sell(self, symbol: str, price: float, percentage: float = 100, reason: str = "") -> bool:
        """
        Sell stock
        
        Args:
            symbol: Stock symbol
            price: Current price
            percentage: Percentage of position to sell (0-100)
            reason: Reason for selling
            
        Returns:
            True if successful
        """
        if symbol not in self.positions or self.positions[symbol]['shares'] == 0:
            logger.warning(f"No position in {symbol} to sell")
            return False
        
        # Calculate shares to sell
        total_shares = self.positions[symbol]['shares']
        shares_to_sell = int(total_shares * (percentage / 100))
        
        if shares_to_sell <= 0:
            logger.warning(f"Percentage too small to sell any shares of {symbol}")
            return False
        
        # Execute sell
        proceeds = shares_to_sell * price
        self.cash += proceeds
        self.positions[symbol]['shares'] -= shares_to_sell
        
        # Calculate P&L
        avg_price = self.positions[symbol]['avg_price']
        pnl = (price - avg_price) * shares_to_sell
        pnl_percentage = ((price / avg_price) - 1) * 100
        
        # Record trade
        trade = {
            'time': datetime.now(),
            'action': 'SELL',
            'symbol': symbol,
            'shares': shares_to_sell,
            'price': price,
            'total': proceeds,
            'pnl': pnl,
            'pnl_percentage': pnl_percentage,
            'reason': reason
        }
        self.trades.append(trade)
        
        logger.info(f"✅ SELL {shares_to_sell} {symbol} @ {price:,.0f} = {proceeds:,.0f} VND. "
                   f"P&L: {pnl:+,.0f} ({pnl_percentage:+.2f}%). Cash: {self.cash:,.0f}")
        
        # Clean up empty  positions
        if self.positions[symbol]['shares'] == 0:
            del self.positions[symbol]
        
        return True
    
    def execute_strategy(self, analyses: List[Dict], current_prices: Dict[str, float]) -> None:
        """
        Execute trading based on bot signals
        
        Args:
            analyses: List of stock analyses from bot
            current_prices: Current prices for all stocks
        """
        logger.info("=" * 60)
        logger.info("EXECUTING TRADING STRATEGY")
        logger.info("=" * 60)
        
        for analysis in analyses:
            symbol = analysis['symbol']
            confidence = analysis['confidence']
            action = analysis['decision']
            price = current_prices.get(symbol, 0)
            
            if price == 0:
                logger.warning(f"No price data for {symbol}, skipping")
                continue
            
            # Determine position size based on confidence
            if '🟢' in action:  # MUA NGAY
                # Allocate based on confidence (higher confidence = larger position)
                allocation_pct = min(confidence / 100 * 0.30, 0.25)  # Max 25% of capital
                position_size = self.cash * allocation_pct
                
                if position_size >= price:  # Can afford at least 1 share
                    self.buy(symbol, price, position_size, 
                            reason=f"Strong buy signal, confidence {confidence}%")
            
            elif '🟡' in action:  # TÍCH LŨY
                # Smaller position for accumulation
                allocation_pct = min(confidence / 100 * 0.20, 0.15)  # Max 15%
                position_size = self.cash * allocation_pct
                
                if position_size >= price:
                    self.buy(symbol, price, position_size,
                            reason=f"Accumulation signal, confidence {confidence}%")
            
            elif '🔴' in action or confidence < 40:  # ĐỨNG NGOÀI or low confidence
                # Sell if we have a position
                if symbol in self.positions:
                    self.sell(symbol, price, 100, 
                            reason=f"Exit signal, confidence {confidence}%")
        
        # Record portfolio value
        total_value = self.get_portfolio_value(current_prices)
        self.portfolio_value_history.append({
            'time': datetime.now(),
            'value': total_value,
            'cash': self.cash,
            'positions': dict(self.positions)
        })
    
    def get_performance_report(self, current_prices: Dict[str, float]) -> Dict:
        """Generate performance report"""
        total_value = self.get_portfolio_value(current_prices)
        total_pnl = total_value - self.initial_capital
        total_return = (total_pnl / self.initial_capital) * 100
        
        # Calculate per-position P&L
        position_pnl = {}
        for symbol, pos in self.positions.items():
            current_price = current_prices.get(symbol, pos['avg_price'])
            pnl = (current_price - pos['avg_price']) * pos['shares']
            pnl_pct = ((current_price / pos['avg_price']) - 1) * 100
            position_pnl[symbol] = {
                'shares': pos['shares'],
                'avg_price': pos['avg_price'],
                'current_price': current_price,
                'value': pos['shares'] * current_price,
                'pnl': pnl,
                'pnl_percentage': pnl_pct
            }
        
        return {
            'initial_capital': self.initial_capital,
            'current_value': total_value,
            'cash': self.cash,
            'total_pnl': total_pnl,
            'total_return_pct': total_return,
            'num_trades': len(self.trades),
            'num_positions': len(self.positions),
            'positions': position_pnl,
            'trades': self.trades
        }

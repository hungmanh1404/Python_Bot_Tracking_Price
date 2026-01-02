"""
Real-Time Price Monitor
Continuously monitors stock prices and detects significant changes
"""
import time
from typing import Dict, Optional, List
from datetime import datetime, time as dt_time
from utils.logger import logger
from data_scraper import StockDataScraper

class PriceMonitor:
    """Monitors real-time stock prices"""
    
    def __init__(self, symbols: List[str], poll_interval: int = 300, data_mode: str = 'demo'):
        """
        Initialize price monitor
        
        Args:
            symbols: List of stock symbols to monitor
            poll_interval: Seconds between price checks
            data_mode: 'demo' for mock data, 'real' for actual market data
        """
        self.symbols = symbols
        self.poll_interval = poll_interval
        self.scraper = StockDataScraper(data_mode=data_mode)
        
        self.current_prices = {}  # {symbol: price}
        self.previous_prices = {}  # {symbol: price}
        self.price_changes = {}  # {symbol: change_pct}
        self.last_update = None
    
    def is_market_open(self) -> bool:
        """Check if market is currently open"""
        now = datetime.now()
        current_time = now.time()
        current_day = now.weekday()  # 0-6 (Monday-Sunday)
        
        # Check if it's a trading day (Monday-Friday)
        if current_day not in [0, 1, 2, 3, 4]:
            return False
        
        # Check market hours
        morning_start = dt_time(9, 0)
        morning_end = dt_time(11, 30)
        afternoon_start = dt_time(13, 0)
        afternoon_end = dt_time(14, 30)
        
        in_morning_session = morning_start <= current_time <= morning_end
        in_afternoon_session = afternoon_start <= current_time <= afternoon_end
        
        return in_morning_session or in_afternoon_session
    
    def time_until_market_open(self) -> int:
        """Calculate seconds until market opens"""
        now = datetime.now()
        current_time = now.time()
        current_day = now.weekday()
        
        # If weekend, wait until Monday 9am
        if current_day >= 5:  # Saturday or Sunday
            days_until_monday = 7 - current_day
            hours_until_open = (days_until_monday * 24) + (9 - now.hour)
            return hours_until_open * 3600
        
        # If before morning session
        if current_time < dt_time(9, 0):
            seconds = (dt_time(9, 0).hour - now.hour) * 3600
            seconds -= (now.minute * 60 + now.second)
            return seconds
        
        # If between sessions
        if dt_time(11, 30) < current_time < dt_time(13, 0):
            seconds = (13 - now.hour) * 3600
            seconds -= (now.minute * 60 + now.second)
            return seconds
        
        # If after market close, wait until next day
        if current_time > dt_time(14, 30):
            next_day_seconds = ((24 - now.hour) + 9) * 3600
            next_day_seconds -= (now.minute * 60 + now.second)
            return next_day_seconds
        
        return 0
    
    def fetch_current_prices(self) -> Dict[str, float]:
        """Fetch current prices for all symbols"""
        prices = {}
        
        for symbol in self.symbols:
            try:
                data = self.scraper.get_stock_data(symbol)
                if data and data.get('price'):
                    prices[symbol] = data['price']
                else:
                    # Use previous price if fetch fails
                    if symbol in self.current_prices:
                        prices[symbol] = self.current_prices[symbol]
                        logger.warning(f"Using cached price for {symbol}")
            except Exception as e:
                logger.error(f"Error fetching price for {symbol}: {e}")
                if symbol in self.current_prices:
                    prices[symbol] = self.current_prices[symbol]
        
        return prices
    
    def update_prices(self) -> bool:
        """Update prices and calculate changes"""
        try:
            new_prices = self.fetch_current_prices()
            
            if not new_prices:
                logger.error("Failed to fetch any prices")
                return False
            
            # Calculate changes
            for symbol, new_price in new_prices.items():
                old_price = self.current_prices.get(symbol, new_price)
                
                if old_price > 0:
                    change_pct = ((new_price - old_price) / old_price) * 100
                    self.price_changes[symbol] = change_pct
                else:
                    self.price_changes[symbol] = 0
            
            # Update prices
            self.previous_prices = self.current_prices.copy()
            self.current_prices = new_prices
            self.last_update = datetime.now()
            
            return True
            
        except Exception as e:
            logger.error(f"Error updating prices: {e}")
            return False
    
    def get_significant_changes(self, threshold_pct: float = 2.0) -> Dict[str, float]:
        """Get stocks with price changes > threshold"""
        significant = {}
        
        for symbol, change in self.price_changes.items():
            if abs(change) >= threshold_pct:
                significant[symbol] = change
        
        return significant
    
    def get_current_prices(self) -> Dict[str, float]:
        """Get current prices"""
        return self.current_prices.copy()
    
    def get_price_info(self, symbol: str) -> Optional[Dict]:
        """Get detailed price info for a symbol"""
        if symbol not in self.current_prices:
            return None
        
        return {
            'symbol': symbol,
            'current_price': self.current_prices[symbol],
            'previous_price': self.previous_prices.get(symbol),
            'change_pct': self.price_changes.get(symbol, 0),
            'last_update': self.last_update
        }
    
    def start_monitoring(self, callback=None):
        """
        Start continuous monitoring
        
        Args:
            callback: Function to call on each update
        """
        logger.info("=" * 70)
        logger.info("🔍 Starting Price Monitor")
        logger.info(f"Symbols: {', '.join(self.symbols)}")
        logger.info(f"Poll interval: {self.poll_interval}s")
        logger.info("=" * 70)
        
        while True:
            try:
                if not self.is_market_open():
                    wait_time = self.time_until_market_open()
                    logger.info(f"Market closed. Waiting {wait_time // 3600}h until open...")
                    time.sleep(min(wait_time, 3600))  # Check every hour max
                    continue
                
                # Update prices
                success = self.update_prices()
                
                if success:
                    logger.info(f"✅ Prices updated at {self.last_update.strftime('%H:%M:%S')}")
                    
                    # Log prices
                    for symbol, price in self.current_prices.items():
                        change = self.price_changes.get(symbol, 0)
                        change_sign = "+" if change >= 0 else ""
                        logger.info(f"  {symbol}: {price:,.0f} VND ({change_sign}{change:.2f}%)")
                    
                    # Check for significant changes
                    significant = self.get_significant_changes(2.0)
                    if significant:
                        logger.warning(f"⚡ Significant changes detected: {significant}")
                    
                    # Call callback if provided
                    if callback:
                        callback(self.current_prices, self.price_changes)
                
                # Wait for next poll
                time.sleep(self.poll_interval)
                
            except KeyboardInterrupt:
                logger.info("Price monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}", exc_info=True)
                time.sleep(60)  # Wait 1 minute before retry

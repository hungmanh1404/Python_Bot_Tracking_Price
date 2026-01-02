"""
Auto Trading Configuration
Centralized config for automated trading bot
"""
import os
from datetime import time
from dotenv import load_dotenv

load_dotenv()

class AutoTradingConfig:
    """Configuration for automated trading"""
    
    # Capital Management
    INITIAL_CAPITAL = 10_000_000  # VND
    PAPER_TRADING_MODE = True  # Set False for real trading
    
    # Data Source
    DATA_MODE = 'demo'  # 'demo' for mock data, 'real' for actual market data
    
    # Timing
    POLL_INTERVAL = 300  # 5 minutes (in seconds)
    
    # Market Hours (Vietnam Stock Exchange)
    MARKET_HOURS = {
        'morning_start': time(9, 0),
        'morning_end': time(11, 30),
        'afternoon_start': time(13, 0),
        'afternoon_end': time(14, 30),
        'trading_days': [0, 1, 2, 3, 4]  # Monday-Friday
    }
    
    # Position Sizing
    MAX_POSITION_SIZE = 0.25  # 25% per stock
    MIN_POSITION_SIZE = 0.05  # 5% minimum
    
    # Trading Thresholds
    MIN_CONFIDENCE_TO_BUY = 60
    MIN_CONFIDENCE_TO_ACCUMULATE = 50
    MIN_CONFIDENCE_TO_SELL = 40
    
    # Risk Management
    STOP_LOSS_PCT = 0.08  # -8% auto sell
    TAKE_PROFIT_PCT = 0.15  # +15% auto sell 50%
    TRAILING_STOP_PCT = 0.05  # 5% trailing stop
    
    MAX_DAILY_LOSS_PCT = 0.05  # -5% stop trading for the day
    MAX_DRAWDOWN_PCT = 0.15  # -15% stop completely
    MAX_CONSECUTIVE_LOSSES = 3  # Stop after 3 losses in a row
    
    # Position Limits
    MAX_OPEN_POSITIONS = 4  # Maximum number of stocks to hold
    
    # Reporting
    HOURLY_REPORT = True
    DAILY_REPORT = True
    TRADE_ALERTS = True
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Stock Symbols
    TRADING_SYMBOLS = ['FPT', 'PVS', 'KBC', 'HPG']
    
    @classmethod
    def is_paper_trading(cls):
        """Check if in paper trading mode"""
        return cls.PAPER_TRADING_MODE
    
    @classmethod
    def get_max_position_value(cls, capital: float) -> float:
        """Calculate max position value"""
        return capital * cls.MAX_POSITION_SIZE
    
    @classmethod
    def validate(cls):
        """Validate configuration"""
        if not cls.TELEGRAM_BOT_TOKEN or not cls.TELEGRAM_CHAT_ID:
            raise ValueError("Telegram credentials not configured")
        
        if cls.MAX_POSITION_SIZE > 0.5:
            raise ValueError("MAX_POSITION_SIZE too high (>50%)")
        
        if cls.STOP_LOSS_PCT > 0.2:
            raise ValueError("STOP_LOSS_PCT too high (>20%)")
        
        return True

# Validate on import
AutoTradingConfig.validate()

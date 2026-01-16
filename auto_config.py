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
    DATA_MODE = 'real'  # 'demo' for mock data, 'real' for actual market data
    
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
    MIN_CONFIDENCE_TO_BUY = 40        # Lowered to match analyzer logic
    MIN_CONFIDENCE_TO_ACCUMULATE = 30  
    MIN_CONFIDENCE_TO_SELL = 30
    
    # Risk Management (Trụ 3)
    RISK_PER_TRADE_PCT = 0.01  # 1% risk per trade
    INITIAL_CAPITAL = 10_000_000  # Fixed 10M VND
    
    # Stop Loss & Take Profit
    MIN_RR_RATIO = 2.0  # Take profit must be at least 2x risk
    STOP_LOSS_PCT = 0.05  # Max 5% hard stop
    TRAILING_STOP_PCT = 0.05
    TAKE_PROFIT_PARTIAL_1 = 0.30  # Sell 30% at R:1.5
    TAKE_PROFIT_PARTIAL_2 = 0.40  # Sell 40% at R:2.0
    
    # Safety Limits
    MAX_DAILY_LOSS_PCT = 0.05  # -5% stop trading for the day
    MAX_DRAWDOWN_PCT = 0.15  # -15% stop completely
    MAX_CONSECUTIVE_LOSSES = 3  # Stop after 3 losses in a row (Trigger 48h pause)
    
    # Position Limits
    MAX_OPEN_POSITIONS = 3  # Reduced to focus on quality
    
    # Reporting
    HOURLY_REPORT = False  # Disabled default hourly spam (using NotificationController)
    DAILY_REPORT = True
    TRADE_ALERTS = True
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Sector Analyst Configuration
    SECTOR_ANALYST_MODE = True
    DAILY_REPORT_TIME = '08:30'  # Vietnam time - report before market opens
    
    # FPT Monitoring Thresholds
    FPT_PE_THRESHOLD = 18.0  # Alert if P/E < 18x (undervalued)
    FPT_REVENUE_GROWTH_THRESHOLD = 15.0  # Alert if quarterly growth < 15%
    
    # PVS Monitoring (via Brent oil)
    PVS_BRENT_THRESHOLD = 85.0  # USD per barrel
    PVS_BRENT_DAYS_STABLE = 7  # Number of days to confirm trend
    
    # KBC Monitoring (news keywords)
    KBC_KEYWORDS = [
        'KBC ký biên bản ghi nhớ',
        'Foxconn',
        'LG Innotek',
        'Samsung',
        'hợp tác chiến lược'
    ]
    
    # HPG Monitoring (via Shanghai steel HRC)
    HPG_HRC_WEEKS_INCREASE = 2  # Number of consecutive weeks of price increase
    
    # Stock Symbols (only stocks with real-time data from BaoMoi)
    TRADING_SYMBOLS = ['FPT', 'KBC', 'HPG']  # Removed PVS - no real-time data available
    
    # Sector Analyst Symbols (includes PVS monitored via oil prices)
    SECTOR_ANALYST_SYMBOLS = ['FPT', 'PVS', 'KBC', 'HPG']
    
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

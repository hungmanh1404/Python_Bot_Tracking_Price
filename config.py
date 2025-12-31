"""
Configuration module for Stock Analyzer Bot
Loads environment variables and provides configuration settings
"""
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Application configuration"""
    
    # Telegram settings
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Stock symbols to track
    STOCK_SYMBOLS = os.getenv('STOCK_SYMBOLS', 'FPT,PVS,KBC,HPG').split(',')
    
    # Schedule time (HH:MM format)
    SCHEDULE_TIME = os.getenv('SCHEDULE_TIME', '08:00')
    
    # Thresholds for analysis
    CONFIDENCE_THRESHOLD_BUY = 75  # Buy if confidence >= 75
    CONFIDENCE_THRESHOLD_HOLD = 60  # Hold if 60 <= confidence < 75
    
    # Risk/Reward requirements
    MIN_RISK_REWARD_RATIO = 2.0
    
    @classmethod
    def validate(cls):
        """Validate that all required config is present"""
        if not cls.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN not set in .env file")
        if not cls.TELEGRAM_CHAT_ID:
            raise ValueError("TELEGRAM_CHAT_ID not set in .env file")
        return True

# Validate config on import
Config.validate()

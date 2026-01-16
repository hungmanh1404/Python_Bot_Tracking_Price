import sys
import os

# Add project root to path
sys.path.append('/Users/manh.nguyen/Desktop/AngentChungChi/stock_analyzer')

# MOCK DEPENDENCIES
from unittest.mock import MagicMock
sys.modules['dotenv'] = MagicMock()
sys.modules['requests'] = MagicMock()
# Mock load_dotenv specifically
sys.modules['dotenv'].load_dotenv = MagicMock()

# MOCK ENVIRONMENT VARIABLES
os.environ['TELEGRAM_BOT_TOKEN'] = 'mock_token'
os.environ['TELEGRAM_CHAT_ID'] = 'mock_chat_id'

print("1. Importing modules...")
try:
    from auto_config import AutoTradingConfig
    # ... rest of imports
    from notification_controller import NotificationController
    from market_regime_filter import MarketRegimeFilter
    from entry_strategies import EntryStrategies
    from trade_journal import TradeJournal
    from safety_manager import SafetyManager
    from analyzer import Agent3Analyzer
    from auto_trader import AutoTradeExecutor
    from run_auto_trading import AutoTradingBot
    print("✅ All modules imported successfully.")
except Exception as e:
    print(f"❌ Import failed: {e}")
    sys.exit(1)

print("\n2. Initializing components...")
try:
    config = AutoTradingConfig
    print("✅ Config loaded.")
    
    journal = TradeJournal()
    print("✅ TradeJournal initialized.")
    
    safety = SafetyManager(config)
    print("✅ SafetyManager initialized.")
    
    regime = MarketRegimeFilter()
    print("✅ MarketRegimeFilter initialized.")
    
    strategies = EntryStrategies()
    print("✅ EntryStrategies initialized.")
    
    analyzer = Agent3Analyzer()
    print("✅ Agent3Analyzer initialized.")
    
    # Needs mock for notifier/simulator
    class MockNotifier:
        def send_startup_message(self, c): pass
    
    print("✅ All components initialized successfully.")
    
    print("\n3. Testing Bot Initialization...")
    bot = AutoTradingBot()
    print("✅ AutoTradingBot instantiated.")

except Exception as e:
    print(f"❌ Initialization failed: {e}")
    sys.exit(1)

print("\n🎉 SYSTEM VERIFICATION PASSED")

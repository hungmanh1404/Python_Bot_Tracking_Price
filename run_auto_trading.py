"""
Run Automated Trading Bot
Main loop for continuous automated trading
Integrated with 4-Pillar System (Notification, Market Regime, Strategies, Journal)
"""
import time
from datetime import datetime
from typing import Dict

from auto_config import AutoTradingConfig
from price_monitor import PriceMonitor
from analyzer import Agent3Analyzer
from paper_trading import PaperTradingSimulator
from safety_manager import SafetyManager
from auto_trader import AutoTradeExecutor
from telegram_notifier import TelegramNotifier
from notification_controller import NotificationController, NotificationLevel
from trading_report import TradingReportGenerator
from utils.logger import logger

# Health check server for Render.com (prevents free tier sleep)
try:
    from health_server import start_health_server
    HEALTH_SERVER_ENABLED = True
except ImportError:
    HEALTH_SERVER_ENABLED = False

class AutoTradingBot:
    """Main automated trading bot"""
    
    def __init__(self):
        """Initialize bot components"""
        self.config = AutoTradingConfig
        self.running = False
        
        # Initialize components
        self.monitor = PriceMonitor(
            symbols=self.config.TRADING_SYMBOLS,
            poll_interval=self.config.POLL_INTERVAL,
            data_mode=self.config.DATA_MODE
        )
        
        # Core Systems
        self.base_notifier = TelegramNotifier()
        self.notifier = NotificationController(self.base_notifier)
        
        self.analyzer = Agent3Analyzer() # Includes Market Regime Filter
        self.simulator = PaperTradingSimulator(initial_capital=self.config.INITIAL_CAPITAL)
        self.safety = SafetyManager(self.config) # Includes Trade Journal
        
        self.executor = AutoTradeExecutor(
            self.simulator, self.safety, self.config, self.notifier
        )
        
        self.reporter = TradingReportGenerator()
        
        # Tracking
        self.iteration_count = 0
    
    def start(self):
        """Start the bot"""
        logger.info("=" * 70)
        logger.info("🚀 AUTOMATED TRADING BOT (4-PILLAR SYSTEM)")
        logger.info(f"Mode: {'PAPER TRADING' if self.config.PAPER_TRADING_MODE else 'LIVE TRADING'}")
        logger.info(f"Capital: {self.config.INITIAL_CAPITAL:,.0f} VND")
        logger.info("=" * 70)
        
        self.running = True
        self.notifier.send_startup_message(self.config)
        
        try:
            while self.running:
                self.iteration_count += 1
                logger.info(f"\nCompleted Iteration #{self.iteration_count}")
                
                # Main Loop logic
                self.run_iteration()
                
                logger.info(f"💤 Sleeping for {self.config.POLL_INTERVAL}s...")
                time.sleep(self.config.POLL_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("\n⚠️ Bot stopped by user")
            self.stop()
        except Exception as e:
            logger.error(f"❌ Fatal error in trading loop: {e}", exc_info=True)
            self.notifier.notify(f"🚨 *BOT CRASHED*\n\n{str(e)}", NotificationLevel.CRITICAL, "system")
            self.stop()

    def run_iteration(self):
        """Single trading iteration"""
        # 1. Check if market is open
        if not self.monitor.is_market_open():
            wait_time = self.monitor.time_until_market_open()
            if wait_time > 1800: # Only log if long wait
                logger.info(f"Market closed. Waiting {wait_time // 3600}h {(wait_time % 3600) // 60}m...")
            return
        
        # 2. Reset daily tracking
        current_capital = self.simulator.get_portfolio_value(self.monitor.current_prices or {})
        self.safety.reset_daily_tracking(current_capital)
        
        # 3. Check safety limits & Journal Pause
        if self.safety.is_circuit_breaker_active():
            # Already active, just wait
            return
            
        if self.safety.check_daily_loss_limit(current_capital):
            return
            
        if self.safety.check_max_drawdown(current_capital, self.config.INITIAL_CAPITAL):
            return
            
        # 4. Update prices
        success = self.monitor.update_prices()
        if not success:
            logger.warning("Failed to update prices, skipping")
            return
            
        current_prices = self.monitor.get_current_prices()
        market_data_map = {
            s: self.monitor.get_price_info(s) or {} for s in self.config.TRADING_SYMBOLS
        }
        
        # 5. Check stop-losses (Critical)
        triggered_stops = self.executor.check_and_execute_stop_losses(current_prices)
        if triggered_stops:
            logger.info(f"Stop losses executed for: {triggered_stops}")
            
        # 6. Update trailing stops
        self.executor.update_trailing_stops(current_prices)
        
        # 7. Analyze and Trade
        for symbol in self.config.TRADING_SYMBOLS:
            if symbol not in current_prices: continue
            
            # Prepare data
            data = {
                'price': current_prices[symbol],
                'change': self.monitor.price_changes.get(symbol, 0),
                'volume': 0 # TODO: Get real volume if available
            }
            
            # 3-Agent Analysis (includes Regime Filter)
            analysis = self.analyzer.analyze(symbol, data)
            
            # Execute (includes Entry Strategy check)
            self.executor.execute_signal(analysis, current_prices[symbol], data)
            
        # 8. Periodic Reporting (Hourly/Daily Digests)
        performance = self.simulator.get_performance_report(current_prices)
        
        # Hourly Digest
        self.notifier.send_hourly_digest(performance)
        
        # Daily Digest (at end of day 14:30)
        now = datetime.now()
        if now.hour == 14 and now.minute >= 30:
             journal_summary = self.safety.journal.export_report()
             self.notifier.send_daily_digest(performance, journal_summary)

    def stop(self):
        """Stop the bot gracefully"""
        self.running = False
        
        # Send final report
        if self.monitor.current_prices:
            performance = self.simulator.get_performance_report(self.monitor.current_prices)
            journal_summary = self.safety.journal.export_report()
            self.notifier.send_daily_digest(performance, journal_summary)
        
        self.notifier.notify("🛑 *BOT STOPPED*", NotificationLevel.CRITICAL, "system")
        logger.info("✅ Bot stopped gracefully")

def main():
    """Main entry point"""
    try:
        # Start health check server for Render.com
        if HEALTH_SERVER_ENABLED:
            start_health_server()
            logger.info("Health check server enabled for Render.com")
        
        bot = AutoTradingBot()
        bot.start()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)

if __name__ == "__main__":
    main()

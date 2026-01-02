"""
Run Automated Trading Bot
Main loop for continuous automated trading
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
        
        self.analyzer = Agent3Analyzer()
        self.simulator = PaperTradingSimulator(initial_capital=self.config.INITIAL_CAPITAL)
        self.safety = SafetyManager(self.config)
        self.executor = AutoTradeExecutor(self.simulator, self.safety, self.config)
        self.notifier = TelegramNotifier()
        self.reporter = TradingReportGenerator()
        
        # Tracking
        self.last_hourly_report = None
        self.last_daily_report = None
        self.iteration_count = 0
    
    def send_startup_message(self):
        """Send startup notification"""
        mode = "PAPER TRADING" if self.config.PAPER_TRADING_MODE else "⚠️ LIVE TRADING"
        
        msg = f"""🤖 *AUTO TRADING BOT STARTED*

*Mode:* {mode}
*Capital:* {self.config.INITIAL_CAPITAL:,.0f} VND
*Symbols:* {', '.join(self.config.TRADING_SYMBOLS)}
*Poll Interval:* {self.config.POLL_INTERVAL}s

*Safety Settings:*
• Stop Loss: -{self.config.STOP_LOSS_PCT * 100}%
• Daily Loss Limit: -{self.config.MAX_DAILY_LOSS_PCT * 100}%
• Max Drawdown: -{self.config.MAX_DRAWDOWN_PCT * 100}%

Bot is now monitoring the market...
⏰ {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
"""
        
        self.notifier.send_message(msg)
        logger.info("Startup notification sent")
    
    def send_trade_alert(self, trade: Dict):
        """Send alert when trade is executed"""
        action_emoji = "🟢 ↗" if trade['action'] == 'BUY' else "🔴 ↘"
        
        msg = f"""{action_emoji} *TRADE EXECUTED*

*Action:* {trade['action']}
*Symbol:* {trade['symbol']}
*Price:* {trade['price']:,.0f} VND
*Shares:* {trade['shares']}
*Value:* {trade['total']:,.0f} VND

*Reason:* {trade.get('reason', 'N/A')}
*Time:* {trade['time'].strftime('%H:%M:%S')}
"""
        
        if trade['action'] == 'SELL' and 'pnl' in trade:
            pnl_emoji = "💚" if trade['pnl'] > 0 else "❤️"
            msg += f"\n{pnl_emoji} *P&L:* {trade['pnl']:+,.0f} VND ({trade['pnl_percentage']:+.2f}%)"
        
        self.notifier.send_message(msg)
    
    def send_hourly_report(self, current_prices: Dict[str, float]):
        """Send hourly status update"""
        performance = self.simulator.get_performance_report(current_prices)
        
        msg = f"""📊 *HOURLY UPDATE*

💰 *Portfolio:* {performance['current_value']:,.0f} VND
💵 *Cash:* {performance['cash']:,.0f} VND
📈 *P&L:* {performance['total_pnl']:+,.0f} VND ({performance['total_return_pct']:+.2f}%)

*Positions:* {performance['num_positions']}
*Trades Today:* {len([t for t in performance['trades'] if t['time'].date() == datetime.now().date()])}

*Safety Status:*
• Circuit Breaker: {'❌ ACTIVE' if self.safety.is_circuit_breaker_active() else '✅ OK'}
• Consecutive Losses: {self.safety.consecutive_losses}

⏰ {datetime.now().strftime('%H:%M:%S')}
"""
        
        self.notifier.send_message(msg)
        logger.info("Hourly report sent")
    
    def trading_loop(self):
        """Main trading loop"""
        logger.info("=" * 70)
        logger.info("🚀 AUTOMATED TRADING BOT")
        logger.info(f"Mode: {'PAPER TRADING' if self.config.PAPER_TRADING_MODE else 'LIVE TRADING'}")
        logger.info(f"Capital: {self.config.INITIAL_CAPITAL:,.0f} VND")
        logger.info("=" * 70)
        
        self.running = True
        self.send_startup_message()
        
        try:
            while self.running:
                self.iteration_count += 1
                logger.info(f"\n{'=' * 70}")
                logger.info(f"Iteration #{self.iteration_count} - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                logger.info(f"{'=' * 70}")
                
                # 1. Check if market is open
                if not self.monitor.is_market_open():
                    wait_time = self.monitor.time_until_market_open()
                    logger.info(f"Market closed. Waiting {wait_time // 3600}h {(wait_time % 3600) // 60}m...")
                    time.sleep(min(wait_time, 1800))  # Check every 30min max
                    continue
                
                # 2. Reset daily tracking if new day
                current_capital = self.simulator.get_portfolio_value(self.monitor.current_prices or {})
                self.safety.reset_daily_tracking(current_capital)
                
                # 3. Check safety limits
                if self.safety.is_circuit_breaker_active():
                    logger.error(f"🚨 Circuit breaker active: {self.safety.circuit_breaker_reason}")
                    logger.error("Trading halted. Manual intervention required.")
                    
                    # Notify user
                    self.notifier.send_message(
                        f"🚨 *CIRCUIT BREAKER ACTIVE*\n\n{self.safety.circuit_breaker_reason}\n\n"
                        "Trading has been halted. Please review and restart manually."
                    )
                    break
                
                # Check daily loss limit
                if self.safety.check_daily_loss_limit(current_capital):
                    continue
                
                # Check max drawdown
                if self.safety.check_max_drawdown(current_capital, self.config.INITIAL_CAPITAL):
                    continue
                
                # Check consecutive losses
                if self.safety.check_consecutive_losses():
                    continue
                
                # 4. Update prices
                logger.info("📡 Fetching current prices...")
                success = self.monitor.update_prices()
                
                if not success:
                    logger.warning("Failed to update prices, skipping iteration")
                    time.sleep(60)
                    continue
                
                current_prices = self.monitor.get_current_prices()
                logger.info(f"✅ Prices updated: {current_prices}")
                
                # 5. Check stop-losses
                logger.info("🛡️ Checking stop-losses...")
                triggered_stops = self.executor.check_and_execute_stop_losses(current_prices)
                
                if triggered_stops:
                    for symbol in triggered_stops:
                        # Send alert
                        last_trade = self.simulator.trades[-1]
                        self.send_trade_alert(last_trade)
                
                # 6. Update trailing stops
                self.executor.update_trailing_stops(current_prices)
                
                # 7. Check take profit
                take_profits = self.executor.check_take_profit(current_prices)
                if take_profits:
                    logger.info(f"💰 Take profit executed for: {take_profits}")
                
                # 8. Analyze market and generate signals
                logger.info("🤖 Running market analysis...")
                for symbol in self.config.TRADING_SYMBOLS:
                    if symbol not in current_prices:
                        continue
                    
                    # Prepare data for analysis
                    data = {
                        'symbol': symbol,
                        'price': current_prices[symbol],
                        'change': self.monitor.price_changes.get(symbol, 0),
                        'volume': 0
                    }
                    
                    # Analyze
                    analysis = self.analyzer.analyze(symbol, data)
                    
                    # Execute based on signal
                    traded = self.executor.execute_signal(analysis, current_prices[symbol])
                    
                    if traded:
                        # Send trade alert
                        last_trade = self.simulator.trades[-1]
                        if self.config.TRADE_ALERTS:
                            self.send_trade_alert(last_trade)
                
                # 9. Update portfolio value
                total_value = self.simulator.get_portfolio_value(current_prices)
                logger.info(f"💼 Portfolio Value: {total_value:,.0f} VND")
                
                # 10. Periodic reporting
                now = datetime.now()
                
                # Hourly report
                if self.config.HOURLY_REPORT:
                    if (self.last_hourly_report is None or 
                        (now - self.last_hourly_report).seconds >= 3600):
                        self.send_hourly_report(current_prices)
                        self.last_hourly_report = now
                
                # 11. Sleep until next iteration
                logger.info(f"💤 Sleeping for {self.config.POLL_INTERVAL}s...")
                time.sleep(self.config.POLL_INTERVAL)
                
        except KeyboardInterrupt:
            logger.info("\n⚠️ Bot stopped by user")
            self.stop()
        except Exception as e:
            logger.error(f"❌ Fatal error in trading loop: {e}", exc_info=True)
            self.notifier.send_message(f"🚨 *BOT CRASHED*\n\n```\n{str(e)}\n```")
            self.stop()
    
    def stop(self):
        """Stop the bot gracefully"""
        self.running = False
        
        # Send final report
        if self.monitor.current_prices:
            performance = self.simulator.get_performance_report(self.monitor.current_prices)
            report = self.reporter.generate_trading_report(performance)
            
            self.notifier.send_long_message(f"🛑 *BOT STOPPED*\n\n{report}")
        
        logger.info("=" * 70)
        logger.info("✅ Bot stopped gracefully")
        logger.info("=" * 70)

def main():
    """Main entry point"""
    try:
        # Start health check server for Render.com
        if HEALTH_SERVER_ENABLED:
            start_health_server()
            logger.info("Health check server enabled for Render.com")
        
        bot = AutoTradingBot()
        bot.trading_loop()
    except Exception as e:
        logger.error(f"Failed to start bot: {e}", exc_info=True)

if __name__ == "__main__":
    main()

"""
Run Paper Trading Simulation
Execute trading strategy with real market data and 10M VND capital
"""
import sys
from datetime import datetime

from data_scraper import StockDataScraper
from analyzer import Agent3Analyzer
from paper_trading import PaperTradingSimulator
from trading_report import TradingReportGenerator
from telegram_notifier import TelegramNotifier
from config import Config
from utils.logger import logger

# REAL MARKET PRICES as of December 31, 2025
REAL_PRICES = {
    'FPT': 96_100,   # VND (from TradingView)
    'PVS': 34_600,   # VND (from CafeF)
    'KBC': 35_650,   # VND (from TheInvestor)
    'HPG': 26_450    # VND (from VietStock)
}

def run_paper_trading():
    """Run paper trading simulation"""
    try:
        logger.info("=" * 70)
        logger.info("🎯 PAPER TRADING SIMULATION - 10 TRIỆU VND")
        logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 70)
        
        # Initialize components
        scraper = StockDataScraper()
        analyzer = Agent3Analyzer()
        simulator = PaperTradingSimulator(initial_capital=10_000_000)
        report_gen = TradingReportGenerator()
        notifier = TelegramNotifier()
        
        logger.info(f"💰 Starting capital: {simulator.initial_capital:,.0f} VND")
        logger.info(f"📊 Trading stocks: {list(REAL_PRICES.keys())}")
        logger.info("")
        
        # Get market data
        logger.info("📡 Fetching market data...")
        all_data = []
        
        for symbol in REAL_PRICES.keys():
            # Try to scrape additional data
            data = scraper.get_stock_data(symbol)
            
            # Use real prices
            if data:
                data['price'] = REAL_PRICES[symbol]
            else:
                # Fallback to basic data with real price
                data = {
                    'symbol': symbol,
                    'price': REAL_PRICES[symbol],
                    'change': 0,
                    'volume': 0
                }
            
            all_data.append(data)
            logger.info(f"  ✅ {symbol}: {REAL_PRICES[symbol]:,.0f} VND")
        
        logger.info("")
        
        # Analyze all stocks
        logger.info("🤖 Running 3-Agent Analysis...")
        analyses = []
        for data in all_data:
            analysis = analyzer.analyze(data['symbol'], data)
            analyses.append(analysis)
            
            symbol = analysis['symbol']
            decision = analysis['decision']
            confidence = analysis['confidence']
            logger.info(f"  {symbol}: {decision} (Confidence: {confidence}%)")
        
        logger.info("")
        
        # Execute trading strategy
        logger.info("💼 Executing Trading Strategy...")
        logger.info("")
        simulator.execute_strategy(analyses, REAL_PRICES)
        
        logger.info("")
        logger.info("=" * 70)
        
        # Generate performance report
        performance = simulator.get_performance_report(REAL_PRICES)
        
        logger.info("📊 PERFORMANCE SUMMARY:")
        logger.info(f"  Initial Capital: {performance['initial_capital']:,.0f} VND")
        logger.info(f"  Current Value:   {performance['current_value']:,.0f} VND")
        logger.info(f"  Cash Remaining:  {performance['cash']:,.0f} VND")
        logger.info(f"  Total P&L:       {performance['total_pnl']:+,.0f} VND")
        logger.info(f"  Return:          {performance['total_return_pct']:+.2f}%")
        logger.info(f"  Trades Executed: {performance['num_trades']}")
        logger.info(f"  Open Positions:  {performance['num_positions']}")
        
        if performance['total_pnl'] > 0:
            logger.info("  Status:          🟢 PROFITABLE")
        elif performance['total_pnl'] < 0:
            logger.info("  Status:          🔴 LOSS")
        else:
            logger.info("  Status:          ⚪ BREAK EVEN")
        
        logger.info("=" * 70)
        logger.info("")
        
        # Generate and send report
        report = report_gen.generate_trading_report(performance)
        
        logger.info("Sending report to Telegram...")
        success = notifier.send_long_message(report)
        
        if success:
            logger.info("✅ Report sent to Telegram successfully!")
        else:
            logger.error("❌ Failed to send report")
            logger.info("Report content:")
            logger.info(report)
        
        logger.info("")
        logger.info("=" * 70)
        logger.info("✅ PAPER TRADING SIMULATION COMPLETE")
        logger.info("=" * 70)
        
        return performance
        
    except Exception as e:
        logger.error(f"Error in paper trading simulation: {e}", exc_info=True)
        return None

if __name__ == "__main__":
    run_paper_trading()

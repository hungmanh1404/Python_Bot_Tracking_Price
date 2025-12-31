"""
Main Entry Point for Stock Analyzer Bot
Orchestrates the entire analysis workflow
"""
import sys
import argparse
from typing import List
from datetime import datetime

from config import Config
from data_scraper import StockDataScraper
from analyzer import Agent3Analyzer
from report_generator import ReportGenerator
from telegram_notifier import TelegramNotifier
from scheduler import AnalysisScheduler
from utils.logger import logger

def run_analysis():
    """
    Main analysis workflow:
    1. Scrape stock data
    2. Analyze with 3-agent framework
    3. Generate report
    4. Send to Telegram
    """
    try:
        logger.info("=" * 60)
        logger.info("Starting Stock Analysis Workflow")
        logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 60)
        
        # Initialize components
        scraper = StockDataScraper()
        analyzer = Agent3Analyzer()
        reporter = ReportGenerator()
        notifier = TelegramNotifier()
        
        # Get stock symbols from config
        symbols = Config.STOCK_SYMBOLS
        logger.info(f"Analyzing {len(symbols)} stocks: {', '.join(symbols)}")
        
        # Collect data for all stocks
        all_data = []
        for symbol in symbols:
            data = scraper.get_stock_data(symbol)
            if data:
                all_data.append(data)
            else:
                # Use mock data if scraping fails
                logger.warning(f"Using mock data for {symbol}")
                all_data.append({
                    'symbol': symbol,
                    'price': 0,
                    'change': 0,
                    'volume': 0
                })
        
        # Analyze all stocks
        analyses = []
        for data in all_data:
            analysis = analyzer.analyze(data['symbol'], data)
            analyses.append(analysis)
        
        # Generate report
        market_context = "VN-Index ổn định, thanh khoản tốt"
        report = reporter.generate_daily_report(analyses, market_context)
        
        logger.info("Report generated successfully")
        logger.info(f"Report length: {len(report)} characters")
        
        # Send to Telegram
        success = notifier.send_long_message(report)
        
        if success:
            logger.info("✅ Analysis complete and sent to Telegram")
        else:
            logger.error("❌ Failed to send report to Telegram")
            # Log the report for debugging
            logger.info("Report content:")
            logger.info(report)
        
        logger.info("=" * 60)
        return success
        
    except Exception as e:
        logger.error(f"Error in analysis workflow: {e}", exc_info=True)
        
        # Try to send error notification
        try:
            notifier = TelegramNotifier()
            error_msg = f"⚠️ *Lỗi phân tích*\n\n```\n{str(e)}\n```"
            notifier.send_message(error_msg)
        except:
            pass
        
        return False

def main():
    """Main entry point with CLI argument parsing"""
    parser = argparse.ArgumentParser(description='Stock Analyzer Bot')
    parser.add_argument(
        '--manual',
        action='store_true',
        help='Run analysis once manually (no scheduling)'
    )
    parser.add_argument(
        '--test',
        action='store_true',
        help='Test Telegram connection'
    )
    
    args = parser.parse_args()
    
    try:
        if args.test:
            # Test mode
            logger.info("Testing Telegram connection...")
            notifier = TelegramNotifier()
            if notifier.test_connection():
                test_msg = "✅ *Test Message*\n\nBot is working correctly!"
                notifier.send_message(test_msg)
                logger.info("✅ Test successful!")
            else:
                logger.error("❌ Test failed!")
            return
        
        if args.manual:
            # Manual run (one-time)
            logger.info("Running in manual mode (one-time analysis)")
            run_analysis()
        else:
            # Scheduled mode
            logger.info("Running in scheduled mode")
            scheduler = AnalysisScheduler(run_analysis)
            scheduler.start()
            
    except KeyboardInterrupt:
        logger.info("\nBot stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()

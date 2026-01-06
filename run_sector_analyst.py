"""
Sector Analyst Runner
Main entry point for running the sector analyst system
"""
import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from sector_analyst import SectorAnalyst
from auto_config import AutoTradingConfig
from telegram_notifier import TelegramNotifier
from scheduler import AnalysisScheduler
from utils.logger import logger


def run_sector_analysis():
    """Run sector analysis and send report"""
    try:
        logger.info("=" * 50)
        logger.info("Starting Sector Analysis")
        logger.info("=" * 50)
        
        # Initialize components
        analyst = SectorAnalyst(AutoTradingConfig)
        notifier = TelegramNotifier()
        
        # Generate report
        report = analyst.generate_daily_report(dry_run=False)
        
        # Send to Telegram
        logger.info("Sending report to Telegram...")
        success = notifier.send_sector_report(report)
        
        if success:
            logger.info("✓ Sector analysis completed and sent successfully")
        else:
            logger.error("✗ Failed to send sector analysis report")
        
        logger.info("=" * 50)
        
        return success
        
    except Exception as e:
        logger.error(f"Error in sector analysis: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main entry point"""
    
    # Check if running as one-time or scheduled
    if len(sys.argv) > 1 and sys.argv[1] == '--once':
        # Run once and exit
        logger.info("Running sector analysis once...")
        run_sector_analysis()
    elif len(sys.argv) > 1 and sys.argv[1] == '--test':
        # Test mode - dry run only
        logger.info("Running in TEST mode (dry run)...")
        analyst = SectorAnalyst(AutoTradingConfig)
        analyst.generate_daily_report(dry_run=True)
    else:
        # Run on schedule
        logger.info(f"Starting scheduled sector analyst (daily at {AutoTradingConfig.DAILY_REPORT_TIME})")
        
        try:
            # Create scheduler
            scheduler = AnalysisScheduler(
                run_sector_analysis,
                schedule_time=AutoTradingConfig.DAILY_REPORT_TIME
            )
            
            # Start scheduler (will run once immediately then on schedule)
            scheduler.start()
            
        except KeyboardInterrupt:
            logger.info("Scheduler stopped by user")
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()

"""
Scheduler Module
Handles automatic scheduling of stock analysis
"""
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.cron import CronTrigger
from datetime import datetime
from utils.logger import logger
from config import Config
import sys

class AnalysisScheduler:
    """Manages scheduled execution of stock analysis"""
    
    def __init__(self, analysis_function):
        """
        Initialize scheduler
        
        Args:
            analysis_function: Function to call on schedule
        """
        self.scheduler = BlockingScheduler()
        self.analysis_function = analysis_function
        self.schedule_time = Config.SCHEDULE_TIME
    
    def start(self):
        """Start the scheduler"""
        try:
            # Parse schedule time (HH:MM format)
            hour, minute = map(int, self.schedule_time.split(':'))
            
            # Add job to scheduler
            self.scheduler.add_job(
                self.analysis_function,
                trigger=CronTrigger(hour=hour, minute=minute),
                id='daily_stock_analysis',
                name='Daily Stock Analysis',
                replace_existing=True
            )
            
            logger.info(f"Scheduler started. Will run daily at {self.schedule_time}")
            logger.info("Press Ctrl+C to exit")
            
            # Run once immediately on startup
            logger.info("Running initial analysis...")
            self.analysis_function()
            
            # Start scheduler
            self.scheduler.start()
            
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped by user")
            self.stop()
        except Exception as e:
            logger.error(f"Scheduler error: {e}")
            self.stop()
    
    def stop(self):
        """Stop the scheduler gracefully"""
        if self.scheduler.running:
            self.scheduler.shutdown()
            logger.info("Scheduler shut down successfully")
    
    def run_once(self):
        """Run analysis once without scheduling"""
        logger.info("Running one-time analysis...")
        self.analysis_function()
        logger.info("One-time analysis complete")

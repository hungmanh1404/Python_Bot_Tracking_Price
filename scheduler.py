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
    
    def __init__(self, analysis_function, schedule_time=None):
        """
        Initialize scheduler
        
        Args:
            analysis_function: Function to call on schedule
            schedule_time: Time to run (HH:MM format), defaults to Config.SCHEDULE_TIME
        """
        self.scheduler = BlockingScheduler()
        self.analysis_function = analysis_function
        self.schedule_time = schedule_time or Config.SCHEDULE_TIME
        self.jobs = []  # Track multiple jobs
    
    def start(self):
        """Start the scheduler"""
        try:
            # Parse schedule time (HH:MM format)
            hour, minute = map(int, self.schedule_time.split(':'))
            
            # Add job to scheduler
            job = self.scheduler.add_job(
                self.analysis_function,
                trigger=CronTrigger(hour=hour, minute=minute),
                id='daily_stock_analysis',
                name='Daily Stock Analysis',
                replace_existing=True
            )
            self.jobs.append(job)
            
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
    
    def add_job(self, function, schedule_time, job_id, job_name):
        """
        Add additional scheduled job
        
        Args:
            function: Function to call
            schedule_time: Time to run (HH:MM format)
            job_id: Unique job identifier
            job_name: Human-readable job name
        """
        try:
            hour, minute = map(int, schedule_time.split(':'))
            
            job = self.scheduler.add_job(
                function,
                trigger=CronTrigger(hour=hour, minute=minute),
                id=job_id,
                name=job_name,
                replace_existing=True
            )
            self.jobs.append(job)
            logger.info(f"Added job '{job_name}' scheduled for {schedule_time}")
            
        except Exception as e:
            logger.error(f"Failed to add job '{job_name}': {e}")
    
    def run_once(self):
        """Run analysis once without scheduling"""
        logger.info("Running one-time analysis...")
        self.analysis_function()
        logger.info("One-time analysis complete")

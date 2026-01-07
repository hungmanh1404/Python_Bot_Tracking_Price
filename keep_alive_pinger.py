#!/usr/bin/env python3
"""
Keep-Alive Pinger for Render.com
Pings the health endpoint every 5 minutes to prevent server from sleeping
"""
import requests
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
HEALTH_URL = "https://python-bot-tracking-price.onrender.com/health"
PING_INTERVAL = 300  # 5 minutes in seconds
MAX_RETRIES = 3
TIMEOUT = 10  # seconds

def ping_health_endpoint():
    """Ping the health endpoint once"""
    try:
        logger.info(f"Pinging {HEALTH_URL}...")
        response = requests.get(HEALTH_URL, timeout=TIMEOUT)
        
        if response.status_code == 200:
            logger.info(f"✅ Health check successful: {response.text[:100]}")
            return True
        else:
            logger.warning(f"⚠️ Health check returned status {response.status_code}")
            return False
            
    except requests.exceptions.Timeout:
        logger.error(f"❌ Timeout after {TIMEOUT}s")
        return False
    except requests.exceptions.ConnectionError:
        logger.error("❌ Connection error - server might be starting up")
        return False
    except Exception as e:
        logger.error(f"❌ Error pinging health endpoint: {e}")
        return False

def run_continuous_pinger():
    """Run continuous health checks"""
    logger.info("=" * 70)
    logger.info("🏓 Keep-Alive Pinger Started")
    logger.info(f"Target: {HEALTH_URL}")
    logger.info(f"Interval: {PING_INTERVAL}s ({PING_INTERVAL // 60} minutes)")
    logger.info("=" * 70)
    
    ping_count = 0
    success_count = 0
    
    try:
        while True:
            ping_count += 1
            logger.info(f"\n--- Ping #{ping_count} at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ---")
            
            # Try with retries
            success = False
            for attempt in range(1, MAX_RETRIES + 1):
                if attempt > 1:
                    logger.info(f"Retry attempt {attempt}/{MAX_RETRIES}...")
                    time.sleep(5)  # Wait 5s between retries
                
                success = ping_health_endpoint()
                if success:
                    success_count += 1
                    break
            
            if not success:
                logger.error(f"Failed after {MAX_RETRIES} attempts")
            
            # Statistics
            success_rate = (success_count / ping_count) * 100
            logger.info(f"📊 Stats: {success_count}/{ping_count} successful ({success_rate:.1f}%)")
            
            # Sleep until next ping
            logger.info(f"💤 Sleeping for {PING_INTERVAL}s...")
            time.sleep(PING_INTERVAL)
            
    except KeyboardInterrupt:
        logger.info("\n⚠️ Pinger stopped by user")
        logger.info(f"Final stats: {success_count}/{ping_count} successful")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)

if __name__ == "__main__":
    run_continuous_pinger()

#!/usr/bin/env python3
"""
Multiarch test application that displays system info, world timezones, and monitors IP.
"""
import platform
import os
import time
import logging
import sys
import current_time
import whatsmyip

# Configure logging to output to stdout/stderr for Kubernetes logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

def main():
    logger.info("="*60)
    logger.info("Multiarch Test Application")
    logger.info("="*60)
    logger.info(f"Platform: {platform.machine()}")
    logger.info(f"OPENBLAS_CORETYPE: {os.getenv('OPENBLAS_CORETYPE')}")
    logger.info(f"Python Version: {platform.python_version()}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info("="*60)
    
    # Show world timezones
    current_time.show_world_timezones()
    
    # Start IP monitoring
    logger.info("Starting IP monitoring...")
    monitor = whatsmyip.IPMonitor(check_interval=3600)  # Check every hour
    monitor.start_monitoring()
    
    # Run forever with error handling
    iteration = 0
    consecutive_errors = 0
    max_consecutive_errors = 10
    sleep_interval = 60  # 1 minute between iterations
    
    logger.info("Starting main loop - running indefinitely...")
    
    try:
        while True:
            iteration += 1
            try:
                logger.info(f"Iteration {iteration}")
                current_time.show_world_timezones()
                consecutive_errors = 0  # Reset error counter on success
                time.sleep(sleep_interval)
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error in iteration {iteration}: {e}", exc_info=True)
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.critical(f"Too many consecutive errors ({consecutive_errors}). Waiting longer before retry...")
                    time.sleep(300)  # Wait 5 minutes before retrying
                    consecutive_errors = 0  # Reset after long wait
                else:
                    # Exponential backoff: 2^errors seconds, max 60 seconds
                    backoff_time = min(2 ** consecutive_errors, 60)
                    logger.warning(f"Waiting {backoff_time} seconds before retry (error count: {consecutive_errors})")
                    time.sleep(backoff_time)
        
    except KeyboardInterrupt:
        logger.info(f"\nInterrupted at iteration {iteration}. Shutting down...")
        monitor.stop_monitoring()
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        monitor.stop_monitoring()
        raise

if __name__ == "__main__":
    main()

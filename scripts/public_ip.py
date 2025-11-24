#!/usr/bin/env python3
"""
Get public IP address and post to Redis.
"""
import time
import requests
import logging
import sys
import os
import redis
import json
from datetime import datetime
import pytz

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

_redis_client = None

def get_redis_client(retry=True):
    """Get Redis client using environment variables from secrets. Implements connection pooling and retry logic."""
    global _redis_client
    
    # Return existing client if available and healthy
    if _redis_client:
        try:
            _redis_client.ping()
            return _redis_client
        except Exception as e:
            logger.warning(f"Existing Redis connection unhealthy: {e}. Reconnecting...")
            _redis_client = None
    
    try:
        redis_host = os.getenv('REDIS_HOST')
        redis_port = int(os.getenv('REDIS_PORT', '6379'))
        redis_password = os.getenv('REDIS_PASSWORD')
        
        if not redis_host:
            logger.warning("REDIS_HOST not set, Redis connection will be skipped")
            return None
        
        client = redis.Redis(
            host=redis_host,
            port=redis_port,
            password=redis_password,
            decode_responses=True,
            socket_connect_timeout=10,
            socket_timeout=10,
            retry_on_timeout=True,
            health_check_interval=30
        )
        # Test connection
        client.ping()
        logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
        _redis_client = client
        return client
    except redis.ConnectionError as e:
        logger.warning(f"Redis connection error: {e}")
        if retry:
            logger.info("Will retry Redis connection on next attempt")
        return None
    except Exception as e:
        logger.warning(f"Failed to connect to Redis: {e}")
        return None

def get_public_ip(max_retries=3):
    """Get public IP address using multiple services as fallback with retry logic."""
    ip_services = [
        "https://api.ipify.org?format=text",
        "https://ifconfig.me/ip",
        "https://icanhazip.com",
    ]
    
    for service in ip_services:
        for attempt in range(max_retries):
            try:
                response = requests.get(service, timeout=10)
                if response.status_code == 200:
                    ip = response.text.strip()
                    if ip and len(ip.split('.')) == 4:  # Basic IP validation
                        return ip
                    else:
                        logger.warning(f"Invalid IP format from {service}: {ip}")
            except requests.Timeout as e:
                logger.warning(f"Timeout fetching IP from {service} (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
            except requests.RequestException as e:
                logger.warning(f"Error fetching IP from {service}: {e}")
                break  # Try next service
            except Exception as e:
                logger.warning(f"Unexpected error from {service}: {e}")
                break  # Try next service
    return None

def post_to_redis(redis_client, public_ip, max_retries=3):
    """Post public IP and timestamp to Redis key ip.control.publicIp with retry logic."""
    if not redis_client:
        # Try to get a new connection
        redis_client = get_redis_client()
        if not redis_client:
            return False
    
    key = "ip.control.publicIp"
    timestamp = datetime.now(pytz.UTC)
    
    data = {
        "public_ip": public_ip,
        "timestamp": timestamp.isoformat(),
        "timestamp_formatted": timestamp.strftime('%Y-%m-%d %H:%M:%S %Z'),
        "updated_at": datetime.now(pytz.UTC).isoformat()
    }
    
    value = json.dumps(data, default=str)
    
    for attempt in range(max_retries):
        try:
            redis_client.set(key, value)
            logger.info(f"Posted public IP {public_ip} to Redis key: {key}")
            return True
        except redis.ConnectionError as e:
            logger.warning(f"Redis connection error (attempt {attempt + 1}/{max_retries}): {e}")
            if attempt < max_retries - 1:
                # Try to reconnect
                redis_client = get_redis_client()
                if not redis_client:
                    time.sleep(2 ** attempt)  # Exponential backoff
                    continue
            else:
                logger.error(f"Failed to post to Redis after {max_retries} attempts")
                return False
        except Exception as e:
            logger.error(f"Failed to post to Redis: {e}")
            return False
    
    return False

def main():
    """Main function to run IP monitoring and posting forever with error handling."""
    logger.info("="*60)
    logger.info("Public IP Monitor - Control Node")
    logger.info("="*60)
    
    # Connect to Redis
    redis_client = get_redis_client()
    
    # Run forever with error handling
    iteration = 0
    consecutive_errors = 0
    max_consecutive_errors = 10
    sleep_interval = 60  # 1 minute between iterations
    last_successful_ip = None
    
    logger.info("Starting main loop - running indefinitely...")
    
    try:
        while True:
            iteration += 1
            try:
                logger.info(f"Iteration {iteration}")
                
                # Get public IP
                public_ip = get_public_ip()
                if public_ip:
                    logger.info(f"Public IP: {public_ip}")
                    
                    # Only post if IP changed or first time
                    if public_ip != last_successful_ip:
                        if post_to_redis(redis_client, public_ip):
                            last_successful_ip = public_ip
                            consecutive_errors = 0  # Reset error counter on success
                        else:
                            consecutive_errors += 1
                    else:
                        logger.debug(f"IP unchanged: {public_ip}")
                        consecutive_errors = 0
                else:
                    logger.error("Failed to retrieve public IP address")
                    consecutive_errors += 1
                
                # Sleep between iterations
                time.sleep(sleep_interval)
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error in iteration {iteration}: {e}", exc_info=True)
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.critical(f"Too many consecutive errors ({consecutive_errors}). Waiting longer before retry...")
                    time.sleep(300)  # Wait 5 minutes before retrying
                    consecutive_errors = 0  # Reset after long wait
                    # Try to reconnect to Redis
                    redis_client = get_redis_client()
                else:
                    # Exponential backoff: 2^errors seconds, max 60 seconds
                    backoff_time = min(2 ** consecutive_errors, 60)
                    logger.warning(f"Waiting {backoff_time} seconds before retry (error count: {consecutive_errors})")
                    time.sleep(backoff_time)
        
    except KeyboardInterrupt:
        logger.info(f"\nInterrupted at iteration {iteration}. Shutting down...")
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()


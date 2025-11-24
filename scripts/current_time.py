#!/usr/bin/env python3
"""
Display current time in various timezones around the world and post to Redis.
"""
from datetime import datetime
import pytz
import logging
import os
import redis
import json
import time

logger = logging.getLogger(__name__)

_redis_client = None
_redis_client_lock = False

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

def post_to_redis(redis_client, timestamp_data, max_retries=3):
    """Post timestamp data to Redis key timestamp.servertime with retry logic."""
    if not redis_client:
        # Try to get a new connection
        redis_client = get_redis_client()
        if not redis_client:
            return False
    
    key = "timestamp.servertime"
    value = json.dumps(timestamp_data, default=str)
    
    for attempt in range(max_retries):
        try:
            redis_client.set(key, value)
            logger.info(f"Posted timestamp to Redis key: {key}")
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

def show_world_timezones():
    """Display current time in various timezones around the world and post to Redis."""
    timezones = {
        "UTC": pytz.UTC,
        "New York (EST/EDT)": pytz.timezone("America/New_York"),
        "Los Angeles (PST/PDT)": pytz.timezone("America/Los_Angeles"),
        "London (GMT/BST)": pytz.timezone("Europe/London"),
        "Paris (CET/CEST)": pytz.timezone("Europe/Paris"),
        "Tokyo (JST)": pytz.timezone("Asia/Tokyo"),
        "Sydney (AEDT/AEST)": pytz.timezone("Australia/Sydney"),
        "Mumbai (IST)": pytz.timezone("Asia/Kolkata"),
        "Dubai (GST)": pytz.timezone("Asia/Dubai"),
        "São Paulo (BRT/BRST)": pytz.timezone("America/Sao_Paulo"),
    }
    
    now_utc = datetime.now(pytz.UTC)
    
    logger.info("\n" + "="*60)
    logger.info("Current Time in Various Timezones")
    logger.info("="*60)
    
    timezone_data = {}
    for city, tz in timezones.items():
        local_time = now_utc.astimezone(tz)
        time_str = local_time.strftime('%Y-%m-%d %H:%M:%S %Z')
        logger.info(f"{city:25} : {time_str}")
        timezone_data[city] = time_str
    
    logger.info("="*60 + "\n")
    
    # Prepare data for Redis
    timestamp_data = {
        "utc_timestamp": now_utc.isoformat(),
        "utc_formatted": now_utc.strftime('%Y-%m-%d %H:%M:%S %Z'),
        "timezones": timezone_data,
        "updated_at": datetime.now(pytz.UTC).isoformat()
    }
    
    # Post to Redis
    redis_client = get_redis_client()
    post_to_redis(redis_client, timestamp_data)
    
    return now_utc

if __name__ == "__main__":
    show_world_timezones()


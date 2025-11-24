#!/usr/bin/env python3
"""
Multiarch test application that displays system info, world timezones, and monitors IP.
"""
import platform
import os
import time
import current_time
import whatsmyip

def main():
    print("="*60)
    print("Multiarch Test Application")
    print("="*60)
    print(f"Platform: {platform.machine()}")
    print(f"OPENBLAS_CORETYPE: {os.getenv('OPENBLAS_CORETYPE')}")
    print(f"Python Version: {platform.python_version()}")
    print(f"Platform: {platform.platform()}")
    print("="*60)
    
    # Show world timezones
    current_time.show_world_timezones()
    
    # Start IP monitoring
    print("Starting IP monitoring...")
    monitor = whatsmyip.IPMonitor(check_interval=3600)  # Check every hour
    monitor.start_monitoring()
    
    # Keep the application running
    try:
        while True:
            time.sleep(60)  # Sleep for 1 minute, then show time again
            current_time.show_world_timezones()
    except KeyboardInterrupt:
        print("\nShutting down...")
        monitor.stop_monitoring()

if __name__ == "__main__":
    main()

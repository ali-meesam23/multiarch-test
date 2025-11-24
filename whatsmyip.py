#!/usr/bin/env python3
"""
Check public IP address and monitor for changes.
Prints new IP if it changes.
"""
import time
import requests
import threading

class IPMonitor:
    def __init__(self, check_interval=3600):  # Default: 1 hour
        self.check_interval = check_interval
        self.current_ip = None
        self.running = False
        self.thread = None
        self.ip_services = [
            "https://api.ipify.org?format=text",
            "https://ifconfig.me/ip",
            "https://icanhazip.com",
        ]
    
    def get_public_ip(self):
        """Get public IP address using multiple services as fallback."""
        for service in self.ip_services:
            try:
                response = requests.get(service, timeout=5)
                if response.status_code == 200:
                    ip = response.text.strip()
                    if ip:
                        return ip
            except Exception as e:
                print(f"Error fetching IP from {service}: {e}")
                continue
        return None
    
    def check_ip(self):
        """Check IP and print if it changed."""
        ip = self.get_public_ip()
        if ip:
            if self.current_ip is None:
                print(f"[IP Monitor] Initial IP detected: {ip}")
                self.current_ip = ip
            elif ip != self.current_ip:
                print(f"[IP Monitor] IP CHANGED!")
                print(f"[IP Monitor] Old IP: {self.current_ip}")
                print(f"[IP Monitor] New IP: {ip}")
                self.current_ip = ip
            else:
                print(f"[IP Monitor] IP unchanged: {ip}")
        else:
            print("[IP Monitor] Failed to retrieve IP address")
    
    def start_monitoring(self):
        """Start monitoring IP in a background thread."""
        if self.running:
            print("[IP Monitor] Already running")
            return
        
        self.running = True
        
        # Do initial check
        self.check_ip()
        
        def monitor_loop():
            while self.running:
                time.sleep(self.check_interval)
                if self.running:
                    self.check_ip()
        
        self.thread = threading.Thread(target=monitor_loop, daemon=True)
        self.thread.start()
        print(f"[IP Monitor] Started monitoring (checking every {self.check_interval} seconds)")
    
    def stop_monitoring(self):
        """Stop monitoring IP."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2)
        print("[IP Monitor] Stopped monitoring")

if __name__ == "__main__":
    monitor = IPMonitor(check_interval=3600)  # Check every hour
    monitor.start_monitoring()
    
    try:
        # Keep running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[IP Monitor] Shutting down...")
        monitor.stop_monitoring()


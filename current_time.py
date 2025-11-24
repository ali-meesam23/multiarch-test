#!/usr/bin/env python3
"""
Display current time in various timezones around the world.
"""
from datetime import datetime
import pytz

def show_world_timezones():
    """Display current time in various timezones around the world."""
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
    
    print("\n" + "="*60)
    print("Current Time in Various Timezones")
    print("="*60)
    
    for city, tz in timezones.items():
        local_time = now_utc.astimezone(tz)
        print(f"{city:25} : {local_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    print("="*60 + "\n")
    
    return now_utc

if __name__ == "__main__":
    show_world_timezones()


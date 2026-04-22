#!/usr/bin/env python3
"""
Sri Lanka Solar Tracker IoT Data Simulator (Final Version)

This script generates realistic solar tracker sensor readings for Sri Lankan
tropical climate conditions and posts them to a FastAPI backend.
It matches the exact final JSON schema required for ML training and system testing.
"""

import argparse
import random
import math
import logging
import time
from datetime import datetime, timedelta
import zoneinfo
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

TZ = zoneinfo.ZoneInfo("Asia/Colombo")

def get_session():
    session = requests.Session()
    retry = Retry(connect=3, backoff_factor=0.5)
    adapter = HTTPAdapter(max_retries=retry)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    return session

class SolarSimulator:
    def __init__(self, mode="clear"):
        self.mode = mode
        self.fan_is_on = False
        
        # Mode specific parameters
        if mode == "clear":
            self.max_lux = random.uniform(80000, 110000)
            self.cloud_prob = 0.02
        elif mode == "partly_cloudy":
            self.max_lux = random.uniform(60000, 95000)
            self.cloud_prob = 0.10
        elif mode == "monsoon":
            self.max_lux = random.uniform(30000, 70000)
            self.cloud_prob = 0.30
            
        self.current_cloud_depth = 1.0
        self.cloud_time_remaining = 0
        
    def _update_clouds(self, interval_sec):
        if self.cloud_time_remaining <= 0:
            if random.random() < self.cloud_prob:
                self.cloud_time_remaining = random.randint(120, 900) # 2-15 minutes
                self.current_cloud_depth = random.uniform(0.2, 0.8) # 20%-80% reduction
            else:
                self.current_cloud_depth = min(1.0, self.current_cloud_depth + 0.05)
        else:
            self.cloud_time_remaining -= interval_sec
            
        return self.current_cloud_depth

    def generate_reading(self, current_time: datetime, interval_sec: int, device_id: str) -> dict:
        hour = current_time.hour + current_time.minute / 60.0 + current_time.second / 3600.0
        
        # 1. Daylight curve (06:00 to 18:00)
        is_day = 6.0 <= hour <= 18.0
        
        if is_day:
            # Sine wave from 6 to 18
            sun_angle = (hour - 6.0) / 12.0 * math.pi
            base_lux = math.sin(sun_angle) * self.max_lux
        else:
            base_lux = random.uniform(0, 200)

        # 2. Clouds
        cloud_factor = self._update_clouds(interval_sec) if is_day else 1.0
        lux = max(0, base_lux * cloud_factor + random.uniform(-500, 500))
        if lux < 0: lux = 0.0

        # 3. Temperature 
        # Base temp: night ~25, day peak ~33 at 14:00
        temp_base = 25.5
        if is_day:
            temp_base += math.sin((hour - 6.0) / 12.0 * math.pi) * 8.0
            if hour > 12:
                temp_base += 1.5 # Lag effect
        if self.mode == "monsoon":
            temp_base -= 2.0
            
        temperature = temp_base + random.uniform(-0.5, 0.5)

        # 4. Humidity
        # Night ~85%, Midday ~65%
        humidity_base = 85.0
        if is_day:
            humidity_base -= math.sin((hour - 6.0) / 12.0 * math.pi) * 20.0
        if self.mode == "monsoon":
            humidity_base += 10.0
        
        humidity = max(0, min(100, humidity_base + random.uniform(-2, 2)))

        # 5. Servo Angle
        # Single-axis east-to-west tracking: 75 at 06:00, 90 at 12:00, 105 at 18:00
        if hour < 6.0:
            target_angle = 75.0
        elif hour > 18.0:
            target_angle = 105.0
        else:
            target_angle = 75.0 + ((hour - 6.0) / 12.0) * 30.0
            
        servo_angle = target_angle + random.uniform(-2.0, 2.0)

        # 6. LDR Values (0-4095)
        # Directly proportional to lux, slight difference based on angle tracking error
        tracking_error = (servo_angle - target_angle)
        
        ldr_base = (lux / 110000.0) * 4095.0
        ldr_left = ldr_base + (tracking_error * 50) + random.uniform(-50, 50)
        ldr_right = ldr_base - (tracking_error * 50) + random.uniform(-50, 50)
        
        ldr_left = int(max(0, min(4095, ldr_left)))
        ldr_right = int(max(0, min(4095, ldr_right)))

        # 7. Power Generation Model (Updated for ~6V, ~2W mini solar panel)
        if lux > 1000:
            # Voltage drops slightly as temperature increases (temp coeff ~ -0.3%/C above 25C)
            temp_diff = max(0, temperature - 25.0)
            voltage = 6.4 * (1 - (0.003 * temp_diff)) + random.uniform(-0.1, 0.1)
            
            # Current proportional to lux (Max ~0.35A)
            current = (lux / 110000.0) * 0.35 + random.uniform(-0.01, 0.01) 
            
            voltage = max(0, voltage)
            current = max(0, current)
        else:
            voltage = random.uniform(0, 0.5)
            current = random.uniform(0, 0.005)
            
        power = voltage * current

        # 8. Fan Logic
        # Turn ON when temp > 25°C
        # Turn OFF when temp < 23°C (hysteresis prevents bouncing)
        if temperature > 25.0:
            self.fan_is_on = True
        elif temperature < 23.0:
            self.fan_is_on = False
            
        fan_status = "ON" if self.fan_is_on else "OFF"

        # 9. Status
        status = "error" if random.random() < 0.01 else "ok"

        return {
            "device_id": device_id,
            "timestamp": current_time.isoformat(),
            "servo_angle": int(round(servo_angle)),
            "temperature": round(temperature, 1),
            "humidity": round(humidity, 1),
            "lux": int(round(lux)),
            "ldr_left": ldr_left,
            "ldr_right": ldr_right,
            "voltage": round(voltage, 1),
            "current": round(current, 1),
            "power": round(power, 1),
            "fan_status": fan_status,
            "status": status
        }

def main():
    parser = argparse.ArgumentParser(description="Sri Lanka Solar Tracker Simulator")
    parser.add_argument("--device_id", default="tracker01", help="Device ID")
    parser.add_argument("--base_url", default="http://127.0.0.1:8000", help="FastAPI Backend URL")
    parser.add_argument("--interval_sec", type=int, default=10, help="Interval between readings in seconds")
    parser.add_argument("--days", type=int, default=1, help="Number of days to simulate")
    parser.add_argument("--mode", choices=["clear", "partly_cloudy", "monsoon"], default="clear", help="Weather mode")
    
    args = parser.parse_args()
    
    session = get_session()
    url = f"{args.base_url}/api/readings"
    
    start_time = datetime.now(TZ) - timedelta(days=args.days)
    # Start at midnight for cleaner daily curves
    start_time = start_time.replace(hour=0, minute=0, second=0, microsecond=0)
    
    end_time = datetime.now(TZ)
    current_time = start_time
    
    simulator = SolarSimulator(mode=args.mode)
    
    total_expected = int((end_time - start_time).total_seconds() / args.interval_sec)
    count = 0
    
    logging.info(f"Starting simulation for {args.days} days ({total_expected} readings) in {args.mode} mode")
    
    while current_time < end_time:
        reading = simulator.generate_reading(current_time, args.interval_sec, args.device_id)
        
        try:
            # Add predict=true ? Not specifically requested, but endpoint is /api/readings
            response = session.post(url, json=reading, timeout=5)
            if response.status_code in [200, 201]:
                logging.info(f"[{current_time.strftime('%Y-%m-%d %H:%M:%S')}] OK: {reading['power']}W, {reading['lux']}lux")
            else:
                logging.warning(f"Backend error: {response.status_code} - {response.text}")
        except Exception as e:
            logging.error(f"Failed to post reading: {e}")
            
        current_time += timedelta(seconds=args.interval_sec)
        count += 1
        
    logging.info(f"Simulation complete. Sent {count} readings.")

if __name__ == "__main__":
    main()
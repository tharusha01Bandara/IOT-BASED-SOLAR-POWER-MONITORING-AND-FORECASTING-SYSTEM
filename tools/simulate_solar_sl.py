#!/usr/bin/env python3
"""
Sri Lanka Solar Tracker IoT Data Simulator

This script generates realistic solar tracker sensor readings for Sri Lankan
tropical climate conditions and posts them to a FastAPI backend.

Features:
- Realistic daily solar curves (sunrise ~06:00, sunset ~18:00)
- Tropical climate patterns (high humidity, warm temperatures)
- Cloud event simulation (random dips in irradiance)
- PV power model with temperature efficiency loss
- Single-axis east-west servo tracking
- Fan control with hysteresis
- Configurable weather modes (clear, partly_cloudy, monsoon)
- Network retry logic with exponential backoff

Author: Solar Monitoring System
Version: 1.0.0
"""

import argparse
import json
import logging
import math
import random
import sys
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from enum import Enum

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# Try to import pytz for timezone support, fallback to datetime.timezone
try:
    import pytz
    COLOMBO_TZ = pytz.timezone('Asia/Colombo')
    HAS_PYTZ = True
except ImportError:
    from datetime import timezone
    # Sri Lanka is UTC+5:30
    COLOMBO_TZ = timezone(timedelta(hours=5, minutes=30))
    HAS_PYTZ = False
    print("Warning: pytz not installed. Using UTC+5:30 offset. Install pytz for better timezone support.")


# ============================================================================
# Configuration and Constants
# ============================================================================

class WeatherMode(Enum):
    """Weather conditions for simulation"""
    CLEAR = "clear"
    PARTLY_CLOUDY = "partly_cloudy"
    MONSOON = "monsoon"


@dataclass
class WeatherConfig:
    """Weather-specific configuration parameters"""
    peak_lux_min: float
    peak_lux_max: float
    cloud_probability: float  # Probability of cloud event per minute
    cloud_intensity_min: float  # Min reduction factor (0-1)
    cloud_intensity_max: float  # Max reduction factor (0-1)
    cloud_duration_min: int  # Minutes
    cloud_duration_max: int  # Minutes
    temperature_offset: float  # Additional temperature offset
    humidity_boost: float  # Additional humidity percentage


# Weather mode configurations
WEATHER_CONFIGS = {
    WeatherMode.CLEAR: WeatherConfig(
        peak_lux_min=95000,
        peak_lux_max=110000,
        cloud_probability=0.02,
        cloud_intensity_min=0.10,
        cloud_intensity_max=0.30,
        cloud_duration_min=2,
        cloud_duration_max=8,
        temperature_offset=2.0,
        humidity_boost=-5.0
    ),
    WeatherMode.PARTLY_CLOUDY: WeatherConfig(
        peak_lux_min=70000,
        peak_lux_max=90000,
        cloud_probability=0.08,
        cloud_intensity_min=0.20,
        cloud_intensity_max=0.60,
        cloud_duration_min=3,
        cloud_duration_max=15,
        temperature_offset=0.0,
        humidity_boost=0.0
    ),
    WeatherMode.MONSOON: WeatherConfig(
        peak_lux_min=40000,
        peak_lux_max=70000,
        cloud_probability=0.15,
        cloud_intensity_min=0.40,
        cloud_intensity_max=0.85,
        cloud_duration_min=5,
        cloud_duration_max=25,
        temperature_offset=-3.0,
        humidity_boost=10.0
    )
}

# Sri Lanka specific constants
SUNRISE_HOUR = 6.0  # 06:00
SUNSET_HOUR = 18.0  # 18:00
LATITUDE = 7.8731  # Colombo, Sri Lanka

# PV panel characteristics (small research panel)
PANEL_AREA_M2 = 0.08  # ~80 cm² small panel
PANEL_EFFICIENCY = 0.18  # 18% efficiency
TEMP_COEFFICIENT_POWER = -0.004  # -0.4% per °C above 25°C
VOC_STANDARD = 18.0  # Open circuit voltage at 25°C
ISC_STANDARD = 1.0  # Short circuit current at 1000 W/m²
FILL_FACTOR = 0.75  # PV fill factor


# ============================================================================
# Logging Setup
# ============================================================================

def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging with timestamps and levels"""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    return logging.getLogger(__name__)


# ============================================================================
# Cloud Event Simulation
# ============================================================================

@dataclass
class CloudEvent:
    """Represents a cloud passing over the panel"""
    start_time: datetime
    end_time: datetime
    intensity: float  # Reduction factor (0 = no reduction, 1 = complete block)
    
    def is_active(self, current_time: datetime) -> bool:
        """Check if cloud event is currently affecting the panel"""
        return self.start_time <= current_time <= self.end_time
    
    def get_intensity(self, current_time: datetime) -> float:
        """Get cloud intensity with smooth edges"""
        if not self.is_active(current_time):
            return 0.0
        
        duration = (self.end_time - self.start_time).total_seconds()
        elapsed = (current_time - self.start_time).total_seconds()
        
        # Smooth transition using sine wave
        progress = elapsed / duration
        edge_factor = math.sin(progress * math.pi)
        
        return self.intensity * edge_factor


class CloudSimulator:
    """Manages cloud events during simulation"""
    
    def __init__(self, weather_config: WeatherConfig):
        self.config = weather_config
        self.active_clouds: List[CloudEvent] = []
    
    def update(self, current_time: datetime) -> None:
        """Update cloud events, remove expired ones, generate new ones"""
        # Remove expired clouds
        self.active_clouds = [
            cloud for cloud in self.active_clouds 
            if cloud.end_time > current_time
        ]
        
        # Chance to generate new cloud event
        if random.random() < self.config.cloud_probability / 60:  # Per second probability
            duration_minutes = random.uniform(
                self.config.cloud_duration_min,
                self.config.cloud_duration_max
            )
            
            intensity = random.uniform(
                self.config.cloud_intensity_min,
                self.config.cloud_intensity_max
            )
            
            end_time = current_time + timedelta(minutes=duration_minutes)
            
            cloud = CloudEvent(
                start_time=current_time,
                end_time=end_time,
                intensity=intensity
            )
            
            self.active_clouds.append(cloud)
    
    def get_total_reduction(self, current_time: datetime) -> float:
        """Get combined reduction factor from all active clouds"""
        total_reduction = 0.0
        
        for cloud in self.active_clouds:
            if cloud.is_active(current_time):
                total_reduction += cloud.get_intensity(current_time)
        
        # Cap at 0.95 (always some diffuse light)
        return min(total_reduction, 0.95)


# ============================================================================
# Solar Position and Daylight Calculations
# ============================================================================

def calculate_solar_hour_angle(local_time: datetime) -> float:
    """
    Calculate solar hour angle in degrees.
    Noon = 0°, morning negative, afternoon positive
    """
    hour = local_time.hour + local_time.minute / 60.0 + local_time.second / 3600.0
    solar_noon = 12.0
    hours_from_noon = hour - solar_noon
    
    # 15 degrees per hour
    hour_angle = hours_from_noon * 15.0
    
    return hour_angle


def calculate_daylight_factor(local_time: datetime) -> float:
    """
    Calculate daylight intensity factor (0 to 1) based on time of day.
    Uses Gaussian-like curve for realistic sunrise/sunset transitions.
    """
    hour = local_time.hour + local_time.minute / 60.0
    
    # Outside daylight hours
    if hour < SUNRISE_HOUR - 0.5 or hour > SUNSET_HOUR + 0.5:
        return 0.0
    
    # Solar noon is midpoint between sunrise and sunset
    solar_noon = (SUNRISE_HOUR + SUNSET_HOUR) / 2.0
    
    # Hours from solar noon
    hours_from_noon = abs(hour - solar_noon)
    max_hours = (SUNSET_HOUR - SUNRISE_HOUR) / 2.0
    
    if hours_from_noon > max_hours:
        return 0.0
    
    # Gaussian-like curve
    # Formula: exp(-0.5 * (x/sigma)^2)
    sigma = max_hours / 2.5  # Adjust spread
    factor = math.exp(-0.5 * (hours_from_noon / sigma) ** 2)
    
    # Add sunrise/sunset transitions
    if hour < SUNRISE_HOUR + 0.5:
        # Sunrise transition
        sunrise_progress = (hour - (SUNRISE_HOUR - 0.5)) / 1.0
        factor *= sunrise_progress ** 2
    elif hour > SUNSET_HOUR - 0.5:
        # Sunset transition
        sunset_progress = ((SUNSET_HOUR + 0.5) - hour) / 1.0
        factor *= sunset_progress ** 2
    
    return max(0.0, min(1.0, factor))


def calculate_servo_angle(local_time: datetime, noise_std: float = 0.5) -> float:
    """
    Calculate single-axis east-west tracking servo angle (degrees).
    
    Morning (east): ~40-60°
    Noon: ~90°
    Evening (west): ~120-140°
    
    Add small noise to simulate mechanical imperfections.
    """
    hour_angle = calculate_solar_hour_angle(local_time)
    
    # Map hour angle to servo angle
    # -90° (morning) -> 45°
    # 0° (noon) -> 90°
    # +90° (evening) -> 135°
    
    # Linear mapping with offset
    servo_angle = 90.0 + (hour_angle * 0.5)
    
    # Clamp to physical limits
    servo_angle = max(30.0, min(160.0, servo_angle))
    
    # Add mechanical noise
    noise = random.gauss(0, noise_std)
    servo_angle += noise
    
    return round(servo_angle, 1)


# ============================================================================
# Sensor Value Generation
# ============================================================================

class SolarSensorSimulator:
    """Generates realistic solar tracker sensor readings"""
    
    def __init__(self, weather_mode: WeatherMode, device_id: str):
        self.weather_config = WEATHER_CONFIGS[weather_mode]
        self.device_id = device_id
        self.cloud_simulator = CloudSimulator(self.weather_config)
        self.fan_state = False  # Track fan state for hysteresis
        
        # State for smooth transitions
        self.previous_values = {
            'temperature': 26.0,
            'humidity': 70.0,
            'voltage': 0.0,
            'current': 0.0
        }
    
    def generate_lux(self, local_time: datetime) -> float:
        """Generate realistic light intensity (lux)"""
        # Base daylight curve
        daylight_factor = calculate_daylight_factor(local_time)
        
        if daylight_factor < 0.01:
            return 0.0
        
        # Peak lux for weather condition
        peak_lux = random.uniform(
            self.weather_config.peak_lux_min,
            self.weather_config.peak_lux_max
        )
        
        # Base lux from solar position
        base_lux = peak_lux * daylight_factor
        
        # Apply cloud effects
        self.cloud_simulator.update(local_time)
        cloud_reduction = self.cloud_simulator.get_total_reduction(local_time)
        lux = base_lux * (1.0 - cloud_reduction)
        
        # Add small random variations (atmospheric turbulence)
        lux *= random.uniform(0.97, 1.03)
        
        return round(max(0.0, lux), 1)
    
    def generate_temperature(self, local_time: datetime, lux: float) -> float:
        """Generate realistic temperature (°C) for Sri Lankan climate"""
        hour = local_time.hour + local_time.minute / 60.0
        
        # Base temperature curve
        # Night: ~24-27°C
        # Day: ~30-36°C
        
        # Daily cycle (peaks around 14:00)
        time_factor = math.sin((hour - 6.0) * math.pi / 12.0)  # 0 at 6am, 1 at 2pm
        time_factor = max(0.0, time_factor)
        
        night_temp = random.uniform(24.0, 27.0)
        day_temp = random.uniform(30.0, 36.0)
        
        base_temp = night_temp + (day_temp - night_temp) * time_factor
        
        # Additional heating from solar irradiance on panel
        if lux > 10000:
            panel_heating = (lux / 100000.0) * random.uniform(2.0, 5.0)
            base_temp += panel_heating
        
        # Weather mode offset
        base_temp += self.weather_config.temperature_offset
        
        # Small random variations
        base_temp += random.uniform(-0.5, 0.5)
        
        # Smooth transition from previous value
        alpha = 0.7  # Smoothing factor
        temp = alpha * base_temp + (1 - alpha) * self.previous_values['temperature']
        self.previous_values['temperature'] = temp
        
        return round(temp, 1)
    
    def generate_humidity(self, local_time: datetime, temperature: float) -> float:
        """Generate realistic humidity (%) for Sri Lankan climate"""
        hour = local_time.hour + local_time.minute / 60.0
        
        # Sri Lanka has high humidity year-round
        # Morning/evening: higher (75-90%)
        # Midday: slightly lower (60-75%)
        
        # Daily cycle (inverse of temperature)
        time_factor = math.sin((hour - 6.0) * math.pi / 12.0)
        time_factor = max(0.0, time_factor)
        
        morning_humidity = random.uniform(75.0, 90.0)
        midday_humidity = random.uniform(60.0, 75.0)
        
        base_humidity = morning_humidity - (morning_humidity - midday_humidity) * time_factor
        
        # Higher temperature slightly reduces relative humidity
        temp_adjustment = (temperature - 25.0) * -0.5
        base_humidity += temp_adjustment
        
        # Weather mode boost
        base_humidity += self.weather_config.humidity_boost
        
        # Clamp to valid range
        base_humidity = max(50.0, min(95.0, base_humidity))
        
        # Smooth transition
        alpha = 0.6
        humidity = alpha * base_humidity + (1 - alpha) * self.previous_values['humidity']
        self.previous_values['humidity'] = humidity
        
        return round(humidity, 1)
    
    def generate_pv_outputs(self, lux: float, temperature: float) -> Tuple[float, float, float]:
        """
        Generate realistic PV electrical outputs using simplified PV model.
        
        Returns: (voltage, current, power) tuple
        """
        if lux < 1000:  # No significant output below ~1000 lux
            return (0.0, 0.0, 0.0)
        
        # Convert lux to approximate irradiance (W/m²)
        # Rough approximation: 1000 W/m² ≈ 100,000 lux for sunlight
        irradiance = (lux / 100000.0) * 1000.0  # W/m²
        
        # Temperature effect on voltage (decreases with temp)
        temp_delta = temperature - 25.0  # Reference temperature
        voltage_factor = 1.0 + (TEMP_COEFFICIENT_POWER * temp_delta)
        voltage = VOC_STANDARD * voltage_factor * (irradiance / 1000.0)
        
        # Voltage sags under load (MPP is ~80% of Voc)
        voltage *= 0.80
        
        # Current is proportional to irradiance
        current = ISC_STANDARD * (irradiance / 1000.0)
        
        # Apply fill factor for realistic MPP
        power = voltage * current * FILL_FACTOR
        
        # Add small random variations for measurement noise
        voltage *= random.uniform(0.98, 1.02)
        current *= random.uniform(0.98, 1.02)
        power = voltage * current  # Recalculate with noise
        
        # Smooth transitions
        alpha = 0.75
        voltage = alpha * voltage + (1 - alpha) * self.previous_values['voltage']
        current = alpha * current + (1 - alpha) * self.previous_values['current']
        
        self.previous_values['voltage'] = voltage
        self.previous_values['current'] = current
        
        # Clamp to physical limits
        voltage = max(0.0, min(18.0, voltage))
        current = max(0.0, min(1.2, current))
        power = voltage * current
        
        return (
            round(voltage, 2),
            round(current, 3),
            round(power, 2)
        )
    
    def generate_fan_status(self, temperature: float) -> str:
        """
        Generate fan status with hysteresis to prevent rapid on/off cycling.
        
        ON if temp > 40°C
        OFF if temp < 38°C
        Otherwise, maintain previous state
        """
        if temperature > 40.0:
            self.fan_state = True
        elif temperature < 38.0:
            self.fan_state = False
        # else: maintain current state
        
        return "on" if self.fan_state else "off"
    
    def generate_status(self) -> str:
        """
        Generate device status.
        Occasionally generate 'error' to test error handling (1% probability)
        """
        if random.random() < 0.01:
            return "error"
        return "online"
    
    def generate_reading(self, timestamp: datetime) -> dict:
        """Generate complete sensor reading"""
        # Generate all sensor values
        lux = self.generate_lux(timestamp)
        temperature = self.generate_temperature(timestamp, lux)
        humidity = self.generate_humidity(timestamp, temperature)
        servo_angle = calculate_servo_angle(timestamp)
        voltage, current, power = self.generate_pv_outputs(lux, temperature)
        fan_status = self.generate_fan_status(temperature)
        status = self.generate_status()
        
        # Format timestamp
        if HAS_PYTZ:
            ts_str = timestamp.isoformat()
        else:
            ts_str = timestamp.isoformat()
        
        return {
            "device_id": self.device_id,
            "timestamp": ts_str,
            "servo_angle": servo_angle,
            "temperature": temperature,
            "humidity": humidity,
            "lux": lux,
            "voltage": voltage,
            "current": current,
            "power": power,
            "fan_status": fan_status,
            "status": status
        }


# ============================================================================
# HTTP Client with Retry Logic
# ============================================================================

class APIClient:
    """HTTP client with retry logic and backoff"""
    
    def __init__(self, base_url: str, timeout: int = 10):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.session = self._create_session()
        self.consecutive_failures = 0
        self.max_failures_before_warn = 5
    
    def _create_session(self) -> requests.Session:
        """Create requests session with retry logic"""
        session = requests.Session()
        
        # Configure retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["POST"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        return session
    
    def post_reading(self, reading: dict, logger: logging.Logger) -> bool:
        """
        Post sensor reading to API endpoint.
        
        Returns: True if successful, False otherwise
        """
        url = f"{self.base_url}/api/readings"
        
        try:
            response = self.session.post(
                url,
                json=reading,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            
            # Success
            self.consecutive_failures = 0
            
            result = response.json()
            logger.debug(
                f"✓ Posted reading | Device: {reading['device_id']} | "
                f"Power: {reading['power']:.2f}W | Lux: {reading['lux']:.0f}"
            )
            
            return True
            
        except requests.exceptions.Timeout:
            self.consecutive_failures += 1
            logger.warning(f"⚠ Timeout posting reading (attempt {self.consecutive_failures})")
            return False
            
        except requests.exceptions.ConnectionError as e:
            self.consecutive_failures += 1
            if self.consecutive_failures <= self.max_failures_before_warn:
                logger.warning(f"⚠ Connection error: {e}")
            elif self.consecutive_failures == self.max_failures_before_warn + 1:
                logger.error("✗ Backend appears to be down. Will continue simulating...")
            return False
            
        except requests.exceptions.HTTPError as e:
            self.consecutive_failures += 1
            logger.error(f"✗ HTTP error {e.response.status_code}: {e.response.text}")
            return False
            
        except Exception as e:
            self.consecutive_failures += 1
            logger.error(f"✗ Unexpected error posting reading: {e}")
            return False


# ============================================================================
# Main Simulator
# ============================================================================

class SolarTrackerSimulator:
    """Main simulator orchestrator"""
    
    def __init__(
        self,
        device_id: str,
        base_url: str,
        weather_mode: WeatherMode,
        interval_sec: float,
        start_time: Optional[datetime] = None,
        logger: Optional[logging.Logger] = None
    ):
        self.device_id = device_id
        self.interval_sec = interval_sec
        self.weather_mode = weather_mode
        self.logger = logger or logging.getLogger(__name__)
        
        # Initialize components
        self.sensor_simulator = SolarSensorSimulator(weather_mode, device_id)
        self.api_client = APIClient(base_url)
        
        # Start time
        if start_time:
            self.current_time = start_time
        else:
            if HAS_PYTZ:
                self.current_time = datetime.now(COLOMBO_TZ)
            else:
                self.current_time = datetime.now(COLOMBO_TZ)
        
        # Statistics
        self.readings_generated = 0
        self.readings_posted = 0
        self.readings_failed = 0
    
    def simulate_days(self, num_days: int) -> None:
        """
        Simulate specified number of days of solar tracker operation.
        """
        self.logger.info("=" * 70)
        self.logger.info("Sri Lanka Solar Tracker Simulator - Starting")
        self.logger.info("=" * 70)
        self.logger.info(f"Device ID:     {self.device_id}")
        self.logger.info(f"Weather Mode:  {self.weather_mode.value}")
        self.logger.info(f"Interval:      {self.interval_sec} seconds")
        self.logger.info(f"Duration:      {num_days} days")
        self.logger.info(f"Start Time:    {self.current_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        self.logger.info(f"Backend URL:   {self.api_client.base_url}/api/readings")
        self.logger.info("=" * 70)
        
        total_readings = int((num_days * 24 * 3600) / self.interval_sec)
        end_time = self.current_time + timedelta(days=num_days)
        
        self.logger.info(f"Will generate ~{total_readings:,} readings")
        self.logger.info("")
        
        try:
            while self.current_time < end_time:
                self._simulate_step()
                
                # Progress logging every 100 readings
                if self.readings_generated % 100 == 0:
                    success_rate = (
                        (self.readings_posted / self.readings_generated * 100)
                        if self.readings_generated > 0 else 0
                    )
                    self.logger.info(
                        f"Progress: {self.readings_generated:,}/{total_readings:,} readings "
                        f"| Success rate: {success_rate:.1f}% "
                        f"| Time: {self.current_time.strftime('%Y-%m-%d %H:%M:%S')}"
                    )
                
                # Advance time
                self.current_time += timedelta(seconds=self.interval_sec)
                
        except KeyboardInterrupt:
            self.logger.info("\n\n⚠ Simulation interrupted by user")
        
        self._print_summary()
    
    def _simulate_step(self) -> None:
        """Simulate one time step"""
        # Generate reading
        reading = self.sensor_simulator.generate_reading(self.current_time)
        self.readings_generated += 1
        
        # Post to API
        success = self.api_client.post_reading(reading, self.logger)
        
        if success:
            self.readings_posted += 1
        else:
            self.readings_failed += 1
    
    def _print_summary(self) -> None:
        """Print simulation summary"""
        self.logger.info("\n" + "=" * 70)
        self.logger.info("Simulation Complete")
        self.logger.info("=" * 70)
        self.logger.info(f"Total readings generated: {self.readings_generated:,}")
        self.logger.info(f"Successfully posted:      {self.readings_posted:,}")
        self.logger.info(f"Failed to post:           {self.readings_failed:,}")
        
        if self.readings_generated > 0:
            success_rate = (self.readings_posted / self.readings_generated) * 100
            self.logger.info(f"Success rate:             {success_rate:.2f}%")
        
        self.logger.info("=" * 70)


# ============================================================================
# CLI Interface
# ============================================================================

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Sri Lanka Solar Tracker IoT Data Simulator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Simulate 1 clear day with 10-second intervals
  python simulate_solar_sl.py --days 1 --mode clear --interval_sec 10

  # Simulate 3 monsoon days with 5-second intervals
  python simulate_solar_sl.py --days 3 --mode monsoon --interval_sec 5

  # Simulate partly cloudy day with custom device ID
  python simulate_solar_sl.py --device_id tracker02 --days 1 --mode partly_cloudy

  # Start from specific date/time
  python simulate_solar_sl.py --days 2 --start_date "2026-01-01 06:00:00"

Weather Modes:
  clear          - Clear sunny day (peak lux: 95-110k)
  partly_cloudy  - Intermittent clouds (peak lux: 70-90k)
  monsoon        - Heavy cloud cover (peak lux: 40-70k)
        """
    )
    
    parser.add_argument(
        '--device_id',
        type=str,
        default='tracker01',
        help='Device identifier (default: tracker01)'
    )
    
    parser.add_argument(
        '--base_url',
        type=str,
        default='http://127.0.0.1:8000',
        help='Base URL of FastAPI backend (default: http://127.0.0.1:8000)'
    )
    
    parser.add_argument(
        '--interval_sec',
        type=float,
        default=10.0,
        help='Interval between readings in seconds (default: 10)'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=1,
        help='Number of simulated days (default: 1)'
    )
    
    parser.add_argument(
        '--mode',
        type=str,
        choices=['clear', 'partly_cloudy', 'monsoon'],
        default='clear',
        help='Weather mode (default: clear)'
    )
    
    parser.add_argument(
        '--start_date',
        type=str,
        help='Start date/time (format: "YYYY-MM-DD HH:MM:SS", default: now)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose debug logging'
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    args = parse_arguments()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    
    # Parse weather mode
    weather_mode = WeatherMode(args.mode)
    
    # Parse start time
    start_time = None
    if args.start_date:
        try:
            # Parse without timezone first
            dt_naive = datetime.strptime(args.start_date, "%Y-%m-%d %H:%M:%S")
            # Localize to Colombo timezone
            if HAS_PYTZ:
                start_time = COLOMBO_TZ.localize(dt_naive)
            else:
                start_time = dt_naive.replace(tzinfo=COLOMBO_TZ)
        except ValueError as e:
            logger.error(f"Invalid start_date format: {e}")
            logger.error('Use format: "YYYY-MM-DD HH:MM:SS"')
            sys.exit(1)
    
    # Create and run simulator
    simulator = SolarTrackerSimulator(
        device_id=args.device_id,
        base_url=args.base_url,
        weather_mode=weather_mode,
        interval_sec=args.interval_sec,
        start_time=start_time,
        logger=logger
    )
    
    simulator.simulate_days(args.days)


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
Quick test script for the solar simulator.
Tests the simulator without posting to backend (dry run test).
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from simulate_solar_sl import (
    SolarSensorSimulator,
    WeatherMode,
    calculate_daylight_factor,
    calculate_servo_angle,
    COLOMBO_TZ,
    HAS_PYTZ
)


def test_sensor_generation():
    """Test sensor value generation without network calls"""
    
    print("=" * 70)
    print("Testing Solar Simulator Sensor Generation")
    print("=" * 70)
    print()
    
    # Create simulator
    simulator = SolarSensorSimulator(WeatherMode.CLEAR, "test_device")
    
    # Test times throughout the day
    test_times = [
        ("00:00", "Midnight (no sunlight)"),
        ("06:00", "Sunrise"),
        ("09:00", "Morning"),
        ("12:00", "Solar noon (peak)"),
        ("15:00", "Afternoon"),
        ("18:00", "Sunset"),
        ("21:00", "Night"),
    ]
    
    print("Generating sample readings for different times of day:\n")
    
    for time_str, description in test_times:
        # Create test timestamp
        if HAS_PYTZ:
            test_time = COLOMBO_TZ.localize(datetime(2026, 2, 23, int(time_str[:2]), int(time_str[3:])))
        else:
            test_time = datetime(2026, 2, 23, int(time_str[:2]), int(time_str[3:]), tzinfo=COLOMBO_TZ)
        
        # Generate reading
        reading = simulator.generate_reading(test_time)
        
        print(f"⏰ {description} ({time_str})")
        print(f"   Servo Angle: {reading['servo_angle']:.1f}°")
        print(f"   Temperature: {reading['temperature']:.1f}°C")
        print(f"   Humidity:    {reading['humidity']:.1f}%")
        print(f"   Lux:         {reading['lux']:,.0f}")
        print(f"   Voltage:     {reading['voltage']:.2f}V")
        print(f"   Current:     {reading['current']:.3f}A")
        print(f"   Power:       {reading['power']:.2f}W")
        print(f"   Fan Status:  {reading['fan_status']}")
        print(f"   Status:      {reading['status']}")
        print()
    
    print("=" * 70)
    print("✅ Sensor generation test complete!")
    print("=" * 70)
    print()


def test_daylight_curves():
    """Test daylight factor calculations"""
    
    print("=" * 70)
    print("Testing Daylight Factor Curve")
    print("=" * 70)
    print()
    
    print("Hour | Daylight Factor | Servo Angle")
    print("-----|-----------------|------------")
    
    for hour in range(0, 24):
        if HAS_PYTZ:
            test_time = COLOMBO_TZ.localize(datetime(2026, 2, 23, hour, 0))
        else:
            test_time = datetime(2026, 2, 23, hour, 0, tzinfo=COLOMBO_TZ)
        
        daylight = calculate_daylight_factor(test_time)
        servo = calculate_servo_angle(test_time, noise_std=0)
        
        bar = "█" * int(daylight * 50)
        print(f"{hour:02d}:00 | {daylight:6.3f} {bar:50s} | {servo:.1f}°")
    
    print()
    print("=" * 70)
    print("✅ Daylight curve test complete!")
    print("=" * 70)
    print()


def test_weather_modes():
    """Test different weather mode configurations"""
    
    print("=" * 70)
    print("Testing Weather Modes")
    print("=" * 70)
    print()
    
    # Noon on a typical day
    if HAS_PYTZ:
        test_time = COLOMBO_TZ.localize(datetime(2026, 2, 23, 12, 0))
    else:
        test_time = datetime(2026, 2, 23, 12, 0, tzinfo=COLOMBO_TZ)
    
    for mode in WeatherMode:
        print(f"🌤️  {mode.value.upper()}")
        
        simulator = SolarSensorSimulator(mode, "test_device")
        
        # Generate 5 samples and average
        lux_samples = []
        for _ in range(5):
            reading = simulator.generate_reading(test_time)
            lux_samples.append(reading['lux'])
        
        avg_lux = sum(lux_samples) / len(lux_samples)
        
        print(f"   Average peak lux: {avg_lux:,.0f}")
        print(f"   Sample readings:  {[f'{l:,.0f}' for l in lux_samples[:3]]}")
        print()
    
    print("=" * 70)
    print("✅ Weather mode test complete!")
    print("=" * 70)
    print()


def main():
    """Run all tests"""
    
    print("\n")
    print("╔" + "═" * 68 + "╗")
    print("║" + " " * 15 + "Solar Simulator Self-Test Suite" + " " * 21 + "║")
    print("╚" + "═" * 68 + "╝")
    print()
    
    try:
        # Test 1: Sensor generation
        test_sensor_generation()
        
        # Test 2: Daylight curves
        test_daylight_curves()
        
        # Test 3: Weather modes
        test_weather_modes()
        
        print("\n✅ All tests passed! Simulator is ready to use.")
        print("\nTo run the simulator, use:")
        print("  python simulate_solar_sl.py --days 1 --mode clear --interval_sec 10")
        print()
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()

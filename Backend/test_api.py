"""
Test Script - Sample Data Insertion

This script demonstrates how to send test data to the API.
Useful for development and testing.
"""

import requests
from datetime import datetime
import random
import time

# Configuration
API_BASE_URL = "http://localhost:8000/api"
DEVICE_ID = "tracker01"


def generate_sample_reading():
    """Generate a sample sensor reading with random data"""
    return {
        "device_id": DEVICE_ID,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "servo_angle": round(random.uniform(0, 180), 2),
        "temperature": round(random.uniform(20, 40), 2),
        "humidity": round(random.uniform(40, 80), 2),
        "lux": round(random.uniform(1000, 10000), 2),
        "voltage": round(random.uniform(15, 20), 2),
        "current": round(random.uniform(1, 3), 2),
        "power": round(random.uniform(15, 60), 2),
        "fan_status": random.choice(["on", "off", "auto"]),
        "status": random.choice(["online", "offline", "error", "maintenance"])
    }


def post_reading(reading):
    """Post a reading to the API"""
    try:
        response = requests.post(
            f"{API_BASE_URL}/readings",
            json=reading,
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error posting reading: {e}")
        # Print detailed error response
        try:
            error_detail = response.json()
            print(f"   Error details: {error_detail}")
        except:
            print(f"   Response text: {response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error posting reading: {e}")
        return None


def get_latest_reading():
    """Get the latest reading from the API"""
    try:
        response = requests.get(
            f"{API_BASE_URL}/readings/latest",
            params={"device_id": DEVICE_ID},
            timeout=5
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"❌ Error getting reading: {e}")
        # Print detailed error response
        try:
            error_detail = response.json()
            print(f"   Error details: {error_detail}")
        except:
            print(f"   Response text: {response.text}")
        return None
    except requests.exceptions.RequestException as e:
        print(f"❌ Error getting reading: {e}")
        return None


def check_health():
    """Check API health"""
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=5)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"❌ Error checking health: {e}")
        return None


def main():
    """Main test function"""
    print("=" * 60)
    print("Solar Monitoring System - Test Script")
    print("=" * 60)
    print()
    
    # Check health
    print("🔍 Checking API health...")
    health = check_health()
    if health:
        print(f"✅ API Status: {health.get('status')}")
        print(f"✅ Database: {health.get('database')}")
        print(f"✅ Version: {health.get('version')}")
    else:
        print("❌ API is not responding. Please start the server.")
        return
    
    print()
    
    # Send sample readings
    print("📤 Sending sample readings...")
    for i in range(5):
        reading = generate_sample_reading()
        print(f"\n📊 Reading #{i+1}:")
        print(f"   Temperature: {reading['temperature']}°C")
        print(f"   Humidity: {reading['humidity']}%")
        print(f"   Power: {reading['power']}W")
        print(f"   Lux: {reading['lux']} lux")
        
        result = post_reading(reading)
        if result:
            print(f"   ✅ Stored successfully (ID: {result.get('inserted_id')})")
        else:
            print("   ❌ Failed to store")
        
        time.sleep(1)  # Wait 1 second between readings
    
    print()
    
    # Get latest reading
    print("📥 Retrieving latest reading...")
    latest = get_latest_reading()
    if latest:
        print("✅ Latest reading:")
        print(f"   Device: {latest.get('device_id')}")
        print(f"   Timestamp: {latest.get('timestamp')}")
        print(f"   Temperature: {latest.get('temperature')}°C")
        print(f"   Power: {latest.get('power')}W")
        print(f"   Status: {latest.get('status')}")
    else:
        print("❌ Failed to retrieve latest reading")
    
    print()
    print("=" * 60)
    print("✅ Test completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()

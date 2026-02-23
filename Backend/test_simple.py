"""
Simple API Test Script - Check validation errors
"""

import requests
from datetime import datetime
import json

API_BASE_URL = "http://localhost:8000/api"

# Test data
reading = {
    "device_id": "tracker01",
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "servo_angle": 45.5,
    "temperature": 28.3,
    "humidity": 65.2,
    "lux": 5420.0,
    "voltage": 18.5,
    "current": 2.3,
    "power": 42.55,
    "fan_status": "auto",
    "status": "online"
}

print("=" * 60)
print("Testing API with sample reading")
print("=" * 60)
print("\nSending data:")
print(json.dumps(reading, indent=2))
print("\n" + "=" * 60)

try:
    response = requests.post(
        f"{API_BASE_URL}/readings",
        json=reading,
        timeout=5
    )
    
    print(f"\nStatus Code: {response.status_code}")
    print(f"Response: {json.dumps(response.json(), indent=2)}")
    
    if response.status_code == 201:
        print("\nSUCCESS! Reading stored successfully!")
    else:
        print(f"\nERROR: Failed to store reading")
        
except requests.exceptions.ConnectionError:
    print("\nERROR: Cannot connect to API. Is the server running?")
    print("Start server with: python -m app.main")
except Exception as e:
    print(f"\nERROR: {e}")

print("\n" + "=" * 60)

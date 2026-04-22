import requests
import json
from datetime import datetime

print("\n" + "="*60)
print("ML PREDICTION ENDPOINT TEST")
print("="*60)

# Test 1: Normal conditions
print("\n[TEST 1] Normal Conditions")
print("-" * 60)
payload1 = {
    'device_id': 'tracker01',
    'timestamp': datetime.utcnow().isoformat() + 'Z',
    'servo_angle': 45.5,
    'temperature': 28.3,
    'humidity': 65.2,
    'lux': 5420.0,
    'voltage': 18.5,
    'current': 2.3,
    'power': 42.55,
    'store_prediction': False
}

response1 = requests.post('http://127.0.0.1:8000/api/ml/predict', json=payload1)
if response1.status_code == 200:
    result1 = response1.json()
    print(f"✅ Status: {response1.status_code} OK")
    print(f"   Current Power: {result1['current_power']:.2f}W")
    print(f"   Predicted Power (15min): {result1['predicted_power_15min']:.2f}W")
    print(f"   Confidence: {result1['confidence']:.2%}")
    print(f"   Model: {result1['model_version']}")
else:
    print(f"❌ Status: {response1.status_code}")
    print(f"   Error: {response1.json()}")

# Test 2: High illumination (sunny)
print("\n[TEST 2] High Illumination (Sunny)")
print("-" * 60)
payload2 = {
    'device_id': 'tracker01',
    'timestamp': datetime.utcnow().isoformat() + 'Z',
    'servo_angle': 60.0,
    'temperature': 32.5,
    'humidity': 55.0,
    'lux': 78000.0,
    'voltage': 21.2,
    'current': 3.8,
    'power': 80.56,
    'store_prediction': False
}

response2 = requests.post('http://127.0.0.1:8000/api/ml/predict', json=payload2)
if response2.status_code == 200:
    result2 = response2.json()
    print(f"✅ Status: {response2.status_code} OK")
    print(f"   Current Power: {result2['current_power']:.2f}W")
    print(f"   Predicted Power (15min): {result2['predicted_power_15min']:.2f}W")
    print(f"   Confidence: {result2['confidence']:.2%}")
    print(f"   Model: {result2['model_version']}")
else:
    print(f"❌ Status: {response2.status_code}")
    print(f"   Error: {response2.json()}")

# Test 3: Low illumination (cloudy)
print("\n[TEST 3] Low Illumination (Cloudy)")
print("-" * 60)
payload3 = {
    'device_id': 'tracker01',
    'timestamp': datetime.utcnow().isoformat() + 'Z',
    'servo_angle': 45.0,
    'temperature': 22.0,
    'humidity': 75.0,
    'lux': 2100.0,
    'voltage': 15.8,
    'current': 0.9,
    'power': 14.22,
    'store_prediction': False
}

response3 = requests.post('http://127.0.0.1:8000/api/ml/predict', json=payload3)
if response3.status_code == 200:
    result3 = response3.json()
    print(f"✅ Status: {response3.status_code} OK")
    print(f"   Current Power: {result3['current_power']:.2f}W")
    print(f"   Predicted Power (15min): {result3['predicted_power_15min']:.2f}W")
    print(f"   Confidence: {result3['confidence']:.2%}")
    print(f"   Model: {result3['model_version']}")
else:
    print(f"❌ Status: {response3.status_code}")
    print(f"   Error: {response3.json()}")

print("\n" + "="*60)
print("TEST SUITE COMPLETE")
print("="*60 + "\n")

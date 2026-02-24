"""
Test ML API Endpoints

Tests the machine learning endpoints to verify they work correctly.
"""

import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000/api"
DEVICE_ID = "tracker01"


def test_ml_status():
    """Test ML model status endpoint"""
    print("\n" + "="*70)
    print("TEST 1: ML Model Status")
    print("="*70)
    
    try:
        response = requests.get(
            f"{BASE_URL}/ml/status",
            params={"device_id": DEVICE_ID},
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_ml_predict():
    """Test ML prediction endpoint"""
    print("\n" + "="*70)
    print("TEST 2: ML Prediction")
    print("="*70)
    
    # Sample reading (daytime with power generation)
    sample_reading = {
        "device_id": DEVICE_ID,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "servo_angle": 45.5,
        "temperature": 32.5,
        "humidity": 65.0,
        "lux": 45000.0,
        "voltage": 12.3,
        "current": 0.85,
        "power": 10.5,
        "fan_status": "on",
        "status": "online",
        "store_prediction": False
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/ml/predict",
            json=sample_reading,
            timeout=10
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"\n✅ Prediction: {data.get('predicted_power_15min', 'N/A'):.2f}W")
            print(f"   Confidence: {data.get('confidence', 0)*100:.1f}%")
            return True
        else:
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def test_ml_train():
    """Test ML training endpoint"""
    print("\n" + "="*70)
    print("TEST 3: ML Training (Optional - takes time)")
    print("="*70)
    
    train_request = {
        "device_id": DEVICE_ID,
        "days": 7,
        "model_type": "RandomForest"
    }
    
    try:
        print("Starting training request...")
        response = requests.post(
            f"{BASE_URL}/ml/train",
            json=train_request,
            timeout=120
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response:\n{json.dumps(response.json(), indent=2)}")
        
        return response.status_code == 200
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


if __name__ == "__main__":
    print("\n" + "="*70)
    print("SOLAR TRACKER ML API ENDPOINT TESTS")
    print("="*70)
    print(f"Base URL: {BASE_URL}")
    print(f"Device ID: {DEVICE_ID}")
    
    results = {}
    
    # Test 1: Status
    results['status'] = test_ml_status()
    
    # Test 2: Prediction
    results['predict'] = test_ml_predict()
    
    # Test 3: Training (optional - commented out by default)
    # results['train'] = test_ml_train()
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{test_name:20s}: {status}")
    
    print("="*70)
    
    all_passed = all(results.values())
    if all_passed:
        print("\n🎉 All tests passed! ML endpoints are working correctly.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")

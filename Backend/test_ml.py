"""
Test script for ML integration

This script tests the complete ML workflow:
1. Train a model with sample data
2. Make predictions
3. Check model status
"""

import requests
import time
from datetime import datetime, timedelta
import random

BASE_URL = "http://localhost:8000"
DEVICE_ID = "tracker01"


def generate_realistic_reading(timestamp: datetime, base_power=25.0) -> dict:
    """Generate a realistic solar reading based on time of day"""
    
    hour = timestamp.hour
    minute = timestamp.minute
    
    # Solar power curve (peaks at noon)
    if 6 <= hour <= 18:  # Daylight hours
        # Simulate sun intensity curve
        hour_from_noon = abs(12 - hour)
        sun_factor = 1 - (hour_from_noon / 6) ** 2
        
        # Add some randomness
        noise = random.uniform(-0.1, 0.1)
        power = base_power * sun_factor * (1 + noise)
        lux = 60000 * sun_factor * (1 + noise)
        
        # Temperature increases with sun
        temperature = 20 + (sun_factor * 15) + random.uniform(-2, 2)
    else:
        # Night time
        power = 0
        lux = 0
        temperature = 15 + random.uniform(-3, 3)
    
    # Calculate electrical values
    voltage = 12.5 + random.uniform(-0.5, 0.5)
    current = power / voltage if power > 0 else 0
    
    return {
        "device_id": DEVICE_ID,
        "timestamp": timestamp.isoformat() + "Z",
        "servo_angle": 45.0 + random.uniform(-10, 10),
        "temperature": round(temperature, 2),
        "humidity": 60 + random.uniform(-10, 10),
        "lux": round(lux, 2),
        "voltage": round(voltage, 2),
        "current": round(current, 3),
        "power": round(power, 2),
        "status": "online",
        "error_code": None
    }


def post_reading(reading: dict) -> bool:
    """Post a reading to the API"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/readings",
            json=reading,
            timeout=10
        )
        response.raise_for_status()
        return True
    except Exception as e:
        print(f"❌ Failed to post reading: {e}")
        return False


def train_model(days: int = 7, model_type: str = "RandomForest") -> dict:
    """Train the ML model"""
    print(f"\n📊 Training {model_type} model with {days} days of data...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/ml/train",
            json={
                "device_id": DEVICE_ID,
                "days": days,
                "model_type": model_type
            },
            timeout=120
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Training successful!")
        print(f"   - Samples used: {result.get('samples_used')}")
        print(f"   - Features: {len(result.get('features_used', []))}")
        
        metrics = result.get('metrics', {})
        if metrics:
            print(f"\n📈 Model Metrics:")
            print(f"   - MAE: {metrics.get('mae', 0):.3f}")
            print(f"   - RMSE: {metrics.get('rmse', 0):.3f}")
            print(f"   - R² Score: {metrics.get('r2', 0):.3f}")
            print(f"   - MAPE: {metrics.get('mape', 0):.3f}%")
        
        return result
    except Exception as e:
        print(f"❌ Training failed: {e}")
        return {}


def make_prediction(reading: dict, store: bool = True) -> dict:
    """Make a power prediction"""
    reading_copy = reading.copy()
    reading_copy["store_prediction"] = store
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/ml/predict",
            json=reading_copy,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"\n🔮 Prediction Results:")
        print(f"   - Current power: {reading['power']:.2f}W")
        print(f"   - Predicted power (15 min): {result.get('predicted_power_15min', 0):.2f}W")
        print(f"   - Confidence: {result.get('confidence', 0):.2%}")
        print(f"   - Model version: {result.get('model_version')}")
        
        return result
    except Exception as e:
        print(f"❌ Prediction failed: {e}")
        return {}


def check_model_status() -> dict:
    """Check model status"""
    print(f"\n📋 Checking model status...")
    
    try:
        response = requests.get(
            f"{BASE_URL}/api/ml/status",
            params={"device_id": DEVICE_ID},
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get('model_exists'):
            print(f"✅ Model exists for device: {DEVICE_ID}")
            print(f"   - Model type: {result.get('model_type')}")
            print(f"   - Trained at: {result.get('trained_at')}")
            print(f"   - Samples used: {result.get('samples_used')}")
        else:
            print(f"❌ No model found for device: {DEVICE_ID}")
        
        return result
    except Exception as e:
        print(f"❌ Status check failed: {e}")
        return {}


def test_reading_with_prediction(reading: dict) -> dict:
    """Test posting a reading with automatic prediction"""
    print(f"\n🔄 Testing reading ingestion with auto-prediction...")
    
    try:
        response = requests.post(
            f"{BASE_URL}/api/readings?predict=true",
            json=reading,
            timeout=10
        )
        response.raise_for_status()
        result = response.json()
        
        print(f"✅ Reading stored successfully")
        
        prediction = result.get('prediction')
        if prediction:
            print(f"🔮 Auto-prediction included:")
            print(f"   - Predicted power: {prediction.get('predicted_power_15min', 0):.2f}W")
            print(f"   - Confidence: {prediction.get('confidence', 0):.2%}")
        else:
            print(f"⚠️  No prediction available (model may not be trained)")
        
        return result
    except Exception as e:
        print(f"❌ Request failed: {e}")
        return {}


def main():
    """Main test workflow"""
    
    print("=" * 60)
    print("🌞 Solar Monitoring System - ML Integration Test")
    print("=" * 60)
    
    # Check if server is running
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server returned error")
            return
    except Exception as e:
        print(f"❌ Cannot connect to server: {e}")
        print("   Make sure the server is running: uvicorn app.main:app --reload")
        return
    
    # Check current model status
    status = check_model_status()
    
    # If no model, generate and post training data
    if not status.get('model_exists'):
        print("\n📝 No model found. Generating training data...")
        print("   (This will create 7 days of synthetic data)")
        
        # Generate 7 days of data (every 5 minutes = 288 readings/day)
        start_time = datetime.now() - timedelta(days=7)
        readings_count = 0
        
        print("\n⏳ Posting training data (this may take a moment)...")
        
        for day in range(7):
            for hour in range(24):
                for minute in [0, 15, 30, 45]:  # Every 15 minutes
                    timestamp = start_time + timedelta(days=day, hours=hour, minutes=minute)
                    reading = generate_realistic_reading(timestamp)
                    
                    if post_reading(reading):
                        readings_count += 1
                        if readings_count % 50 == 0:
                            print(f"   Posted {readings_count} readings...")
        
        print(f"✅ Posted {readings_count} training readings")
        
        # Train the model
        train_model(days=7, model_type="RandomForest")
    else:
        print(f"\n✅ Model already exists, skipping training data generation")
    
    # Generate a test reading for current time
    print("\n" + "=" * 60)
    print("🧪 Testing Predictions")
    print("=" * 60)
    
    current_reading = generate_realistic_reading(datetime.now(), base_power=30.0)
    
    # Test 1: Standalone prediction
    print("\n1️⃣  Test: Standalone Prediction API")
    make_prediction(current_reading, store=True)
    
    # Test 2: Reading with auto-prediction
    print("\n2️⃣  Test: Reading Ingestion with Auto-Prediction")
    future_reading = generate_realistic_reading(
        datetime.now() + timedelta(minutes=5),
        base_power=32.0
    )
    test_reading_with_prediction(future_reading)
    
    # Final status check
    print("\n" + "=" * 60)
    print("✅ All Tests Complete!")
    print("=" * 60)
    
    print("\n📚 Next Steps:")
    print("   1. View API docs: http://localhost:8000/docs")
    print("   2. Check predictions: GET /api/predictions/device/tracker01")
    print("   3. Train with real data: POST /api/ml/train")
    print("   4. Read guide: ML_INTEGRATION_GUIDE.md")


if __name__ == "__main__":
    main()

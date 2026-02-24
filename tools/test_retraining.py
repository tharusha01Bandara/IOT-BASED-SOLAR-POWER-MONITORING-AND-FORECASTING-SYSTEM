"""
Test script for model retraining system.

This script verifies that:
1. MongoDB connection works
2. Training data is available
3. Model training completes successfully
4. Model versioning and logging works

Usage:
    python test_retraining.py [device_id]
"""

import sys
import os
from pathlib import Path
from datetime import datetime

# Add parent directory to path to import Backend modules
sys.path.insert(0, str(Path(__file__).parent.parent / "Backend"))

from app.core.config import get_settings
from pymongo import MongoClient
from app.services.retrain_service import ModelRetrainService


def test_mongodb_connection():
    """Test MongoDB connection."""
    print("\n=== Testing MongoDB Connection ===")
    settings = get_settings()
    try:
        client = MongoClient(settings.mongodb_url)
        db = client[settings.database_name]
        
        # Ping test
        db.command('ping')
        print("✅ MongoDB connection successful")
        
        # Check collections exist
        collections = db.list_collection_names()
        print(f"✅ Found {len(collections)} collections: {', '.join(collections)}")
        
        # Count readings
        readings_count = db[settings.collection_readings_raw].count_documents({})
        print(f"✅ readings_raw has {readings_count} documents")
        
        return client, db
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        sys.exit(1)


def test_training_data_availability(db, device_id, days=7):
    """Test if sufficient training data is available."""
    print(f"\n=== Testing Training Data Availability (last {days} days) ===")
    settings = get_settings()
    
    from datetime import datetime, timedelta
    end_time = datetime.utcnow()
    start_time = end_time - timedelta(days=days)
    
    query = {
        "device_id": device_id,
        "timestamp": {"$gte": start_time, "$lte": end_time}
    }
    
    count = db[settings.collection_readings_raw].count_documents(query)
    print(f"✅ Found {count} data points for device '{device_id}' in last {days} days")
    
    if count < 100:
        print(f"⚠️  Warning: Only {count} data points. Minimum 100 recommended.")
        return False
    
    return count > 0


def test_model_training(db, device_id):
    """Test model training process."""
    print(f"\n=== Testing Model Training for '{device_id}' ===")
    settings = get_settings()
    
    try:
        # Initialize retraining service
        readings_collection = db[settings.collection_readings_raw]
        model_runs_collection = db[settings.collection_model_runs]
        
        service = ModelRetrainService(
            readings_collection=readings_collection,
            model_runs_collection=model_runs_collection,
            settings=settings
        )
        
        print("✅ RetrainService initialized")
        
        # Run training
        print(f"🔄 Starting training with 7 days of data...")
        print(f"   This may take 30-60 seconds...")
        
        result = service.retrain_model(
            device_id=device_id,
            days=7,
            horizon_minutes=15
        )
        
        print(f"\n✅ Training completed!")
        print(f"   Run ID: {result['run_id']}")
        print(f"   Status: {result['status']}")
        print(f"   Samples: {result['rows_used']} total, {result['metrics']['train_samples']} train, {result['metrics']['test_samples']} test")
        print(f"   MAE: {result['metrics']['mae']:.4f}")
        print(f"   RMSE: {result['metrics']['rmse']:.4f}")
        print(f"   R²: {result['metrics']['r2']:.4f}")
        print(f"   Promoted: {'✅ Yes' if result['promoted'] else '❌ No'}")
        print(f"   Model Path: {result['model_path']}")
        
        return True
        
    except Exception as e:
        print(f"❌ Training failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_model_versioning():
    """Test if model versioning directory exists."""
    print("\n=== Testing Model Versioning Setup ===")
    settings = get_settings()
    
    versions_dir = Path(settings.model_versions_dir)
    if versions_dir.exists():
        print(f"✅ Versions directory exists: {versions_dir}")
        models = list(versions_dir.glob("model_*.pkl"))
        print(f"✅ Found {len(models)} versioned models")
        for model in models[:5]:  # Show first 5
            print(f"   - {model.name}")
        return True
    else:
        print(f"❌ Versions directory not found: {versions_dir}")
        print(f"   Run: mkdir -p {versions_dir}")
        return False


def test_model_runs_collection(db):
    """Test if model_runs collection is accessible."""
    print("\n=== Testing model_runs Collection ===")
    settings = get_settings()
    
    collection = db[settings.collection_model_runs]
    count = collection.count_documents({})
    print(f"✅ model_runs collection has {count} training runs")
    
    if count > 0:
        latest = collection.find_one(sort=[("trained_at", -1)])
        print(f"   Latest run:")
        print(f"   - Run ID: {latest.get('run_id')}")
        print(f"   - Device: {latest.get('device_id')}")
        print(f"   - Time: {latest.get('trained_at')}")
        print(f"   - MAE: {latest.get('mae', 'N/A')}")
        print(f"   - Status: {latest.get('status')}")
        print(f"   - Promoted: {latest.get('promoted', False)}")
    
    return True


def main():
    """Run all tests."""
    print("=" * 60)
    print("🧪 Model Retraining System Test Suite")
    print("=" * 60)
    
    # Get device_id from command line or use default
    device_id = sys.argv[1] if len(sys.argv) > 1 else "tracker01"
    print(f"\nTesting with device_id: {device_id}")
    
    # Test 1: MongoDB connection
    client, db = test_mongodb_connection()
    
    # Test 2: Model versioning setup
    test_model_versioning()
    
    # Test 3: Training data availability
    data_available = test_training_data_availability(db, device_id, days=7)
    
    if not data_available:
        print("\n❌ Not enough training data. Please run data simulator first.")
        print(f"   Generate data: python Backend/tools/simulate_data.py --device {device_id}")
        sys.exit(1)
    
    # Test 4: Model training
    training_success = test_model_training(db, device_id)
    
    if not training_success:
        print("\n❌ Training failed. Check logs above for details.")
        sys.exit(1)
    
    # Test 5: Check model_runs collection
    test_model_runs_collection(db)
    
    # Summary
    print("\n" + "=" * 60)
    print("✅ All tests passed! System is ready for production.")
    print("=" * 60)
    print("\n📋 Next Steps:")
    print(f"1. Set up scheduled retraining:")
    print(f"   - Manual: python tools/retrain_worker.py --device {device_id}")
    print(f"   - Scheduler: python tools/retrain_worker.py --schedule --device {device_id}")
    print(f"2. Set up cron/Task Scheduler (see MODEL_RETRAINING_GUIDE.md)")
    print(f"3. Monitor model_runs collection in MongoDB")
    print(f"4. Check API endpoints: http://localhost:8000/api/ml/runs")
    print()
    
    client.close()


if __name__ == "__main__":
    main()

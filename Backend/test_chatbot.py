import requests
import json
from datetime import datetime, timedelta

BASE_URL = "http://localhost:8000"
DEVICE_ID = "DEVICE_001"

def test_chat_query():
    """Test main chat query endpoint"""
    payload = {
        "device_id": DEVICE_ID,
        "query": "What is the trend in power output over the last 6 hours?",
        "time_range": "6h"
    }
    response = requests.post(f"{BASE_URL}/api/chat/query", json=payload)
    print("📊 Chat Query Response:")
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 200, f"Expected 200, got {response.status_code}"

def test_explain_anomaly():
    """Test anomaly explanation"""
    timestamp = (datetime.utcnow() - timedelta(hours=1)).isoformat() + "Z"
    payload = {
        "device_id": DEVICE_ID,
        "timestamp": timestamp
    }
    response = requests.post(f"{BASE_URL}/api/chat/explain-anomaly", json=payload)
    print("\n⚠️ Anomaly Explanation Response:")
    print(json.dumps(response.json(), indent=2))
    assert response.status_code == 200

def test_suggested_questions():
    """Test suggested questions by persona"""
    personas = ["operator", "energy_manager", "maintenance_technician", "academic_evaluator"]
    for persona in personas:
        response = requests.get(
            f"{BASE_URL}/api/chat/suggested-questions",
            params={"persona": persona}
        )
        print(f"\n💡 Suggested Questions ({persona}):")
        print(json.dumps(response.json(), indent=2))
        assert response.status_code == 200

def test_error_handling():
    """Test error cases"""
    print("\n🔴 Testing Error Handling:")
    
    # Missing device_id
    response = requests.post(f"{BASE_URL}/api/chat/query", json={
        "query": "test",
        "time_range": "1h"
    })
    print(f"Missing device_id: {response.status_code}")
    
    # Invalid time_range
    response = requests.post(f"{BASE_URL}/api/chat/query", json={
        "device_id": DEVICE_ID,
        "query": "test",
        "time_range": "invalid"
    })
    print(f"Invalid time_range: {response.status_code}")

if __name__ == "__main__":
    try:
        test_chat_query()
        test_explain_anomaly()
        test_suggested_questions()
        test_error_handling()
        print("\n✅ All tests passed!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")

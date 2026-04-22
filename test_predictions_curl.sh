#!/bin/bash

# ML PREDICTION ENDPOINT - CURL TEST COLLECTION
# Copy and paste these commands to test different scenarios

# Configuration
BACKEND_URL="http://127.0.0.1:8000"
DEVICE_ID="tracker01"
TIMESTAMP=$(date -u +'%Y-%m-%dT%H:%M:%SZ')

echo "=================================="
echo "ML PREDICTION ENDPOINT TEST SUITE"
echo "=================================="
echo "Backend URL: $BACKEND_URL"
echo "Device ID: $DEVICE_ID"
echo ""

# ============================================================================
# TEST 1: Optimal Sunny Day
# ============================================================================
echo "[TEST 1] Optimal Sunny Day (Peak conditions)"
echo "-------------------------------------------"
curl -X POST "$BACKEND_URL/api/ml/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "'$DEVICE_ID'",
    "timestamp": "'$TIMESTAMP'",
    "servo_angle": 50.0,
    "temperature": 35.0,
    "humidity": 40.0,
    "lux": 95000.0,
    "voltage": 22.5,
    "current": 4.2,
    "power": 94.5,
    "store_prediction": true
  }' | jq '.'
echo ""
echo ""

# ============================================================================
# TEST 2: Partial Clouds
# ============================================================================
echo "[TEST 2] Partial Clouds (50% cloud cover)"
echo "-------------------------------------------"
curl -X POST "$BACKEND_URL/api/ml/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "'$DEVICE_ID'",
    "timestamp": "'$TIMESTAMP'",
    "servo_angle": 45.0,
    "temperature": 28.0,
    "humidity": 60.0,
    "lux": 42000.0,
    "voltage": 19.2,
    "current": 2.8,
    "power": 53.76,
    "store_prediction": true
  }' | jq '.'
echo ""
echo ""

# ============================================================================
# TEST 3: Overcast Day
# ============================================================================
echo "[TEST 3] Overcast Day (Heavy clouds)"
echo "-------------------------------------------"
curl -X POST "$BACKEND_URL/api/ml/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "'$DEVICE_ID'",
    "timestamp": "'$TIMESTAMP'",
    "servo_angle": 45.0,
    "temperature": 20.0,
    "humidity": 85.0,
    "lux": 8500.0,
    "voltage": 14.5,
    "current": 0.6,
    "power": 8.7,
    "store_prediction": true
  }' | jq '.'
echo ""
echo ""

# ============================================================================
# TEST 4: Sunset/Low angle
# ============================================================================
echo "[TEST 4] Sunset (Low sun angle)"
echo "-------------------------------------------"
curl -X POST "$BACKEND_URL/api/ml/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "'$DEVICE_ID'",
    "timestamp": "'$TIMESTAMP'",
    "servo_angle": 10.0,
    "temperature": 18.0,
    "humidity": 65.0,
    "lux": 3200.0,
    "voltage": 12.5,
    "current": 0.3,
    "power": 3.75,
    "store_prediction": false
  }' | jq '.'
echo ""
echo ""

# ============================================================================
# TEST 5: Night (No sunlight)
# ============================================================================
echo "[TEST 5] Night (No solar activity)"
echo "-------------------------------------------"
curl -X POST "$BACKEND_URL/api/ml/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "'$DEVICE_ID'",
    "timestamp": "'$TIMESTAMP'",
    "servo_angle": 45.0,
    "temperature": 15.0,
    "humidity": 75.0,
    "lux": 0.0,
    "voltage": 0.0,
    "current": 0.0,
    "power": 0.0,
    "store_prediction": false
  }' | jq '.'
echo ""
echo ""

# ============================================================================
# TEST 6: Heat Stress
# ============================================================================
echo "[TEST 6] Heat Stress (48°C temperature)"
echo "-------------------------------------------"
curl -X POST "$BACKEND_URL/api/ml/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "'$DEVICE_ID'",
    "timestamp": "'$TIMESTAMP'",
    "servo_angle": 55.0,
    "temperature": 48.0,
    "humidity": 20.0,
    "lux": 88000.0,
    "voltage": 20.5,
    "current": 3.5,
    "power": 71.75,
    "store_prediction": true
  }' | jq '.'
echo ""
echo ""

# ============================================================================
# TEST 7: Cold Conditions
# ============================================================================
echo "[TEST 7] Cold Conditions (5°C temperature)"
echo "-------------------------------------------"
curl -X POST "$BACKEND_URL/api/ml/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "'$DEVICE_ID'",
    "timestamp": "'$TIMESTAMP'",
    "servo_angle": 30.0,
    "temperature": 5.0,
    "humidity": 55.0,
    "lux": 45000.0,
    "voltage": 22.8,
    "current": 3.9,
    "power": 88.92,
    "store_prediction": true
  }' | jq '.'
echo ""
echo ""

# ============================================================================
# TEST 8: Misaligned Panel
# ============================================================================
echo "[TEST 8] Misaligned Panel (Poor servo angle)"
echo "-------------------------------------------"
curl -X POST "$BACKEND_URL/api/ml/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "'$DEVICE_ID'",
    "timestamp": "'$TIMESTAMP'",
    "servo_angle": 15.0,
    "temperature": 32.0,
    "humidity": 45.0,
    "lux": 82000.0,
    "voltage": 18.5,
    "current": 1.8,
    "power": 33.3,
    "store_prediction": true
  }' | jq '.'
echo ""
echo ""

# ============================================================================
# TEST 9: High Humidity
# ============================================================================
echo "[TEST 9] High Humidity (90% humidity)"
echo "-------------------------------------------"
curl -X POST "$BACKEND_URL/api/ml/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "'$DEVICE_ID'",
    "timestamp": "'$TIMESTAMP'",
    "servo_angle": 40.0,
    "temperature": 22.0,
    "humidity": 90.0,
    "lux": 65000.0,
    "voltage": 20.2,
    "current": 3.0,
    "power": 60.6,
    "store_prediction": true
  }' | jq '.'
echo ""
echo ""

# ============================================================================
# TEST 10: Invalid Request (Missing field) - Should fail
# ============================================================================
echo "[TEST 10] Invalid Request (Missing servo_angle - should fail)"
echo "-------------------------------------------"
curl -X POST "$BACKEND_URL/api/ml/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "'$DEVICE_ID'",
    "timestamp": "'$TIMESTAMP'",
    "temperature": 28.0,
    "humidity": 60.0,
    "lux": 75000.0,
    "voltage": 21.0,
    "current": 3.5,
    "power": 73.5,
    "store_prediction": false
  }' | jq '.'
echo ""
echo ""

# ============================================================================
# TEST 11: Invalid Device - Should fail with 404
# ============================================================================
echo "[TEST 11] Non-existent Device (Should fail with 404)"
echo "-------------------------------------------"
curl -X POST "$BACKEND_URL/api/ml/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "tracker99",
    "timestamp": "'$TIMESTAMP'",
    "servo_angle": 45.0,
    "temperature": 28.0,
    "humidity": 60.0,
    "lux": 75000.0,
    "voltage": 21.0,
    "current": 3.5,
    "power": 73.5,
    "store_prediction": false
  }' | jq '.'
echo ""
echo ""

# ============================================================================
# TEST 12: Out of Range Value - Should fail
# ============================================================================
echo "[TEST 12] Out of Range (servo_angle > 180 - should fail)"
echo "-------------------------------------------"
curl -X POST "$BACKEND_URL/api/ml/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "'$DEVICE_ID'",
    "timestamp": "'$TIMESTAMP'",
    "servo_angle": 185.0,
    "temperature": 28.0,
    "humidity": 60.0,
    "lux": 75000.0,
    "voltage": 21.0,
    "current": 3.5,
    "power": 73.5,
    "store_prediction": false
  }' | jq '.'
echo ""
echo ""

echo "=================================="
echo "TEST SUITE COMPLETE"
echo "=================================="

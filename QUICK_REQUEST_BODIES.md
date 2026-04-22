/**
 * QUICK COPY-PASTE REQUEST BODIES
 * 
 * Use these request bodies directly in Postman, curl, or browser console
 * Just copy and paste!
 */

// ============================================================================
// BASIC TEMPLATE (Sunny Day)
// ============================================================================

{
  "device_id": "tracker01",
  "timestamp": "2026-04-22T12:00:00Z",
  "servo_angle": 45.0,
  "temperature": 28.0,
  "humidity": 60.0,
  "lux": 75000.0,
  "voltage": 21.0,
  "current": 3.5,
  "power": 73.5,
  "store_prediction": false
}

// ============================================================================
// HIGH POWER OUTPUT (Peak conditions)
// ============================================================================

{
  "device_id": "tracker01",
  "timestamp": "2026-04-22T12:00:00Z",
  "servo_angle": 50.0,
  "temperature": 35.0,
  "humidity": 40.0,
  "lux": 95000.0,
  "voltage": 22.5,
  "current": 4.2,
  "power": 94.5,
  "store_prediction": true
}

// ============================================================================
// LOW POWER OUTPUT (Cloudy)
// ============================================================================

{
  "device_id": "tracker01",
  "timestamp": "2026-04-22T10:30:00Z",
  "servo_angle": 45.0,
  "temperature": 20.0,
  "humidity": 85.0,
  "lux": 8500.0,
  "voltage": 14.5,
  "current": 0.6,
  "power": 8.7,
  "store_prediction": true
}

// ============================================================================
// NO POWER (Night time)
// ============================================================================

{
  "device_id": "tracker01",
  "timestamp": "2026-04-22T22:00:00Z",
  "servo_angle": 45.0,
  "temperature": 15.0,
  "humidity": 75.0,
  "lux": 0.0,
  "voltage": 0.0,
  "current": 0.0,
  "power": 0.0,
  "store_prediction": false
}

// ============================================================================
// EXTREME HEAT (Temperature stress)
// ============================================================================

{
  "device_id": "tracker01",
  "timestamp": "2026-04-22T14:00:00Z",
  "servo_angle": 55.0,
  "temperature": 48.0,
  "humidity": 20.0,
  "lux": 88000.0,
  "voltage": 20.5,
  "current": 3.5,
  "power": 71.75,
  "store_prediction": true
}

// ============================================================================
// EXTREME COLD (Temperature boost)
// ============================================================================

{
  "device_id": "tracker01",
  "timestamp": "2026-04-22T06:30:00Z",
  "servo_angle": 30.0,
  "temperature": 5.0,
  "humidity": 55.0,
  "lux": 45000.0,
  "voltage": 22.8,
  "current": 3.9,
  "power": 88.92,
  "store_prediction": true
}

// ============================================================================
// MISALIGNED PANEL (Poor servo angle)
// ============================================================================

{
  "device_id": "tracker01",
  "timestamp": "2026-04-22T12:00:00Z",
  "servo_angle": 15.0,
  "temperature": 32.0,
  "humidity": 45.0,
  "lux": 82000.0,
  "voltage": 18.5,
  "current": 1.8,
  "power": 33.3,
  "store_prediction": true
}

// ============================================================================
// PARTIAL CLOUDS
// ============================================================================

{
  "device_id": "tracker01",
  "timestamp": "2026-04-22T11:45:00Z",
  "servo_angle": 45.0,
  "temperature": 28.0,
  "humidity": 60.0,
  "lux": 42000.0,
  "voltage": 19.2,
  "current": 2.8,
  "power": 53.76,
  "store_prediction": true
}

// ============================================================================
// SUNSET (Low angle sun)
// ============================================================================

{
  "device_id": "tracker01",
  "timestamp": "2026-04-22T18:30:00Z",
  "servo_angle": 10.0,
  "temperature": 18.0,
  "humidity": 65.0,
  "lux": 3200.0,
  "voltage": 12.5,
  "current": 0.3,
  "power": 3.75,
  "store_prediction": false
}

// ============================================================================
// HIGH HUMIDITY
// ============================================================================

{
  "device_id": "tracker01",
  "timestamp": "2026-04-22T08:00:00Z",
  "servo_angle": 40.0,
  "temperature": 22.0,
  "humidity": 90.0,
  "lux": 65000.0,
  "voltage": 20.2,
  "current": 3.0,
  "power": 60.6,
  "store_prediction": true
}

// ============================================================================
// DIFFERENT DEVICE (tracker02 - if model exists)
// ============================================================================

{
  "device_id": "tracker02",
  "timestamp": "2026-04-22T12:00:00Z",
  "servo_angle": 45.0,
  "temperature": 28.0,
  "humidity": 60.0,
  "lux": 75000.0,
  "voltage": 21.0,
  "current": 3.5,
  "power": 73.5,
  "store_prediction": false
}

// ============================================================================
// ERROR TESTS - These should fail with appropriate errors
// ============================================================================

// ERROR 1: Missing servo_angle (should return 400)
{
  "device_id": "tracker01",
  "timestamp": "2026-04-22T12:00:00Z",
  "temperature": 28.0,
  "humidity": 60.0,
  "lux": 75000.0,
  "voltage": 21.0,
  "current": 3.5,
  "power": 73.5,
  "store_prediction": false
}

// ERROR 2: servo_angle > 180 (should return 400)
{
  "device_id": "tracker01",
  "timestamp": "2026-04-22T12:00:00Z",
  "servo_angle": 185.0,
  "temperature": 28.0,
  "humidity": 60.0,
  "lux": 75000.0,
  "voltage": 21.0,
  "current": 3.5,
  "power": 73.5,
  "store_prediction": false
}

// ERROR 3: Invalid device_id (should return 404)
{
  "device_id": "tracker99",
  "timestamp": "2026-04-22T12:00:00Z",
  "servo_angle": 45.0,
  "temperature": 28.0,
  "humidity": 60.0,
  "lux": 75000.0,
  "voltage": 21.0,
  "current": 3.5,
  "power": 73.5,
  "store_prediction": false
}

// ERROR 4: Negative humidity (should return 400)
{
  "device_id": "tracker01",
  "timestamp": "2026-04-22T12:00:00Z",
  "servo_angle": 45.0,
  "temperature": 28.0,
  "humidity": -10.0,
  "lux": 75000.0,
  "voltage": 21.0,
  "current": 3.5,
  "power": 73.5,
  "store_prediction": false
}

// ============================================================================
// HOW TO TEST IN BROWSER CONSOLE
// ============================================================================

/*
STEP 1: Open Browser Console (F12 -> Console tab)

STEP 2: Paste this command:

fetch('http://127.0.0.1:8000/api/ml/predict', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    "device_id": "tracker01",
    "timestamp": "2026-04-22T12:00:00Z",
    "servo_angle": 45.0,
    "temperature": 28.0,
    "humidity": 60.0,
    "lux": 75000.0,
    "voltage": 21.0,
    "current": 3.5,
    "power": 73.5,
    "store_prediction": false
  })
}).then(r => r.json()).then(d => console.log(JSON.stringify(d, null, 2)))

STEP 3: Press Enter

STEP 4: See the response in console (scroll if needed)

Expected response:
{
  "success": true,
  "device_id": "tracker01",
  "current_power": 73.5,
  "predicted_power_15min": 0.274,
  "confidence": 0.998,
  "model_version": "1776819378",
  "predicted_at": "2026-04-22T12:00:15.123456"
}
*/

// ============================================================================
// HOW TO TEST WITH CURL
// ============================================================================

/*
COMMAND:

curl -X POST http://127.0.0.1:8000/api/ml/predict \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "tracker01",
    "timestamp": "2026-04-22T12:00:00Z",
    "servo_angle": 45.0,
    "temperature": 28.0,
    "humidity": 60.0,
    "lux": 75000.0,
    "voltage": 21.0,
    "current": 3.5,
    "power": 73.5,
    "store_prediction": false
  }' | jq '.'
*/

// ============================================================================
// UNDERSTANDING THE PARAMETERS
// ============================================================================

/*
device_id        (string):  Device identifier (e.g., "tracker01")
timestamp        (string):  ISO 8601 datetime (e.g., "2026-04-22T12:00:00Z")
servo_angle      (float):   Panel angle 0-180 degrees
temperature      (float):   Ambient temperature in °C (-50 to 100)
humidity         (float):   Relative humidity 0-100 %
lux              (float):   Light intensity in lux (0+)
voltage          (float):   Panel voltage in volts (0+)
current          (float):   Panel current in amps (0+)
power            (float):   Panel power output in watts (0+)
store_prediction (boolean): Save prediction to database (true/false)

TYPICAL VALUE RANGES:
- servo_angle:   0-90 (facing sun), up to 180 when tracking
- temperature:   -10 to 50 (realistic outdoor range)
- humidity:      20-90 (typical outdoor)
- lux:           0 (night) to 100,000 (direct sunlight)
- voltage:       0 (night) to 24 (peak output)
- current:       0 (night) to 5 (peak output)
- power:         0 (night) to 100 (peak output for 2W panel scaled)
*/

// ============================================================================
// RESPONSE INTERPRETATION
// ============================================================================

/*
SUCCESS (200 OK):
{
  "success": true,
  "device_id": "tracker01",
  "current_power": 73.5,               // Input power
  "predicted_power_15min": 0.274,      // Predicted power in 15 minutes
  "confidence": 0.998,                 // Confidence score (0-1)
  "model_version": "1776819378",       // Model that made prediction
  "predicted_at": "2026-04-22T..."     // When prediction was made
}

NOT FOUND (404):
{
  "success": false,
  "error": "ModelNotFound",
  "message": "No trained model found for device: tracker99"
}

VALIDATION ERROR (400):
{
  "detail": [
    {
      "type": "value_error",
      "loc": ["body", "servo_angle"],
      "msg": "Input should be less than or equal to 180",
      "input": 185.0
    }
  ]
}

SERVER ERROR (500):
{
  "success": false,
  "error": "InternalError",
  "message": "An unexpected error occurred"
}
*/

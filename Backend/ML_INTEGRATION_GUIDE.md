# Machine Learning Integration Guide

## Overview

The Solar Monitoring System includes **production-ready Machine Learning capabilities** to predict solar panel power output 15 minutes ahead. This enables:

- Proactive power management
- Grid integration planning
- Anomaly detection
- Performance optimization

## Architecture

### Components

1. **ML Service** (`app/services/ml_service.py`)
   - Data loading from MongoDB
   - Feature engineering (time + trend features)
   - Model training with time-based split
   - Prediction with confidence scoring
   - Model persistence

2. **ML Router** (`app/routers/ml.py`)
   - POST `/api/ml/train` - Train model
   - POST `/api/ml/predict` - Make predictions
   - GET `/api/ml/status` - Check model status
   - DELETE `/api/ml/model` - Delete model

3. **ML Schemas** (`app/schemas/ml.py`)
   - Request/response validation
   - Type safety with Pydantic

## Features

### Engineered Features

#### Base Features (from sensor readings)
- `temperature` - Temperature in Celsius
- `humidity` - Humidity percentage
- `lux` - Light intensity
- `voltage` - Battery voltage
- `current` - Battery current
- `power` - Current power output

#### Time Features (auto-generated)
- `hour` - Hour of day (0-23)
- `minute` - Minute of hour (0-59)
- `day_of_week` - Day of week (0-6)

#### Trend Features (computed)
- `power_diff` - Power change from previous reading
- `lux_diff` - Light intensity change
- `rolling_mean_power` - 5-reading rolling average of power

### Supported Models

1. **RandomForest** (default, recommended)
   - Handles non-linear relationships
   - Robust to outliers
   - No feature scaling required
   - Best for complex patterns

2. **LinearRegression**
   - Fast training and prediction
   - Interpretable coefficients
   - Good for linear trends

## Quick Start

### 1. Install Dependencies

Ensure all ML packages are installed:

```bash
pip install -r requirements.txt
```

Required packages:
- scikit-learn==1.4.0
- pandas==2.2.0
- numpy==1.26.3
- joblib==1.3.2

### 2. Collect Training Data

Collect at least **100 readings** (preferably 7+ days) before training:

```bash
# POST readings to the API
curl -X POST "http://localhost:8000/api/readings" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "tracker01",
    "timestamp": "2025-01-08T10:00:00Z",
    "servo_angle": 45.5,
    "temperature": 28.3,
    "humidity": 65.2,
    "lux": 45000,
    "voltage": 12.5,
    "current": 2.3,
    "power": 28.75,
    "status": "online",
    "error_code": null
  }'
```

### 3. Train Model

Train a model using 7 days of historical data:

```bash
curl -X POST "http://localhost:8000/api/ml/train" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "tracker01",
    "days": 7,
    "model_type": "RandomForest"
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Model trained successfully",
  "device_id": "tracker01",
  "model_type": "RandomForest",
  "samples_used": 2016,
  "features_used": [
    "temperature", "humidity", "lux", "voltage", 
    "current", "power", "hour", "minute", 
    "day_of_week", "power_diff", "lux_diff", 
    "rolling_mean_power"
  ],
  "metrics": {
    "mae": 2.45,
    "mse": 8.32,
    "rmse": 2.88,
    "r2": 0.94,
    "mape": 3.21
  },
  "trained_at": "2025-01-08T12:00:00Z",
  "model_version": "RandomForest_v1_20250108"
}
```

### 4. Make Predictions

#### Option A: Standalone Prediction

```bash
curl -X POST "http://localhost:8000/api/ml/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "tracker01",
    "timestamp": "2025-01-08T14:00:00Z",
    "servo_angle": 45.5,
    "temperature": 28.3,
    "humidity": 65.2,
    "lux": 45000,
    "voltage": 12.5,
    "current": 2.3,
    "power": 28.75,
    "status": "online",
    "store_prediction": true
  }'
```

**Response:**
```json
{
  "success": true,
  "device_id": "tracker01",
  "predicted_power_15min": 30.25,
  "confidence": 0.92,
  "predicted_at": "2025-01-08T14:15:00Z",
  "model_version": "RandomForest_v1_20250108",
  "prediction_stored": true
}
```

#### Option B: Auto-Prediction on Data Ingestion

Enable automatic predictions when posting readings:

```bash
curl -X POST "http://localhost:8000/api/readings?predict=true" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "tracker01",
    "timestamp": "2025-01-08T14:00:00Z",
    "servo_angle": 45.5,
    "temperature": 28.3,
    "humidity": 65.2,
    "lux": 45000,
    "voltage": 12.5,
    "current": 2.3,
    "power": 28.75,
    "status": "online",
    "error_code": null
  }'
```

**Response includes prediction:**
```json
{
  "success": true,
  "message": "Reading stored successfully with prediction: 30.25W",
  "device_id": "tracker01",
  "timestamp": "2025-01-08T14:00:00Z",
  "inserted_id": "699c796dde15ec1e5c6c7797",
  "prediction": {
    "predicted_power_15min": 30.25,
    "confidence": 0.92,
    "model_version": "RandomForest_v1_20250108"
  }
}
```

### 5. Check Model Status

```bash
curl -X GET "http://localhost:8000/api/ml/status?device_id=tracker01"
```

**Response:**
```json
{
  "model_exists": true,
  "device_id": "tracker01",
  "model_type": "RandomForest",
  "trained_at": "2025-01-08T12:00:00Z",
  "model_version": "RandomForest_v1_20250108",
  "samples_used": 2016,
  "features": [
    "temperature", "humidity", "lux", "voltage",
    "current", "power", "hour", "minute",
    "day_of_week", "power_diff", "lux_diff",
    "rolling_mean_power"
  ],
  "metrics": {
    "mae": 2.45,
    "mse": 8.32,
    "rmse": 2.88,
    "r2": 0.94,
    "mape": 3.21
  }
}
```

## API Reference

### POST /api/ml/train

Train an ML model for power forecasting.

**Request Body:**
```json
{
  "device_id": "tracker01",     // Required: Device identifier
  "days": 7,                     // Optional: Days of data (default: 7)
  "model_type": "RandomForest"   // Optional: "RandomForest" or "LinearRegression"
}
```

**Responses:**
- `200 OK` - Training started/completed
- `400 Bad Request` - Insufficient data or invalid parameters
- `500 Internal Server Error` - Training failed

**Notes:**
- Requires at least 100 readings
- For >5000 readings, trains in background
- Model saved to `app/ml_models/{device_id}_model.pkl`

### POST /api/ml/predict

Predict power output 15 minutes ahead.

**Request Body:**
```json
{
  "device_id": "tracker01",
  "timestamp": "2025-01-08T14:00:00Z",
  "servo_angle": 45.5,
  "temperature": 28.3,
  "humidity": 65.2,
  "lux": 45000,
  "voltage": 12.5,
  "current": 2.3,
  "power": 28.75,
  "status": "online",
  "store_prediction": true  // Optional: Store prediction in DB
}
```

**Responses:**
- `200 OK` - Prediction successful
- `404 Not Found` - Model not trained
- `500 Internal Server Error` - Prediction failed

### GET /api/ml/status

Get model information and metrics.

**Query Parameters:**
- `device_id` (required): Device identifier

**Responses:**
- `200 OK` - Model status returned
- `500 Internal Server Error` - Failed to get status

### DELETE /api/ml/model

Delete trained model files.

**Query Parameters:**
- `device_id` (required): Device identifier

**Responses:**
- `200 OK` - Model deleted
- `404 Not Found` - Model doesn't exist
- `500 Internal Server Error` - Deletion failed

## Performance

### Model Metrics

The system evaluates models using:

1. **MAE (Mean Absolute Error)** - Average prediction error in watts
   - Lower is better
   - Typical: 2-5W for well-trained models

2. **RMSE (Root Mean Squared Error)** - Penalizes large errors
   - Lower is better
   - Typical: 3-6W

3. **R² Score** - Proportion of variance explained
   - Range: 0-1 (1 = perfect)
   - Typical: 0.85-0.95 for good models

4. **MAPE (Mean Absolute Percentage Error)** - Percentage error
   - Lower is better
   - Typical: 3-8%

### Confidence Scoring

Confidence is calculated as:
```
confidence = max(0, 1 - (MAE / mean_power))
```

High confidence (>0.9): Very reliable prediction
Medium confidence (0.7-0.9): Good prediction
Low confidence (<0.7): Use with caution

## Best Practices

### Training

1. **Data Collection**
   - Collect at least 7 days of data
   - Ensure data covers different weather conditions
   - Include entire day cycle (sunrise to sunset)

2. **Retraining**
   - Retrain weekly for seasonal changes
   - Retrain after panel maintenance
   - Retrain if R² score drops below 0.8

3. **Model Selection**
   - Use RandomForest for production (better accuracy)
   - Use LinearRegression for faster inference

### Predictions

1. **Validation**
   - Check confidence score before using prediction
   - Discard predictions with confidence < 0.5
   - Monitor actual vs predicted for drift detection

2. **Storage**
   - Set `store_prediction=true` for analysis
   - Compare predictions with actual readings
   - Build metrics dashboard

3. **Integration**
   - Use `predict=true` query param for automatic predictions
   - Implement fallback logic for model unavailability
   - Cache predictions to reduce computation

## Monitoring

### Check Prediction Accuracy

Query stored predictions and compare with actual readings:

```bash
curl -X GET "http://localhost:8000/api/predictions/device/tracker01?hours=24"
```

### Model Drift Detection

Monitor these indicators:
- R² score decreasing over time
- MAE increasing
- Confidence scores dropping
- Large prediction errors

**Action:** Retrain model with recent data

## Troubleshooting

### Issue: "InsufficientData" Error

**Cause:** Not enough readings for training

**Solution:**
```bash
# Check data count
curl -X GET "http://localhost:8000/api/readings/history?device_id=tracker01&hours=168"

# Ensure at least 100 readings exist
```

### Issue: "ModelNotFound" Error

**Cause:** Model not trained yet

**Solution:**
```bash
# Train model first
curl -X POST "http://localhost:8000/api/ml/train" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "tracker01", "days": 7}'
```

### Issue: Low R² Score (<0.7)

**Possible Causes:**
1. Insufficient training data
2. Noisy sensor data
3. Extreme weather events
4. Hardware issues

**Solutions:**
- Collect more data
- Check sensor calibration
- Increase training days
- Use RandomForest instead of LinearRegression

### Issue: High Prediction Errors

**Solutions:**
1. Retrain with more recent data
2. Increase training window (days parameter)
3. Verify sensor accuracy
4. Check for system changes (panel angle, shading, etc.)

## File Structure

```
app/
├── ml_models/                    # Model storage (auto-created)
│   ├── tracker01_model.pkl       # Trained model file
│   └── tracker01_model_meta.json # Model metadata
├── services/
│   └── ml_service.py             # ML business logic
├── routers/
│   └── ml.py                     # ML API endpoints
└── schemas/
    └── ml.py                     # ML request/response schemas
```

## Example Workflow

### Complete Setup and Usage

```bash
# 1. Start the server
uvicorn app.main:app --reload

# 2. Verify health
curl http://localhost:8000/health

# 3. Post training data (repeat for 7 days)
for i in {1..2000}; do
  curl -X POST "http://localhost:8000/api/readings" \
    -H "Content-Type: application/json" \
    -d '{...sensor data...}'
  sleep 300  # Every 5 minutes
done

# 4. Train model
curl -X POST "http://localhost:8000/api/ml/train" \
  -H "Content-Type: application/json" \
  -d '{"device_id": "tracker01", "days": 7}'

# 5. Check status
curl http://localhost:8000/api/ml/status?device_id=tracker01

# 6. Enable auto-predictions
# Add ?predict=true to reading endpoint

# 7. Monitor predictions
curl http://localhost:8000/api/predictions/device/tracker01
```

## Production Considerations

### Scalability

- **Multiple Devices**: Each device has its own model
- **Background Training**: Large datasets train asynchronously
- **Model Caching**: Models loaded once and reused
- **Prediction Throughput**: ~1000 predictions/second

### Security

- Input validation with Pydantic
- Model file isolation
- Error handling without data leakage
- Logging for audit trails

### Reliability

- Graceful degradation if model unavailable
- Prediction failures don't block data ingestion
- Model versioning for rollback
- Health checks include ML status

## References

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [scikit-learn User Guide](https://scikit-learn.org/stable/user_guide.html)
- [Time Series Forecasting Best Practices](https://scikit-learn.org/stable/modules/cross_validation.html#time-series-split)

## Support

For issues or questions:
1. Check logs: `app/logs/`
2. Review metrics: GET `/api/ml/status`
3. Retrain model if needed
4. Verify sensor data quality

---

**Version:** 1.0.0  
**Last Updated:** 2025-01-08  
**Status:** Production Ready ✅

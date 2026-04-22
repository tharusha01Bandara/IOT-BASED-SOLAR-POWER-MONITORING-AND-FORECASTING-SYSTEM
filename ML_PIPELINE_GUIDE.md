# Complete ML Pipeline Guide: Data Generation to Model Integration

## Overview

This guide walks you through the complete ML workflow for your Solar Tracker project from raw data generation to production model inference. The pipeline consists of 5 major stages:

```
Stage 1: Data Generation → Stage 2: Data Building → Stage 3: Feature Engineering → 
Stage 4: Model Training → Stage 5: Integration & Inference
```

---

## STAGE 1: DATA GENERATION (Simulator)

### Purpose
Generate realistic solar tracker sensor data that mimics real ESP32 device readings to populate your MongoDB database.

### Files Involved
- `tools/simulate_solar_final.py` - Main simulator script

### Data Format Generated
```json
{
  "device_id": "tracker01",
  "timestamp": "2026-04-21T12:30:45.123Z",
  "servo_angle": 90.0,
  "temperature": 32.4,
  "humidity": 65.2,
  "lux": 52300.45,
  "ldr_left": 2200,
  "ldr_right": 2000,
  "voltage": 6.0,
  "current": 0.22,
  "power": 1.32,
  "fan_status": "ON",
  "status": "ok"
}
```

### Key Features of Current Simulator
- **Real Climate Modeling**: Sri Lankan tropical climate (06:00-18:00 daylight)
- **Temperature Range**: 24-27°C (night), 30-36°C (day)
- **Humidity**: 60-90% (realistic tropical levels)
- **Weather Modes**: `clear`, `partly_cloudy`, `monsoon`
- **Servo Tracking**: East-West single-axis tracking (30-160°)
- **Fan Logic**: Turns ON at 40°C, OFF at 38°C (hysteresis)
- **LDR Values**: Simulated but NOT used in current ML (kept for device compatibility)
- **Lux**: From BH1750 sensor simulation (primary light sensor for ML)

### How to Run

#### Quick Start (1 day clear weather)
```bash
cd e:\Solar Tracker
python tools/simulate_solar_final.py --days 1 --mode clear --interval_sec 10
```

#### Generate Multiple Days
```bash
# 7 days of partly cloudy data
python tools/simulate_solar_final.py --days 7 --mode partly_cloudy --interval_sec 10

# 14 days of monsoon data (more clouds = harder training data)
python tools/simulate_solar_final.py --days 14 --mode monsoon --interval_sec 30
```

#### Custom Parameters
```bash
python tools/simulate_solar_final.py \
  --device_id tracker01 \
  --days 3 \
  --mode clear \
  --interval_sec 5 \
  --base_url http://localhost:8000
```

### What Happens During Simulation
1. **Connects to FastAPI Backend**: `/api/readings` endpoint
2. **Generates Reading Every N Seconds**: With realistic values
3. **Sends JSON POST**: To backend for storage in MongoDB
4. **Logs Progress**: Shows success rate and any errors
5. **Stores in MongoDB**: `solar_db.readings_raw` collection

### Data Volume Recommendations
- **Quick Testing**: 1 day (1,440 readings at 10-sec intervals)
- **Model Training**: 7-14 days (10,080-20,160 readings)
- **High Accuracy**: 30+ days of diverse weather

---

## STAGE 2: DATASET BUILDING

### Purpose
Extract raw sensor readings from MongoDB and transform them into a labeled ML dataset with features and target variables.

### Files Involved
- `tools/build_dataset.py` - Dataset creation script
- `tools/requirements_dataset.txt` - Dependencies

### Input
- MongoDB readings collection (from Stage 1)
- Device ID filter
- Time window (days)

### Output
- `data/solar_dataset.csv` - Training-ready dataset
- `data/dataset_report.json` - Data quality report

### Pipeline Steps

#### Step 1: Data Fetching
```python
# Query MongoDB for device readings
query = {
    "device_id": "tracker01",
    "timestamp": {"$gte": start_time, "$lte": end_time},
    "status": "online"  # Only valid readings
}
```

#### Step 2: Data Cleaning
- **Parse Timestamps**: Convert to Asia/Colombo timezone
- **Filter Valid Readings**: Only `status == "online"`
- **Remove Duplicates**: Same timestamp entries
- **Validate Ranges**:
  - Temperature: 0-60°C
  - Lux: ≥ 0
  - Power, Voltage, Current: ≥ 0

#### Step 3: Feature Engineering

**Temporal Features:**
```python
hour = timestamp.hour              # 0-23
minute = timestamp.minute          # 0-59
day_of_week = timestamp.weekday()  # 0=Monday, 6=Sunday
```

**Binary Features:**
```python
fan_on = 1 if fan_status == "ON" else 0
```

**Differential Features:**
```python
power_diff = power[t] - power[t-1]
lux_diff = lux[t] - lux[t-1]
```

**Rolling Aggregates:**
```python
rolling_mean_power_5 = power.rolling(5).mean()
rolling_mean_lux_5 = lux.rolling(5).mean()
```

**Final Feature Set (14 features):**
```
['hour', 'minute', 'day_of_week',
 'servo_angle', 'temperature', 'humidity', 'lux',
 'voltage', 'current', 'power',
 'fan_on', 'power_diff', 'lux_diff',
 'rolling_mean_power_5', 'rolling_mean_lux_5']
```

#### Step 4: Label Creation (15-minute horizon)
```python
# For each reading at time t:
target_time = t + 15_minutes

# Find closest reading within ±30 seconds
matching_reading = find_reading_near(target_time, tolerance=30_sec)

if matching_reading exists:
    target_power = matching_reading.power
    add_row_to_dataset(features, target_power)
else:
    drop_row  # Can't create valid label
```

**Important**: No data leakage! Only past/current features → future power label.

#### Step 5: Export

CSV Format Example:
```csv
timestamp,hour,minute,day_of_week,servo_angle,temperature,humidity,lux,voltage,current,power,fan_on,power_diff,lux_diff,rolling_mean_power_5,rolling_mean_lux_5,target_power_t_plus_15
2026-02-24 06:15:00+0530,6,15,0,45.2,27.3,82.1,5430.0,18.5,2.34,43.29,0,0.0,0.0,43.29,5430.0,44.23
```

### How to Run

#### Basic Usage (Last 7 days)
```bash
cd e:\Solar Tracker
python tools/build_dataset.py --days 7 --out_csv data/solar_dataset.csv
```

#### With Verbose Output
```bash
python tools/build_dataset.py \
  --days 14 \
  --out_csv data/training_data.csv \
  --verbose
```

#### With MongoDB URI
```bash
python tools/build_dataset.py \
  --mongo_uri "mongodb://localhost:27017" \
  --db_name solar_db \
  --days 7 \
  --out_csv data/solar_dataset.csv
```

#### Full Options
```bash
python tools/build_dataset.py \
  --days 30 \
  --device_id tracker01 \
  --horizon_minutes 15 \
  --tolerance_seconds 30 \
  --out_csv data/training_30d.csv \
  --out_report data/dataset_report.json \
  --verbose
```

### Output Analysis

**Dataset Report** (`dataset_report.json`):
```json
{
  "total_rows_fetched": 45000,
  "rows_after_cleaning": 42500,
  "rows_after_labeling": 41800,
  "feature_missing_values": 0,
  "target_missing_values": 200,
  "power_stats": {
    "min": 0.5,
    "max": 285.4,
    "mean": 95.2,
    "std": 67.3
  },
  "timestamp_range": {
    "start": "2026-02-24 06:00:00+0530",
    "end": "2026-03-10 18:00:00+0530"
  }
}
```

### Troubleshooting
- **No data found**: Check MongoDB connection and device_id filter
- **Low label match rate**: Increase `tolerance_seconds` parameter
- **Missing values**: Check data quality in MongoDB or simulator

---

## STAGE 3: FEATURE ENGINEERING (Embedded)

### Note
Feature engineering happens INSIDE `build_dataset.py`. No separate step needed.

### Features Used in ML

The model receives 14 features grouped by type:

| Category | Features | Purpose |
|----------|----------|---------|
| **Time** | hour, minute, day_of_week | Capture daily/weekly solar patterns |
| **Environment** | temperature, humidity | Thermal effects on PV efficiency |
| **Light** | lux | Primary irradiance proxy (from BH1750) |
| **Mechanical** | servo_angle | Tracker position |
| **Electrical** | voltage, current, power | System state |
| **Status** | fan_on | Cooling activity |
| **Dynamics** | power_diff, lux_diff | Rate of change |
| **Trend** | rolling_mean_power_5, rolling_mean_lux_5 | Smoothed history |

### Why These Features?

- **Temporal**: Solar power is highly dependent on time of day/year
- **Environmental**: Temperature reduces PV cell efficiency
- **Lux**: Direct proxy for irradiance (replacing LDR which had noise)
- **Dynamics**: Rate of change helps model transient behavior
- **Trend**: Rolling windows capture longer-term patterns

### Why LDR is NOT Included
- Older methodology replaced by BH1750 sensor
- BH1750 provides direct, calibrated lux measurement
- LDR values still collected but not used in ML training
- LDR still transmitted in API for device compatibility

---

## STAGE 4: MODEL TRAINING

### Purpose
Train a supervised regression model to predict solar power 15 minutes in the future.

### Files Involved
- `tools/train_model.py` - Training script
- `data/solar_dataset.csv` - Input dataset

### Model Architecture

#### Algorithm Choice: RandomForest
- **Why**: Handles non-linear relationships, robust to outliers
- **Hyperparameters**:
  - `n_estimators`: 100 trees
  - `max_depth`: 15 levels
  - `min_samples_split`: 10
  - `min_samples_leaf`: 4
  - `max_features`: 'sqrt' (7 random features per split)

#### Alternative: GradientBoosting
- Sequential tree building
- Higher accuracy but slower inference
- Used for comparison in training

### Training Process

#### Step 1: Load Dataset
```python
df = pd.read_csv("data/solar_dataset.csv")
# 41,800 rows with 14 features + 1 target
```

#### Step 2: Prepare Data
```python
X = df[['hour', 'minute', 'day_of_week', ...]]  # 14 features
y = df['target_power_t_plus_15']                 # Target
```

#### Step 3: Train/Test Split
```python
X_train, X_test, y_train, y_test = train_test_split(
    X, y,
    test_size=0.2,          # 80% train, 20% test
    random_state=42         # Reproducible split
)
# Training: 33,440 samples
# Testing: 8,360 samples
```

#### Step 4: Train RandomForest
```python
model = RandomForestRegressor(
    n_estimators=100,
    max_depth=15,
    max_features='sqrt',
    n_jobs=-1,
    random_state=42
)
model.fit(X_train, y_train)
```

#### Step 5: Evaluate Metrics
```python
y_pred = model.predict(X_test)

metrics = {
    "mae": mean_absolute_error(y_test, y_pred),       # ~3-5W
    "rmse": np.sqrt(mean_squared_error(y_test, y_pred)),  # ~5-8W
    "r2": r2_score(y_test, y_pred),                   # 0.85-0.95
    "mape": mean_absolute_percentage_error(y_test, y_pred)  # 8-12%
}
```

### How to Run

#### Quick Training (1-day dataset)
```bash
cd e:\Solar Tracker
python tools/train_model.py \
  --dataset data/solar_dataset.csv \
  --output Backend/app/ml_models/
```

#### Full Production Training
```bash
python tools/train_model.py \
  --dataset data/solar_dataset.csv \
  --model_type RandomForest \
  --output Backend/app/ml_models/ \
  --verbose
```

#### Train Multiple Models
```bash
# RandomForest (faster)
python tools/train_model.py \
  --dataset data/solar_dataset.csv \
  --model_type RandomForest \
  --output Backend/app/ml_models/

# GradientBoosting (more accurate)
python tools/train_model.py \
  --dataset data/solar_dataset.csv \
  --model_type GradientBoosting \
  --output Backend/app/ml_models/
```

### Output Files

After training completes:

```
Backend/app/ml_models/
├── latest_randomforest.pkl          # Trained model (binary)
├── solar_power_model_RandomForest_[timestamp]_metadata.json  # Metadata
└── training_report_[timestamp].json # Detailed metrics
```

**Metadata Example:**
```json
{
  "model_type": "RandomForest",
  "trained_at": "2026-04-21T14:30:00Z",
  "version": "20260421_143000",
  "dataset_size": 41800,
  "train_size": 33440,
  "test_size": 8360,
  "features": 14,
  "metrics": {
    "mae": 4.23,
    "rmse": 6.78,
    "r2_score": 0.892,
    "mape": 9.34
  },
  "feature_importance": {
    "lux": 0.324,
    "rolling_mean_power_5": 0.267,
    "temperature": 0.156,
    ...
  }
}
```

### Expected Metrics
- **MAE**: 3-6 W (mean prediction error)
- **RMSE**: 5-9 W (penalizes large errors)
- **R²**: 0.85-0.95 (explains 85-95% of variance)
- **MAPE**: 8-15% (percent accuracy)

---

## STAGE 5: INTEGRATION & INFERENCE

### Purpose
Use trained model to make real-time predictions in your FastAPI backend.

### Files Modified
- `Backend/app/services/ml_service.py` - Contains `predict_next_15min()`
- `Backend/app/routers/ml.py` - Prediction API endpoint
- `Backend/app/services/retrain_service.py` - Background retraining

### Model Loading

The backend automatically loads the latest model at startup:

```python
# Backend/app/services/ml_service.py
class MLService:
    def __init__(self, collection):
        self.model = self.load_latest_model()
        
    def load_latest_model(self):
        model_path = "Backend/app/ml_models/latest_randomforest.pkl"
        if Path(model_path).exists():
            return joblib.load(model_path)
        return None
```

### Making Predictions

#### REST API: POST `/api/ml/predict`
```bash
curl -X POST http://localhost:8000/api/ml/predict \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "tracker01",
    "timestamp": "2026-04-21T12:30:00Z",
    "servo_angle": 90.0,
    "temperature": 32.4,
    "humidity": 65.2,
    "lux": 52300.45,
    "voltage": 6.0,
    "current": 0.22,
    "power": 1.32,
    "fan_status": "OFF"
  }'
```

#### Response
```json
{
  "success": true,
  "device_id": "tracker01",
  "current_power": 1.32,
  "predicted_power_15min": 1.47,
  "confidence": 0.89,
  "model_version": "20260421_143000",
  "predicted_at": "2026-04-21T12:30:00Z"
}
```

### Prediction Flow

1. **Receive Reading**: POST request with sensor data
2. **Extract Features**: Convert to 14 features used by model
3. **Normalize Values**: Scale features to training range
4. **Model Inference**: `model.predict(features)` → power value
5. **Calculate Confidence**: Based on prediction std deviation
6. **Return Result**: JSON with prediction + metadata

### Automatic Background Retraining

The backend can automatically retrain the model periodically:

```python
# Schedule in your task queue (Celery/APScheduler)
@periodic_task(run_every=crontab(hour=2, minute=0))  # 2 AM daily
def auto_retrain_model():
    service = RetrainService(db_connection)
    service.retrain(device_id="tracker01", days=30)
    # Automatically updates latest_randomforest.pkl
```

---

## COMPLETE WORKFLOW EXAMPLE

### Start to Finish (1 hour execution)

#### Step 1: Generate Data (15 min)
```bash
cd e:\Solar Tracker
python tools/simulate_solar_final.py --days 7 --mode partly_cloudy --interval_sec 10
# Generates ~60,480 readings over 7 days
```

#### Step 2: Build Dataset (10 min)
```bash
python tools/build_dataset.py --days 7 --out_csv data/solar_dataset.csv --verbose
# Produces: data/solar_dataset.csv (41,800 rows)
```

#### Step 3: Train Model (15 min)
```bash
python tools/train_model.py \
  --dataset data/solar_dataset.csv \
  --output Backend/app/ml_models/ \
  --verbose
# Produces: latest_randomforest.pkl + metadata.json
```

#### Step 4: Start Backend
```bash
cd Backend
python -m uvicorn app.main:app --reload
# Model automatically loads at startup
```

#### Step 5: Make Predictions
```bash
curl -X POST http://localhost:8000/api/ml/predict \
  -H "Content-Type: application/json" \
  -d '{"device_id":"tracker01",...}'
# Returns: predicted_power_15min with confidence
```

#### Step 6: Frontend Display
- Real-time predictions shown on Dashboard
- Confidence indicator
- Comparison with actual values (updates every 15 min)

---

## TROUBLESHOOTING & OPTIMIZATION

### Issue 1: Low Model Accuracy (R² < 0.80)

**Causes & Solutions:**
1. **Insufficient Data**: Use 14+ days instead of 7
   ```bash
   python tools/simulate_solar_final.py --days 14 --mode partly_cloudy
   ```

2. **Poor Feature Engineering**: Check for missing values
   ```bash
   python tools/build_dataset.py --days 14 --verbose
   # Look for "rows_after_cleaning" vs "total_rows_fetched"
   ```

3. **Suboptimal Hyperparameters**: Adjust in `train_model.py`
   ```python
   'n_estimators': 200,  # More trees
   'max_depth': 20,      # Deeper trees
   'min_samples_leaf': 2  # Allow smaller leaves
   ```

### Issue 2: Predictions are Always Same Value

**Cause**: Model not loaded properly
```python
# In ml_service.py, check:
if self.model is None:
    raise ValueError("Model not loaded. Train first: python tools/train_model.py")
```

### Issue 3: Backend Can't Connect to MongoDB

**Solution**: Set environment variable
```bash
# PowerShell
$env:MONGODB_URI = "mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority"

# Or in Backend/.env
MONGODB_URI="mongodb://localhost:27017"
```

### Issue 4: Training Takes Too Long

**Optimization**:
- Use fewer trees: `n_estimators`: 50 (instead of 100)
- Smaller dataset: `--days 7` (instead of 30)
- Use GradientBoosting: `--model_type GradientBoosting`

---

## KEY PARAMETERS YOU CAN TUNE

### Simulator Parameters
```python
--interval_sec 5      # More frequent readings = more training data
--days 30             # Longer period = better generalization
--mode monsoon        # Cloudier = harder problem = better model
```

### Dataset Builder Parameters
```python
--horizon_minutes 30  # Predict further ahead (default: 15 min)
--tolerance_seconds 60  # More lenient label matching
--days 30             # Use more historical data
```

### Model Training Parameters
```python
n_estimators: 200     # More trees = slower but potentially more accurate
max_depth: 20         # Deeper trees = more complex patterns
min_samples_leaf: 2   # Smaller leaves = more overfitting risk
```

---

## NEXT STEPS

1. **Generate 14 days of diverse data**:
   ```bash
   python tools/simulate_solar_final.py --days 7 --mode clear
   python tools/simulate_solar_final.py --days 7 --mode monsoon
   ```

2. **Build combined dataset**:
   ```bash
   python tools/build_dataset.py --days 14 --out_csv data/solar_dataset.csv
   ```

3. **Train production model**:
   ```bash
   python tools/train_model.py --dataset data/solar_dataset.csv --output Backend/app/ml_models/
   ```

4. **Deploy and monitor**:
   - Start backend with trained model
   - Monitor prediction accuracy
   - Collect feedback for retraining

---

## Summary

| Stage | Tool | Input | Output | Time |
|-------|------|-------|--------|------|
| 1. Generate | `simulate_solar_final.py` | Config | MongoDB | 15-30 min |
| 2. Build Dataset | `build_dataset.py` | MongoDB | CSV + Report | 5-10 min |
| 3. Features | Embedded | CSV | Enhanced CSV | Automatic |
| 4. Train | `train_model.py` | CSV | PKL + Metadata | 10-20 min |
| 5. Deploy | FastAPI | PKL | API Predictions | Real-time |

**Total time from zero data to predictions**: ~1-2 hours for full setup.

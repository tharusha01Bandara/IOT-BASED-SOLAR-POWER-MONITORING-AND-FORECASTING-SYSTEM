# Complete ML Workflow - Quick Reference

## 🎯 Goal
Train ML model to predict solar power 15 minutes ahead using IoT sensor data.

## 📊 Full Pipeline

```
IoT Simulator → MongoDB → Dataset Builder → ML Training → Predictions
```

## 🚀 Step-by-Step Commands

### Step 1: Generate Training Data (7 days)
```bash
# Start FastAPI backend
cd Backend
uvicorn app.main:app --reload

# In another terminal: Run simulator
cd tools
python simulate_solar_sl.py --days 7 --interval_sec 300 --mode clear
```

**Result:** ~2,016 readings stored in MongoDB (1 reading every 5 minutes for 7 days)

---

### Step 2: Build ML Dataset
```bash
# From project root
python tools/build_dataset.py \
  --days 7 \
  --horizon_minutes 15 \
  --tolerance_seconds 30 \
  --out_csv data/solar_dataset.csv \
  --out_report data/dataset_report.json \
  --verbose
```

**Result:** 
- `data/solar_dataset.csv` - Clean labeled dataset
- `data/dataset_report.json` - Data quality metrics

**Verify:**
```bash
# Check row count
wc -l data/solar_dataset.csv

# View report
cat data/dataset_report.json | python -m json.tool

# Inspect first few rows
head -20 data/solar_dataset.csv
```

---

### Step 3: Train ML Model via API

**Option A: Train from Database**
```bash
curl -X POST http://localhost:8000/api/ml/train \
  -H "Content-Type: application/json" \
  -d '{
    "data_source": "database",
    "device_id": "tracker01",
    "days": 7,
    "model_type": "random_forest"
  }'
```

**Option B: Train from CSV File**
```python
import requests

with open('data/solar_dataset.csv', 'rb') as f:
    response = requests.post(
        'http://localhost:8000/api/ml/train',
        files={'file': ('dataset.csv', f, 'text/csv')},
        data={'model_type': 'random_forest'}
    )
    
print(response.json())
```

**Result:** Trained model saved as `models/solar_power_model.pkl`

---

### Step 4: Verify Model

**Check model status:**
```bash
curl http://localhost:8000/api/ml/status | python -m json.tool
```

**Expected response:**
```json
{
  "model_loaded": true,
  "model_type": "RandomForestRegressor",
  "features": 15,
  "trained_at": "2026-02-24T10:30:00",
  "metrics": {
    "mse": 0.45,
    "rmse": 0.67,
    "mae": 0.52,
    "r2": 0.89
  }
}
```

---

### Step 5: Make Predictions

**Manual prediction:**
```bash
curl -X POST http://localhost:8000/api/ml/predict \
  -H "Content-Type: application/json" \
  -d '{
    "hour": 12,
    "minute": 30,
    "day_of_week": 1,
    "servo_angle": 90.5,
    "temperature": 35.2,
    "humidity": 68.5,
    "lux": 98500,
    "voltage": 14.2,
    "current": 0.85,
    "power": 9.8,
    "fan_on": 0,
    "power_diff": 0.3,
    "lux_diff": 1200,
    "rolling_mean_power_5": 9.5,
    "rolling_mean_lux_5": 97800
  }'
```

**Auto-prediction with new readings:**
```bash
# Post reading with prediction enabled
curl -X POST "http://localhost:8000/api/readings?predict=true" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "tracker01",
    "timestamp": "2026-02-24T12:00:00+05:30",
    "servo_angle": 90.0,
    "temperature": 34.5,
    "humidity": 70.2,
    "lux": 95000,
    "voltage": 14.5,
    "current": 0.82,
    "power": 9.6,
    "fan_status": "off",
    "status": "online"
  }'
```

---

## 📈 Dataset Quality Checklist

After building dataset, verify these metrics:

- [ ] **Rows after labeling** > 1,500 (for 7 days @ 5min intervals)
- [ ] **Label match failures** < 10%
- [ ] **Power stats** reasonable (mean ~5-8W for clear day)
- [ ] **Lux stats** realistic (peak ~95-110k for clear sky)
- [ ] **No excessive missing values** (all columns < 1% missing)
- [ ] **Timespan** covers full requested period

**View report:**
```bash
python -c "import json; print(json.dumps(json.load(open('data/dataset_report.json')), indent=2))"
```

---

## 🔧 Common Issues & Fixes

### Issue: No data fetched
**Fix:** Ensure simulator has run and backend is storing data
```bash
# Check MongoDB has data
mongo "your_connection_string" --eval "db.readings_raw.count()"
```

### Issue: All data filtered out
**Fix:** Simulator status field mismatch
- Dataset builder expects: `"online"` / `"error"`
- Old simulator sent: `"ok"` / `"invalid"`
- **Solution:** Use updated simulator with correct enum values

### Issue: No valid labels created
**Fix:** Increase tolerance or check data gaps
```bash
# Use larger tolerance
python tools/build_dataset.py --days 7 --tolerance_seconds 60
```

### Issue: Model performance poor (R² < 0.7)
**Fixes:**
1. Generate more training data (14-30 days)
2. Try different model types (gradient_boosting)
3. Check for data quality issues in report
4. Verify weather mode matches training scenario

---

## 📊 Expected Dataset Structure

**Columns (16 total):**
```
ts                      - Timestamp (ISO format with timezone)
hour                    - Hour of day (0-23)
minute                  - Minute (0-59)
day_of_week             - Day of week (0=Mon, 6=Sun)
servo_angle             - Servo position (30-160°)
temperature             - Panel temperature (°C)
humidity                - Relative humidity (%)
lux                     - Light intensity
voltage                 - PV voltage (V)
current                 - PV current (A)
power                   - PV power (W) - INPUT FEATURE
fan_on                  - Fan status (0/1)
power_diff              - Power change from previous
lux_diff                - Lux change from previous
rolling_mean_power_5    - 5-sample rolling mean power
rolling_mean_lux_5      - 5-sample rolling mean lux
target_power_t_plus_15  - Power 15min ahead - TARGET LABEL
```

**Sample row:**
```csv
2026-02-24 12:00:00+0530,12,0,0,90.1,34.5,70.2,95432.0,14.3,0.81,9.45,0,0.15,850.2,9.38,94500.3,10.12
```

---

## 🎓 Training Tips

### For Best Model Performance:

1. **Data Volume:**
   - Minimum: 7 days (testing)
   - Recommended: 14-30 days (production)
   - Optimal: Mix of weather conditions

2. **Data Quality:**
   - Clean data (status == "online")
   - No large gaps in time series
   - Realistic sensor ranges

3. **Model Selection:**
   - `random_forest`: Good general performance, fast
   - `gradient_boosting`: Better accuracy, slower
   - `linear_regression`: Fast baseline, less accurate

4. **Feature Importance:**
   - Top predictors: `lux`, `power`, `hour`, `rolling_mean_power_5`
   - Less important: `humidity`, `day_of_week`

---

## 📁 File Locations

```
Solar Tracker/
├── tools/
│   ├── simulate_solar_sl.py           # Data generator
│   ├── build_dataset.py                # Dataset builder ⭐
│   ├── requirements_dataset.txt        # Dependencies
│   └── DATASET_BUILDER_GUIDE.md       # Full documentation
├── data/
│   ├── solar_dataset.csv              # Training dataset ⭐
│   └── dataset_report.json            # Quality metrics ⭐
├── Backend/
│   ├── app/services/ml_service.py     # ML training logic
│   ├── app/routers/ml.py              # ML API endpoints
│   └── models/
│       └── solar_power_model.pkl      # Trained model ⭐
└── ML_INTEGRATION_GUIDE.md            # Complete ML docs
```

---

## ✅ Complete Workflow Checklist

- [ ] 1. Generate training data (7+ days)
- [ ] 2. Build dataset with build_dataset.py
- [ ] 3. Review dataset_report.json
- [ ] 4. Inspect solar_dataset.csv
- [ ] 5. Train model via API
- [ ] 6. Check model status and metrics
- [ ] 7. Test predictions
- [ ] 8. Enable auto-prediction (?predict=true)
- [ ] 9. Monitor prediction accuracy
- [ ] 10. Retrain periodically with new data

---

## 🚀 Production Deployment

### Automated Retraining Pipeline:

```bash
#!/bin/bash
# retrain_model.sh - Run weekly

# 1. Build fresh dataset (last 30 days)
python tools/build_dataset.py --days 30 --out_csv data/latest_dataset.csv

# 2. Check data quality
ROWS=$(wc -l < data/latest_dataset.csv)
if [ $ROWS -lt 5000 ]; then
    echo "Insufficient data: $ROWS rows"
    exit 1
fi

# 3. Train new model
curl -X POST http://localhost:8000/api/ml/train \
  -H "Content-Type: application/json" \
  -d '{"data_source": "database", "days": 30, "model_type": "random_forest"}'

# 4. Verify model loaded
curl http://localhost:8000/api/ml/status

echo "Retraining complete!"
```

### Schedule with cron:
```bash
# Retrain every Sunday at 2 AM
0 2 * * 0 /path/to/solar-tracker/retrain_model.sh >> /var/log/ml_retrain.log 2>&1
```

---

## 📚 Documentation Links

- **Dataset Builder:** `tools/DATASET_BUILDER_GUIDE.md`
- **ML Integration:** `ML_INTEGRATION_GUIDE.md`
- **Simulator:** `tools/README_SIMULATOR.md`
- **API Docs:** `http://localhost:8000/docs`

---

**Ready to train your first model?** Start with Step 1! 🚀

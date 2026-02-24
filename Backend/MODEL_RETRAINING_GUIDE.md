# Model Retraining System - Step 3.7

Complete automated model retraining system with versioning, logging, and scheduled execution.

## 🎯 Overview

This system provides:
- **Automated model retraining** on schedule
- **Model versioning** with timestamped files
- **Performance-based promotion** (only promote if better)
- **Training run logging** to MongoDB
- **Management APIs** for monitoring and control
- **Standalone worker** for production deployment

---

## 📁 File Structure

```
Backend/
├── app/
│   ├── services/
│   │   ├── ml_service.py           # Updated: loads current model pointer
│   │   └── retrain_service.py      # NEW: Core retraining logic
│   ├── routers/
│   │   ├── ml.py                    # Existing ML endpoints
│   │   └── ml_management.py         # NEW: Management APIs
│   ├── core/
│   │   └── config.py                # Updated: retraining settings
│   └── ml_models/
│       ├── versions/                # NEW: Versioned models storage
│       └── current_model.json       # NEW: Current model pointer

tools/
└── retrain_worker.py                # NEW: Standalone retraining worker
```

---

## ⚙️ Configuration

### Environment Variables

Add to your `.env` file:

```bash
# MongoDB Collections
COLLECTION_MODEL_RUNS="model_runs"

# ML Model Configuration
MODEL_DIR="app/ml_models"
MODEL_VERSIONS_DIR="app/ml_models/versions"
MODEL_CURRENT_POINTER="app/ml_models/current_model.json"

# Retraining Configuration
RETRAIN_ENABLED=True
RETRAIN_DAYS=7                    # Days of data to use
RETRAIN_INTERVAL_HOURS=24         # Interval between retrains
RETRAIN_TIME="18:30"              # Time of day (HH:MM)
TIMEZONE="Asia/Colombo"           # Your timezone
MAE_THRESHOLD_PERCENT=10.0        # Max allowed MAE increase (%)
```

### Model Promotion Policy

A new model is **promoted** (becomes current) only if:
- No current model exists, OR
- New model MAE is better than current MAE, OR
- New model MAE is worse by ≤ `MAE_THRESHOLD_PERCENT` (default: 10%)

If a model is **not promoted**, it's still saved and logged, but predictions continue using the current model.

---

## 🚀 Usage

### 1. Standalone Worker (Recommended for Production)

The worker can run once or continuously on a schedule.

#### Run Once (Manual Retraining)

```bash
# Navigate to tools directory
cd tools

# Run retraining
python retrain_worker.py --device tracker01 --days 7

# With verbose logging
python retrain_worker.py --device tracker01 --days 7 --verbose

# Dry run (test without training)
python retrain_worker.py --device tracker01 --dry-run
```

#### Run in Scheduler Mode

Keeps running and executes retraining at scheduled time daily:

```bash
# Run scheduler (checks every 60 seconds)
python retrain_worker.py --schedule --device tracker01

# Custom schedule time
python retrain_worker.py --schedule --device tracker01 --time 18:30

# Custom check interval (5 minutes)
python retrain_worker.py --schedule --device tracker01 --check-interval 300
```

**Stop scheduler:** Press `Ctrl+C` (graceful shutdown)

---

### 2. Cron/Task Scheduler Automation

#### Linux/macOS (crontab)

```bash
# Edit crontab
crontab -e

# Add daily retraining at 18:30
30 18 * * * cd /path/to/tools && /path/to/venv/bin/python retrain_worker.py --device tracker01 --days 7 >> /var/log/solar_retrain.log 2>&1

# Example with full paths
30 18 * * * cd /home/user/solar-tracker/tools && /home/user/solar-tracker/venv/bin/python retrain_worker.py --device tracker01 --days 7 >> /var/log/solar_retrain.log 2>&1
```

**Verify cron job:**
```bash
crontab -l
```

#### Windows (Task Scheduler)

**Option A: GUI**

1. Open Task Scheduler
2. Create Basic Task → Name: "Solar Model Retraining"
3. Trigger: Daily at 18:30
4. Action: Start a program
   - Program: `E:\Solar Tracker\venv\Scripts\python.exe`
   - Arguments: `retrain_worker.py --device tracker01 --days 7`
   - Start in: `E:\Solar Tracker\tools`
5. Finish

**Option B: Command Line (PowerShell as Admin)**

```powershell
$action = New-ScheduledTaskAction -Execute "E:\Solar Tracker\venv\Scripts\python.exe" -Argument "retrain_worker.py --device tracker01 --days 7" -WorkingDirectory "E:\Solar Tracker\tools"

$trigger = New-ScheduledTaskTrigger -Daily -At 18:30

Register-ScheduledTask -TaskName "SolarModelRetraining" -Action $action -Trigger $trigger -Description "Daily ML model retraining for solar tracker"
```

**Verify:**
```powershell
Get-ScheduledTask -TaskName "SolarModelRetraining"
```

---

### 3. Management APIs

Once the backend is running, use these endpoints:

#### 3.1. Trigger Manual Retraining

```bash
# Background (non-blocking)
curl -X POST http://localhost:8000/api/ml/retrain \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "tracker01",
    "days": 7,
    "background": true
  }'

# Foreground (blocking - waits for completion)
curl -X POST http://localhost:8000/api/ml/retrain \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "tracker01",
    "days": 7,
    "background": false
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Retraining started in background",
  "background": true
}
```

#### 3.2. Get Training Runs History

```bash
# Get last 20 runs
curl http://localhost:8000/api/ml/runs

# Filter by device
curl http://localhost:8000/api/ml/runs?device_id=tracker01

# Pagination
curl http://localhost:8000/api/ml/runs?limit=10&skip=20
```

**Response:**
```json
{
  "total": 45,
  "runs": [
    {
      "run_id": "abc-123",
      "device_id": "tracker01",
      "trained_at": "2026-02-24T18:30:00Z",
      "days_used": 7,
      "rows_used": 1981,
      "mae": 0.203,
      "rmse": 0.432,
      "r2": 0.991,
      "status": "success",
      "promoted": true,
      "error": null
    }
  ]
}
```

#### 3.3. Get Current Model Info

```bash
curl http://localhost:8000/api/ml/model/current
```

**Response:**
```json
{
  "model_exists": true,
  "version": "20260224_183000",
  "updated_at": "2026-02-24T18:30:00Z",
  "model_path": "app/ml_models/versions/model_20260224_183000.pkl",
  "metrics": {
    "mae": 0.203,
    "rmse": 0.432,
    "r2": 0.991
  }
}
```

#### 3.4. Get Specific Training Run

```bash
curl http://localhost:8000/api/ml/runs/abc-123
```

#### 3.5. Delete Training Run Record

```bash
curl -X DELETE http://localhost:8000/api/ml/runs/abc-123
```

---

## 🗄️ MongoDB Collections

### `model_runs` Collection

Stores all training run results:

```javascript
{
  "run_id": "550e8400-e29b-41d4-a716-446655440000",
  "device_id": "tracker01",
  "trained_at": ISODate("2026-02-24T18:30:00Z"),
  "days_used": 7,
  "horizon_minutes": 15,
  "rows_used": 1981,
  "mae": 0.203,
  "rmse": 0.432,
  "r2": 0.991,
  "train_samples": 1584,
  "test_samples": 397,
  "features": ["hour", "minute", ...],
  "model_path": "app/ml_models/versions/model_20260224_183000.pkl",
  "status": "success",
  "error": null,
  "promoted": true
}
```

**Query Examples:**

```javascript
// Get all successful runs
db.model_runs.find({ status: "success" })

// Get promoted models only
db.model_runs.find({ promoted: true })

// Get runs with MAE < 0.3
db.model_runs.find({ mae: { $lt: 0.3 } })

// Get last 10 runs, sorted by date
db.model_runs.find().sort({ trained_at: -1 }).limit(10)
```

---

## 📦 Model Versioning

### File Structure

```
app/ml_models/
├── versions/
│   ├── model_20260224_183000.pkl          # Trained model
│   ├── model_20260224_183000_meta.json    # Metadata
│   ├── model_20260225_183000.pkl
│   ├── model_20260225_183000_meta.json
│   └── ...
└── current_model.json                      # Pointer to active model
```

### Current Model Pointer (`current_model.json`)

```json
{
  "model_path": "app/ml_models/versions/model_20260224_183000.pkl",
  "metadata_path": "app/ml_models/versions/model_20260224_183000_meta.json",
  "version": "20260224_183000",
  "updated_at": "2026-02-24T18:30:15.123456Z",
  "metrics": {
    "mae": 0.203,
    "rmse": 0.432,
    "r2": 0.991,
    "train_samples": 1584,
    "test_samples": 397
  }
}
```

### Model Metadata File

```json
{
  "device_id": "tracker01",
  "version": "20260224_183000",
  "trained_at": "2026-02-24T18:30:00Z",
  "days_used": 7,
  "rows_used": 1981,
  "features": [
    "hour", "minute", "day_of_week",
    "servo_angle", "temperature", "humidity", "lux",
    "voltage", "current", "power",
    "fan_on", "power_diff", "lux_diff",
    "rolling_mean_power_5", "rolling_mean_lux_5"
  ],
  "metrics": {
    "mae": 0.203,
    "rmse": 0.432,
    "r2": 0.991,
    "train_samples": 1584,
    "test_samples": 397
  },
  "model_type": "RandomForest"
}
```

---

## 🔍 Monitoring & Debugging

### Check Worker Status

```bash
# Check if worker is running (Linux/macOS)
ps aux | grep retrain_worker

# Check if worker is running (Windows)
Get-Process | Where-Object {$_.ProcessName -eq "python" -and $_.CommandLine -like "*retrain_worker*"}
```

### View Logs

Worker logs go to stdout. Redirect to file for persistence:

```bash
# Linux/macOS
python retrain_worker.py --schedule --device tracker01 >> /var/log/solar_retrain.log 2>&1

# Windows PowerShell
python retrain_worker.py --schedule --device tracker01 2>&1 | Tee-Object -FilePath "C:\logs\solar_retrain.log"
```

### Test MongoDB Connection

```python
from pymongo import MongoClient
client = MongoClient("your_mongodb_uri")
db = client["solar_db"]
runs = db["model_runs"].find().limit(5)
for run in runs:
    print(run)
```

---

## 🛠️ Troubleshooting

### Issue: "No data found for training"

**Cause:** Not enough data in MongoDB for the specified date range.

**Solutions:**
- Reduce `--days` parameter: `--days 3`
- Run simulator to generate more data
- Check MongoDB contains data: `db.readings_raw.count()`

### Issue: "Model not promoted"

**Cause:** New model performance is worse than current model.

**Check logs:** Look for promotion decision message showing MAE comparison.

**Solutions:**
- This is expected behavior (quality control)
- Model is still saved and logged
- Try training with more days: `--days 14`
- Check data quality

### Issue: Worker not running on schedule

**Linux/macOS (cron):**
```bash
# Check cron is running
sudo systemctl status cron

# Check cron logs
grep CRON /var/log/syslog

# Test cron command manually
cd /path/to/tools && /path/to/venv/bin/python retrain_worker.py --device tracker01 --days 7
```

**Windows (Task Scheduler):**
- Open Task Scheduler
- Find task → Right-click → Properties
- Check "History" tab for execution logs
- Verify "Start in" path is correct

### Issue: ModuleNotFoundError

**Cause:** Python path issue when running from cron/Task Scheduler.

**Solution:** Use absolute paths:
```bash
# Instead of
python retrain_worker.py

# Use
/full/path/to/venv/bin/python /full/path/to/retrain_worker.py
```

---

## 🔐 Best Practices

### 1. **Data Backup**

Before enabling automatic retraining:
```bash
# Backup MongoDB
mongodump --uri="your_mongodb_uri" --db=solar_db --out=./backup

# Backup current models
cp -r app/ml_models/versions app/ml_models/versions_backup
```

### 2. **Monitoring**

Set up monitoring for:
- Worker process health
- Training success rate (`status: "success"` in model_runs)
- Model performance trends (MAE over time)
- Disk space in `versions/` directory

### 3. **Cleanup Old Models**

Models accumulate over time. Clean up periodically:

```bash
# Keep only last 30 versions
cd app/ml_models/versions
ls -t model_*.pkl | tail -n +31 | xargs rm
ls -t model_*_meta.json | tail -n +31 | xargs rm
```

Or automate with a cleanup script.

### 4. **Alert on Failures**

Monitor `model_runs` for failures:

```javascript
// Get failed runs
db.model_runs.find({ status: "failed" }).sort({ trained_at: -1 }).limit(10)
```

Set up alerts (email/Slack) when failures occur.

### 5. **Resource Management**

- Training uses CPU/memory
- Schedule during low-traffic periods (e.g., nighttime)
- Consider running on separate worker machine in production

---

## 📊 Performance Tuning

### Training Speed

Adjust model parameters in `retrain_service.py`:

```python
# Faster training (lower accuracy)
model = RandomForestRegressor(
    n_estimators=50,     # Reduced from 100
    max_depth=10,        # Reduced from 15
    n_jobs=-1
)

# Better accuracy (slower)
model = RandomForestRegressor(
    n_estimators=200,    # Increased from 100
    max_depth=20,        # Increased from 15
    n_jobs=-1
)
```

### Data Amount

More data = better models (usually):
- Start with 7 days
- Increase to 14 or 30 days for more patterns
- Trade-off: more data = longer training time

---

## 🎓 Architecture Notes

### Why Separate Worker?

1. **Stability:** Backend crash doesn't stop training
2. **Scaling:** Run workers on dedicated machines
3. **Simplicity:** Easy cron scheduling
4. **Testing:** Can test training without backend

### Atomic Model Updates

Current model pointer uses **atomic write** (write to temp file, then rename) to prevent:
- Partial updates
- Race conditions
- Serving corrupted models

### Time-based Split

Training uses **time-based** train/test split (not random) to:
- Prevent data leakage (future data in training set)
- Simulate real-world deployment
- Properly evaluate time-series forecasting

---

## 📚 Additional Resources

- **API Documentation:** `http://localhost:8000/docs` (when DEBUG=True)
- **MongoDB Compass:** Visual tool for browsing model_runs collection
- **Grafana/Kibana:** Monitor model performance metrics over time

---

## ✅ Quick Verification Checklist

After setup, verify:

- [ ] `.env` has retraining configuration
- [ ] MongoDB has `model_runs` collection
- [ ] `app/ml_models/versions/` directory exists
- [ ] Worker runs successfully: `python retrain_worker.py --device tracker01 --dry-run`
- [ ] APIs respond: `curl http://localhost:8000/api/ml/model/current`
- [ ] Cron/Task Scheduler configured (if using)
- [ ] Logs are being written
- [ ] First training run completed and logged

---

## 🆘 Support

If issues persist:
1. Check logs for detailed error messages
2. Verify MongoDB connection: `db.adminCommand({ ping: 1 })`
3. Test training manually before scheduling
4. Review `model_runs` collection for error patterns

---

**System Status:** ✅ Production-ready  
**Last Updated:** February 24, 2026  
**Version:** 3.7.0

# Model Retraining Quick Reference

## ⚡ Quick Commands

### Test System
```bash
# Test everything
python tools/test_retraining.py tracker01

# Test without training
python tools/retrain_worker.py --device tracker01 --dry-run
```

### Manual Retraining
```bash
# Single run
python tools/retrain_worker.py --device tracker01 --days 7

# With verbose logs
python tools/retrain_worker.py --device tracker01 --days 7 --verbose
```

### Scheduler Mode
```bash
# Run continuous scheduler
python tools/retrain_worker.py --schedule --device tracker01

# Custom time (18:30)
python tools/retrain_worker.py --schedule --device tracker01 --time 18:30
```

### API Calls
```bash
# Trigger retraining
curl -X POST http://localhost:8000/api/ml/retrain \
  -H "Content-Type: application/json" \
  -d '{"device_id":"tracker01","days":7,"background":true}'

# List training runs
curl http://localhost:8000/api/ml/runs?limit=10

# Current model info
curl http://localhost:8000/api/ml/model/current
```

---

## 🔧 Configuration (.env)

```bash
# Essential settings
COLLECTION_MODEL_RUNS="model_runs"
RETRAIN_ENABLED=True
RETRAIN_DAYS=7
RETRAIN_TIME="18:30"
TIMEZONE="Asia/Colombo"
MAE_THRESHOLD_PERCENT=10.0
```

---

## 📅 Scheduling

### Linux/macOS (crontab)
```bash
# Add to crontab (crontab -e)
30 18 * * * cd /path/to/tools && python retrain_worker.py --device tracker01
```

### Windows PowerShell (as Admin)
```powershell
# Quick setup
.\tools\setup_windows_scheduler.ps1
```

---

## 🔍 Monitoring

```bash
# Check worker process
ps aux | grep retrain_worker          # Linux/macOS
Get-Process | Select-String "retrain" # Windows

# View logs
tail -f /var/log/solar_retrain.log    # Linux/macOS
Get-Content solar_retrain.log -Wait   # Windows
```

### MongoDB Queries
```javascript
// Get last 10 runs
db.model_runs.find().sort({trained_at:-1}).limit(10)

// Get failed runs
db.model_runs.find({status:"failed"})

// Get promoted models
db.model_runs.find({promoted:true})
```

---

## 📊 Key Metrics

- **MAE** (Mean Absolute Error): Target < 0.5 W
- **R²** (R-squared): Target > 0.90
- **Training Time**: ~30-60 seconds
- **Data Required**: Minimum 100 samples, recommended 1000+

---

## 🚨 Troubleshooting

| Issue | Solution |
|-------|----------|
| "No data found" | Reduce `--days` or run simulator |
| "Model not promoted" | Normal! New model wasn't better |
| Worker not running | Check cron/Task Scheduler logs |
| ModuleNotFoundError | Use absolute paths in cron |

---

## 📂 File Locations

```
Backend/
├── app/ml_models/
│   ├── versions/              # All versioned models
│   └── current_model.json     # Active model pointer
└── MODEL_RETRAINING_GUIDE.md  # Full documentation

tools/
├── retrain_worker.py          # Main worker script
└── test_retraining.py         # Test suite
```

---

## 🎯 Model Promotion Logic

New model is promoted if:
- ✅ No current model exists, OR
- ✅ New MAE < Current MAE, OR
- ✅ New MAE ≤ Current MAE × (1 + threshold/100)

Example: If current MAE = 0.20, threshold = 10%
- Promote if new MAE ≤ 0.22 (0.20 × 1.10)

---

## ⏱️ Scheduler Behavior

- Checks every 60s (configurable with `--check-interval`)
- Runs at configured time (default: 18:30)
- Only runs once per day
- Graceful shutdown on Ctrl+C

---

## 📈 Best Practices

1. **Backup before first run**: `mongodump --db=solar_db`
2. **Start with 7 days**: Balance freshness vs. patterns
3. **Monitor first week**: Check `model_runs` for issues
4. **Clean old models monthly**: Keep last 30 versions
5. **Set up alerts**: Email on training failures

---

## 🔗 Links

- Full Guide: [MODEL_RETRAINING_GUIDE.md](MODEL_RETRAINING_GUIDE.md)
- API Docs: http://localhost:8000/docs
- MongoDB: Use MongoDB Compass for visual inspection

---

**Status**: ✅ Production-ready | **Version**: 3.7.0

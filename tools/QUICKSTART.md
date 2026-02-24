# Quick Start: Sri Lanka Solar Simulator

## Step 1: Install Dependencies

```bash
cd "e:\Solar Tracker\tools"
pip install pytz requests
```

## Step 2: Test the Simulator (No Backend Required)

```bash
python test_simulator.py
```

Expected output: All tests pass ✅

## Step 3: Start the FastAPI Backend

```bash
cd "e:\Solar Tracker"
uvicorn app.main:app --reload
```

Verify backend is running:
```bash
curl http://127.0.0.1:8000/health
```

## Step 4: Run Your First Simulation

### Example 1: Simulate 1 Clear Day (Recommended First Test)

```bash
cd tools
python simulate_solar_sl.py --days 1 --mode clear --interval_sec 10
```

**What happens:**
- Generates ~8,640 readings (1 every 10 seconds for 24 hours)
- Posts to http://127.0.0.1:8000/api/readings
- Shows progress every 100 readings
- Takes 24 hours in real-time (or faster if backend keeps up)

**Expected output:**
```
======================================================================
Sri Lanka Solar Tracker Simulator - Starting
======================================================================
Device ID:     tracker01
Weather Mode:  clear
Interval:      10 seconds
Duration:      1 days
...

Progress: 100/8,640 readings | Success rate: 100.0% | Time: 2026-02-23 06:16:40
Progress: 200/8,640 readings | Success rate: 100.0% | Time: 2026-02-23 06:33:20
...
```

### Example 2: Quick Test (1 Hour Only)

To test quickly without waiting 24 hours, simulate faster:

```bash
# Option A: Reduce interval to 1 second (360 readings per hour)
python simulate_solar_sl.py --days 0.042 --interval_sec 1 --mode clear
# 0.042 days = 1 hour

# Option B: Use high interval but short duration
python simulate_solar_sl.py --days 0.083 --interval_sec 30 --mode clear
# 0.083 days = 2 hours, 1 reading every 30 seconds
```

### Example 3: Generate ML Training Data (7 Days)

```bash
# 7 days of clear weather data at 5-minute intervals
python simulate_solar_sl.py \
  --days 7 \
  --interval_sec 300 \
  --mode clear \
  --start_date "2026-01-01 00:00:00"
```

**Output**: ~2,016 readings (perfect for ML training)

### Example 4: Simulate Monsoon Weather

```bash
python simulate_solar_sl.py \
  --days 3 \
  --interval_sec 5 \
  --mode monsoon
```

Lower peak lux, more clouds, higher humidity.

### Example 5: Multiple Devices

Run in separate terminals:

```bash
# Terminal 1
python simulate_solar_sl.py --device_id tracker01 --days 1

# Terminal 2
python simulate_solar_sl.py --device_id tracker02 --days 1

# Terminal 3
python simulate_solar_sl.py --device_id tracker03 --days 1
```

## Step 5: Verify Data in Backend

### Check Latest Reading

```bash
curl "http://127.0.0.1:8000/api/readings/latest?device_id=tracker01"
```

### Check Reading History

```bash
curl "http://127.0.0.1:8000/api/readings/history?device_id=tracker01&hours=1"
```

### Check Statistics

```bash
curl "http://127.0.0.1:8000/api/readings/statistics?device_id=tracker01&hours=24"
```

## Step 6: Train ML Model with Generated Data

Once you have 7+ days of data:

```bash
curl -X POST "http://127.0.0.1:8000/api/ml/train" \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "tracker01",
    "days": 7,
    "model_type": "RandomForest"
  }'
```

## Troubleshooting

### 1. "Connection refused"

**Problem**: Backend is not running

**Solution**:
```bash
# In another terminal, start backend
cd "e:\Solar Tracker"
uvicorn app.main:app --reload
```

### 2. "pytz not installed" warning

**Problem**: Optional timezone library missing

**Solution**:
```bash
pip install pytz
```

The simulator still works without pytz, but installing it provides better timezone support.

### 3. Simulator too slow

**Problem**: Real-time simulation takes too long

**Solution**: There's no "fast-forward" mode because the backend needs to process each reading. Options:
- Use larger `--interval_sec` (e.g., 60 or 300 seconds)
- Simulate shorter duration (e.g., `--days 0.1` = 2.4 hours)
- Run multiple shorter simulations

### 4. Backend can't keep up

**Problem**: Readings are failing with timeout errors

**Solution**:
- Increase `--interval_sec` to give backend more processing time
- Check backend logs for performance issues
- Verify MongoDB connection is stable

## Common Scenarios

### Scenario 1: Collect Full Week for ML Training

```bash
# Start backend (Terminal 1)
uvicorn app.main:app --reload

# Run 7-day simulation with 5-min intervals (Terminal 2)
cd tools
python simulate_solar_sl.py \
  --days 7 \
  --interval_sec 300 \
  --mode clear \
  --start_date "2026-01-01 06:00:00"

# This will take 7 days real-time, but generates perfect training data
# Result: ~2,016 readings in MongoDB
```

### Scenario 2: Quick Testing (5 minutes of data)

```bash
# Generate 5 minutes of high-frequency data
python simulate_solar_sl.py \
  --days 0.00347 \
  --interval_sec 1 \
  --mode partly_cloudy

# 0.00347 days = 5 minutes
# Result: 300 readings
```

### Scenario 3: Compare Weather Modes

```bash
# Day 1: Clear
python simulate_solar_sl.py --days 1 --mode clear --device_id tracker01

# Day 2: Partly Cloudy (wait for Day 1 to finish)
python simulate_solar_sl.py --days 1 --mode partly_cloudy --device_id tracker01

# Day 3: Monsoon
python simulate_solar_sl.py --days 1 --mode monsoon --device_id tracker01

# Now compare in backend
curl "http://127.0.0.1:8000/api/readings/statistics?device_id=tracker01&hours=72"
```

## Next Steps

1. ✅ **Collect baseline data**: Run 1 day clear simulation
2. ✅ **Verify data quality**: Check backend statistics
3. ✅ **Train ML model**: Use 7 days of data
4. ✅ **Test predictions**: Enable `?predict=true` on readings endpoint
5. ✅ **Experiment**: Try different weather modes and intervals

## Pro Tips

### Tip 1: Use `--verbose` for Debugging

```bash
python simulate_solar_sl.py --days 1 --mode clear --verbose
```

Shows detailed logs including each reading posted.

### Tip 2: Background Simulation

```bash
# Run in background (Linux/Mac)
nohup python simulate_solar_sl.py --days 7 --mode clear > simulation.log 2>&1 &

# Windows: Use `start` command
start /B python simulate_solar_sl.py --days 7 --mode clear
```

### Tip 3: Different Times of Day

```bash
# Start at sunrise
python simulate_solar_sl.py --start_date "2026-02-23 06:00:00" --days 0.5

# Start at noon (peak sun)
python simulate_solar_sl.py --start_date "2026-02-23 12:00:00" --days 0.5

# Start at sunset
python simulate_solar_sl.py --start_date "2026-02-23 18:00:00" --days 0.5
```

### Tip 4: Save Simulation Statistics

```bash
python simulate_solar_sl.py --days 1 --mode clear 2>&1 | tee simulation_log.txt
```

Saves output to file while showing on screen.

## Recommended Workflow

```bash
# 1. Test simulator (no backend needed)
python test_simulator.py

# 2. Start backend
uvicorn app.main:app --reload

# 3. Quick test (1 hour)
python simulate_solar_sl.py --days 0.042 --interval_sec 10 --mode clear

# 4. If successful, run full simulation
python simulate_solar_sl.py --days 7 --interval_sec 300 --mode clear

# 5. Train ML model
curl -X POST http://127.0.0.1:8000/api/ml/train \
  -H "Content-Type: application/json" \
  -d '{"device_id": "tracker01", "days": 7}'

# 6. Test predictions
curl -X POST "http://127.0.0.1:8000/api/readings?predict=true" \
  -H "Content-Type: application/json" \
  -d '{...next reading...}'
```

---

**Happy Simulating! 🌞**

For detailed documentation, see [README_SIMULATOR.md](README_SIMULATOR.md)

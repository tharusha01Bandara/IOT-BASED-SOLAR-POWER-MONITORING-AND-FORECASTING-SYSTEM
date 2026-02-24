# Dataset Builder Tool - Usage Guide

## Overview

The `build_dataset.py` script transforms raw IoT sensor readings from MongoDB into a clean, labeled ML dataset for training power prediction models.

## Quick Start

### 1. Install Dependencies

```bash
# From project root
pip install -r tools/requirements_dataset.txt
```

### 2. Set MongoDB Connection

**Option A: Environment Variable**
```bash
export MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority"
```

**Option B: .env File**
```bash
# Create .env file in project root
echo 'MONGODB_URI="mongodb+srv://username:password@cluster.mongodb.net/"' > .env
```

**Option C: Command Line**
```bash
python build_dataset.py --mongo_uri "mongodb://localhost:27017" --days 7
```

### 3. Build Dataset

```bash
# Basic usage (last 7 days)
python tools/build_dataset.py --days 7 --out_csv data/solar_dataset.csv

# With custom settings
python tools/build_dataset.py \
  --days 14 \
  --horizon_minutes 15 \
  --tolerance_seconds 30 \
  --out_csv data/training_data.csv \
  --out_report data/report.json
```

## Command Line Options

| Option | Default | Description |
|--------|---------|-------------|
| `--mongo_uri` | `$MONGODB_URI` | MongoDB connection string |
| `--db_name` | `solar_db` | Database name |
| `--collection` | `readings_raw` | Collection name |
| `--device_id` | `tracker01` | Device ID to filter |
| `--days` | `7` | Number of days to fetch |
| `--horizon_minutes` | `15` | Prediction horizon (minutes ahead) |
| `--tolerance_seconds` | `30` | Label matching tolerance (±seconds) |
| `--out_csv` | `data/solar_dataset.csv` | Output CSV path |
| `--out_parquet` | None | Output Parquet path (optional) |
| `--out_report` | `data/dataset_report.json` | Report JSON path |
| `--verbose` | False | Enable debug logging |

## Pipeline Steps

### Step 1: Data Fetching
- Connects to MongoDB
- Fetches readings for specified device and time range
- Sorts by timestamp ascending

### Step 2: Data Cleaning
- Parses timestamps to Asia/Colombo timezone
- Filters out non-"online" status readings
- Removes duplicate timestamps
- Validates sensor ranges:
  - `temperature`: 0-60°C
  - `lux`, `voltage`, `current`, `power`: ≥ 0

### Step 3: Feature Engineering

**Temporal Features:**
- `hour` (0-23)
- `minute` (0-59)
- `day_of_week` (0=Monday, 6=Sunday)

**Binary Features:**
- `fan_on` (1 if fan_status=="on", else 0)

**Differential Features:**
- `power_diff` = power - power_previous
- `lux_diff` = lux - lux_previous

**Rolling Features:**
- `rolling_mean_power_5` (5-sample rolling mean)
- `rolling_mean_lux_5` (5-sample rolling mean)

### Step 4: Label Creation

For each reading at time `t`:
1. Calculate target timestamp: `t + horizon_minutes`
2. Search for reading within `±tolerance_seconds` of target
3. Use closest match's power value as `target_power_t_plus_15`
4. Drop rows without valid future labels

**No data leakage:** Only past/current values used for features.

### Step 5: Export

**CSV Format:**
```csv
ts,hour,minute,day_of_week,servo_angle,temperature,humidity,lux,voltage,current,power,fan_on,power_diff,lux_diff,rolling_mean_power_5,rolling_mean_lux_5,target_power_t_plus_15
2026-02-24 06:15:00+0530,6,15,0,45.2,27.3,82.1,5430.0,2.34,0.125,0.29,0,0.0,0.0,0.29,5430.0,1.45
```

### Step 6: Report Generation

**JSON Report Includes:**
- Row counts at each pipeline stage
- Dropped row statistics
- Timestamp range
- Missing value counts
- Power/Lux/Temperature statistics
- Label match failure count

## Example Usage Scenarios

### Scenario 1: Quick Dataset for Testing
```bash
# Generate 1 day of data for quick model testing
python tools/build_dataset.py --days 1 --out_csv data/test_dataset.csv
```

### Scenario 2: Production Training Dataset
```bash
# Generate 30 days of data with strict matching
python tools/build_dataset.py \
  --days 30 \
  --horizon_minutes 15 \
  --tolerance_seconds 15 \
  --out_csv data/training_30d.csv \
  --out_parquet data/training_30d.parquet \
  --verbose
```

### Scenario 3: Multiple Devices
```bash
# Build datasets for different solar trackers
python tools/build_dataset.py --device_id tracker01 --days 7 --out_csv data/tracker01.csv
python tools/build_dataset.py --device_id tracker02 --days 7 --out_csv data/tracker02.csv
```

### Scenario 4: Different Prediction Horizons
```bash
# 5-minute ahead prediction
python tools/build_dataset.py --horizon_minutes 5 --out_csv data/5min_horizon.csv

# 30-minute ahead prediction
python tools/build_dataset.py --horizon_minutes 30 --out_csv data/30min_horizon.csv
```

## Using the Dataset for ML Training

### Load Dataset
```python
import pandas as pd

# Load CSV
df = pd.read_csv('data/solar_dataset.csv')

# Or load Parquet (faster for large datasets)
df = pd.read_parquet('data/solar_dataset.parquet')
```

### Prepare Features and Target
```python
# Feature columns
feature_cols = [
    'hour', 'minute', 'day_of_week',
    'servo_angle', 'temperature', 'humidity',
    'lux', 'voltage', 'current', 'power',
    'fan_on',
    'power_diff', 'lux_diff',
    'rolling_mean_power_5', 'rolling_mean_lux_5'
]

# Target column
target_col = 'target_power_t_plus_15'

# Split features and target
X = df[feature_cols]
y = df[target_col]
```

### Train-Test Split
```python
from sklearn.model_selection import train_test_split

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, shuffle=False  # Use shuffle=False for time series
)
```

### Train Model
```python
from sklearn.ensemble import RandomForestRegressor

model = RandomForestRegressor(n_estimators=100, random_state=42)
model.fit(X_train, y_train)
```

## Troubleshooting

### No data fetched
**Issue:** `No documents found matching criteria`

**Solutions:**
- Check device_id matches your MongoDB data
- Verify date range has data (--days parameter)
- Check MongoDB connection string
- Ensure readings_raw collection exists

### All data filtered out
**Issue:** `All data was filtered out during cleaning`

**Solutions:**
- Check status field values (should be "online", not "ok")
- Verify sensor values are in valid ranges
- Use --verbose flag to see detailed filtering logs

### No valid labels
**Issue:** `No valid labels could be created`

**Solutions:**
- Increase --tolerance_seconds (e.g., 60 or 120)
- Ensure data spans at least horizon_minutes duration
- Check for gaps in your time series data

### Missing pyarrow
**Issue:** `pyarrow not installed. Skipping Parquet export.`

**Solution:**
```bash
pip install pyarrow>=14.0.0
```

## Data Quality Checks

After building, review the report:

```bash
cat data/dataset_report.json
```

**Good indicators:**
- `rows_after_labeling` > 80% of `rows_after_cleaning`
- `label_match_failures` < 20%
- No excessive missing values
- Power stats show reasonable range (0-15W for your panel)

**Warning signs:**
- High label_match_failures (increase tolerance or check data gaps)
- Most data dropped during cleaning (review status field values)
- Very low row count (increase --days parameter)

## Integration with ML Service

Once dataset is built:

1. **Copy CSV to backend:**
   ```bash
   cp data/solar_dataset.csv Backend/data/
   ```

2. **Train model via API:**
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

3. **Or train from file:**
   ```python
   import requests
   
   with open('data/solar_dataset.csv', 'rb') as f:
       files = {'file': ('dataset.csv', f, 'text/csv')}
       response = requests.post(
           'http://localhost:8000/api/ml/train',
           files=files,
           data={'model_type': 'random_forest'}
       )
   ```

## Performance Tips

1. **For large datasets** (>1M rows):
   - Use Parquet format (faster I/O)
   - Increase MongoDB timeout settings
   - Consider date range splitting

2. **For faster processing:**
   - Disable rolling features if not needed
   - Use larger tolerance_seconds
   - Filter by specific date ranges

3. **For better quality:**
   - Use smaller tolerance_seconds (stricter matching)
   - Increase --days for more training data
   - Enable --verbose to monitor data quality

## Next Steps

After building dataset:

1. ✅ Review data quality report
2. ✅ Inspect CSV in spreadsheet or pandas
3. ✅ Train ML model (see ML_INTEGRATION_GUIDE.md)
4. ✅ Evaluate predictions
5. ✅ Deploy model via ML service API

## Support

For issues or questions:
- Check logs with --verbose flag
- Review dataset_report.json for data quality metrics
- Verify MongoDB connection and data format
- Ensure simulator status field uses correct enum values ("onlin", not "ok")

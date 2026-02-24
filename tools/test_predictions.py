"""
Quick test script to make predictions with trained model

Usage:
    python test_predictions.py
"""

import joblib
import pandas as pd
import json
from pathlib import Path

# Load latest model
models_dir = Path("../models")
with open(models_dir / "latest_randomforest.json") as f:
    latest = json.load(f)

model_path = models_dir / latest['model_file']
print(f"Loading model: {latest['model_file']}")
model = joblib.load(model_path)

# Load test data - get daytime samples with power > 1W
df = pd.read_csv("../data/solar_dataset.csv")
daytime = df[df['power'] > 1.0]
if len(daytime) >= 10:
    test_samples = daytime.sample(n=10, random_state=42).sort_values('ts')
else:
    test_samples = df.tail(10)

# Feature columns
features = [
    'hour', 'minute', 'day_of_week',
    'servo_angle', 'temperature', 'humidity', 'lux',
    'voltage', 'current', 'power',
    'fan_on', 'power_diff', 'lux_diff',
    'rolling_mean_power_5', 'rolling_mean_lux_5'
]

X_test = test_samples[features]
y_actual = test_samples['target_power_t_plus_15']

# Make predictions
predictions = model.predict(X_test)

# Display results
print("\n" + "="*80)
print("SOLAR POWER PREDICTIONS - 15 Minutes Ahead")
print("="*80)
print(f"{'Time':<8} {'Current':>8} {'Predicted':>10} {'Actual':>10} {'Error':>10}")
print("-"*80)

for idx, (pred, actual) in enumerate(zip(predictions, y_actual)):
    row = test_samples.iloc[idx]
    current_power = row['power']
    error = abs(pred - actual)
    time_str = f"{int(row['hour']):02d}:{int(row['minute']):02d}"
    
    print(f"{time_str:<8} {current_power:>8.2f}W {pred:>9.2f}W {actual:>9.2f}W {error:>9.3f}W")

print("="*80)
print(f"✅ Model loaded and tested successfully!")
print(f"Model version: {latest['version']}")

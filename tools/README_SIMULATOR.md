# Sri Lanka Solar Tracker IoT Data Simulator

## Overview

Production-quality Python script that generates realistic solar tracker sensor readings for Sri Lankan tropical climate conditions. Designed for training ML models and testing the Solar Monitoring System backend.

## Features

### ✅ Realistic Sri Lankan Climate Modeling
- **Timezone**: Asia/Colombo (UTC+5:30)
- **Daylight**: Sunrise ~06:00, Sunset ~18:00
- **Temperature**: 24-27°C (night), 30-36°C (day)
- **Humidity**: 60-90% (tropical high humidity)
- **Irradiance**: Realistic daily curves with cloud events

### ✅ Advanced Physics Simulation
- **PV Power Model**: Temperature-dependent efficiency loss
- **Single-axis Tracking**: East-west servo angle (30-160°)
- **Cloud Events**: Random intensity and duration based on weather mode
- **Smooth Transitions**: No sudden jumps in sensor values
- **Atmospheric Effects**: Small-scale turbulence and variations

### ✅ Multiple Weather Modes

| Mode | Peak Lux | Cloud Probability | Description |
|------|----------|-------------------|-------------|
| `clear` | 95-110k | Low (2%) | Bright sunny day |
| `partly_cloudy` | 70-90k | Medium (8%) | Intermittent clouds |
| `monsoon` | 40-70k | High (15%) | Heavy overcast |

### ✅ Production Features
- **Network Resilience**: Retry logic with exponential backoff
- **Error Handling**: Graceful degradation if backend is down
- **Configurable**: CLI arguments for all parameters
- **Logging**: Structured logs with progress tracking
- **Statistics**: Success rate and summary reporting

## Installation

### Prerequisites

```bash
# Required Python packages
pip install requests
pip install pytz  # Optional but recommended for timezone support
```

### Quick Install

```bash
cd "e:\Solar Tracker\tools"
pip install -r requirements_simulator.txt  # If you create one
```

## Usage

### Basic Examples

#### 1. Simulate 1 clear day (10-second intervals)

```bash
python simulate_solar_sl.py --days 1 --mode clear --interval_sec 10
```

#### 2. Simulate 3 monsoon days (5-second intervals)

```bash
python simulate_solar_sl.py --days 3 --mode monsoon --interval_sec 5
```

#### 3. Partly cloudy day with custom device ID

```bash
python simulate_solar_sl.py --device_id tracker02 --days 1 --mode partly_cloudy
```

#### 4. High-frequency data collection (1-second intervals)

```bash
python simulate_solar_sl.py --days 1 --interval_sec 1 --mode clear
```

### Advanced Usage

#### Start from Specific Date/Time

```bash
python simulate_solar_sl.py \
  --days 2 \
  --start_date "2026-01-15 06:00:00" \
  --mode partly_cloudy
```

#### Change Backend URL

```bash
python simulate_solar_sl.py \
  --base_url http://192.168.1.100:8000 \
  --days 1
```

#### Verbose Debug Logging

```bash
python simulate_solar_sl.py --days 1 --verbose
```

### Full Command Reference

```bash
python simulate_solar_sl.py \
  --device_id tracker01 \
  --base_url http://127.0.0.1:8000 \
  --interval_sec 10 \
  --days 1 \
  --mode clear \
  --start_date "2026-02-23 06:00:00" \
  --verbose
```

## CLI Arguments

| Argument | Type | Default | Description |
|----------|------|---------|-------------|
| `--device_id` | str | `tracker01` | Device identifier |
| `--base_url` | str | `http://127.0.0.1:8000` | FastAPI backend URL |
| `--interval_sec` | float | `10.0` | Seconds between readings |
| `--days` | int | `1` | Number of days to simulate |
| `--mode` | str | `clear` | Weather mode (clear/partly_cloudy/monsoon) |
| `--start_date` | str | `now` | Start datetime ("YYYY-MM-DD HH:MM:SS") |
| `--verbose` | flag | `false` | Enable debug logging |

## Data Schema

Each reading posted to `/api/readings`:

```json
{
  "device_id": "tracker01",
  "timestamp": "2026-02-23T12:30:45+05:30",
  "servo_angle": 92.3,
  "temperature": 33.5,
  "humidity": 68.2,
  "lux": 98500.0,
  "voltage": 14.25,
  "current": 0.842,
  "power": 12.00,
  "fan_status": "OFF",
  "status": "ok"
}
```

### Field Descriptions

- **device_id**: Device identifier string
- **timestamp**: ISO 8601 datetime with timezone
- **servo_angle**: Servo position in degrees (30-160°)
- **temperature**: Panel temperature in °C (24-40°C)
- **humidity**: Relative humidity percentage (60-90%)
- **lux**: Light intensity (0-110,000 lux)
- **voltage**: PV output voltage (0-18V)
- **current**: PV output current (0-1.2A)
- **power**: Electrical power output (0-12W)
- **fan_status**: "ON" or "OFF" (with hysteresis at 38-40°C)
- **status**: "ok" or "invalid" (1% invalid for testing)

## Physics Models

### Solar Irradiance

Uses Gaussian-like daily curve:
- Sunrise transition: 05:30-06:30
- Peak: 12:00 (solar noon)
- Sunset transition: 17:30-18:30

### Cloud Events

Random cloud passages with:
- **Duration**: 2-25 minutes (mode-dependent)
- **Intensity**: 10-85% reduction (mode-dependent)
- **Smooth edges**: Sine wave transition

### PV Power Output

Simplified PV model:

```
Irradiance (W/m²) ≈ (lux / 100,000) × 1000

Voltage = Voc × (1 + temp_coeff × ΔT) × (Irr / 1000) × 0.80
Current = Isc × (Irr / 1000)
Power = V × I × Fill_Factor

Where:
- Voc = 18V (open circuit voltage at 25°C)
- Isc = 1A (short circuit current at 1000 W/m²)
- temp_coeff = -0.4% per °C
- Fill_Factor = 0.75
```

Temperature efficiency loss: Power decreases ~0.4% per °C above 25°C

### Servo Tracking

Single-axis east-west tracking:

```
Hour Angle = (Hour - 12) × 15°
Servo Angle = 90° + (Hour Angle × 0.5)

Morning (06:00): ~45°
Noon (12:00): ~90°
Evening (18:00): ~135°
```

Small Gaussian noise (σ=0.5°) simulates mechanical imperfections.

## Output Examples

### Startup Output

```
======================================================================
Sri Lanka Solar Tracker Simulator - Starting
======================================================================
Device ID:     tracker01
Weather Mode:  clear
Interval:      10 seconds
Duration:      1 days
Start Time:    2026-02-23 06:00:00 +0530
Backend URL:   http://127.0.0.1:8000/api/readings
======================================================================
Will generate ~8,640 readings

Progress: 100/8,640 readings | Success rate: 100.0% | Time: 2026-02-23 06:16:40
Progress: 200/8,640 readings | Success rate: 100.0% | Time: 2026-02-23 06:33:20
...
```

### Debug Log Sample (--verbose)

```
2026-02-23 12:30:45 | DEBUG    | ✓ Posted reading | Device: tracker01 | Power: 11.85W | Lux: 105230.0
2026-02-23 12:30:55 | DEBUG    | ✓ Posted reading | Device: tracker01 | Power: 11.92W | Lux: 106540.0
2026-02-23 12:31:05 | WARNING  | ⚠ Timeout posting reading (attempt 1)
2026-02-23 12:31:15 | DEBUG    | ✓ Posted reading | Device: tracker01 | Power: 11.78W | Lux: 104120.0
```

### Summary Output

```
======================================================================
Simulation Complete
======================================================================
Total readings generated: 8,640
Successfully posted:      8,627
Failed to post:           13
Success rate:             99.85%
======================================================================
```

## Use Cases

### 1. ML Model Training Data

Generate 7 days of clear weather data for training:

```bash
python simulate_solar_sl.py \
  --days 7 \
  --mode clear \
  --interval_sec 300 \
  --start_date "2026-01-01 00:00:00"
```

**Output**: ~2,016 readings (one every 5 minutes for 7 days)

### 2. Testing ML Predictions

Generate real-time data stream for testing:

```bash
python simulate_solar_sl.py \
  --days 1 \
  --interval_sec 10 \
  --mode partly_cloudy
```

### 3. Mixed Weather Testing

Simulate different weather conditions sequentially:

```bash
# Day 1: Clear
python simulate_solar_sl.py --days 1 --mode clear --device_id tracker01

# Day 2: Partly cloudy
python simulate_solar_sl.py --days 1 --mode partly_cloudy --device_id tracker01

# Day 3: Monsoon
python simulate_solar_sl.py --days 1 --mode monsoon --device_id tracker01
```

### 4. Multi-Device Simulation

Simulate multiple trackers in parallel:

```bash
# Terminal 1
python simulate_solar_sl.py --device_id tracker01 --days 1 &

# Terminal 2
python simulate_solar_sl.py --device_id tracker02 --days 1 &

# Terminal 3
python simulate_solar_sl.py --device_id tracker03 --days 1 &
```

### 5. High-Frequency Data Collection

Generate high-resolution data (1 Hz):

```bash
python simulate_solar_sl.py \
  --days 1 \
  --interval_sec 1 \
  --mode clear
```

**Output**: ~86,400 readings per day

## Troubleshooting

### Backend Connection Issues

**Symptom**: `⚠ Connection error` or `✗ Backend appears to be down`

**Solutions**:
1. Verify backend is running: `curl http://127.0.0.1:8000/health`
2. Check base_url: `--base_url http://localhost:8000`
3. Check firewall/network settings
4. The simulator will continue generating data and retry posting

### Timezone Warnings

**Symptom**: `Warning: pytz not installed`

**Solution**:
```bash
pip install pytz
```

Without pytz, the script falls back to UTC+5:30 offset (still works correctly).

### Memory Issues (Long Simulations)

**Symptom**: High memory usage for multi-day simulations

**Solution**: The script streams data and doesn't store history, so memory usage should be minimal. If issues persist, reduce `--interval_sec` or split into multiple runs.

### Invalid Readings

**Symptom**: Some readings have `"status": "invalid"`

**Expected Behavior**: By design, 1% of readings are marked invalid to test error handling. This is normal.

## Performance

### Timing Estimates

| Duration | Interval | Total Readings | Runtime |
|----------|----------|----------------|---------|
| 1 day | 10 sec | ~8,640 | ~24 hours (real-time) |
| 1 day | 1 sec | ~86,400 | ~24 hours (real-time) |
| 7 days | 5 min | ~2,016 | 10,080 min (~7 days real-time) |

**Note**: Simulation runs in real-time by default. For faster-than-real-time, the backend must keep up with the posting rate.

### Network Throughput

- **POST request**: ~50-100ms per reading (local network)
- **Max throughput**: ~10-20 readings/second (limited by network and backend)
- **Retry overhead**: 3 retry attempts with 1-second backoff

## Technical Details

### Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  SolarTrackerSimulator                       │
│                                                               │
│  ┌────────────────────┐       ┌────────────────────┐        │
│  │ SensorSimulator    │       │    APIClient       │        │
│  │                    │       │                    │        │
│  │ - Lux calculation  │       │ - POST request     │        │
│  │ - Temperature      │──────▶│ - Retry logic      │───────▶│ Backend
│  │ - Humidity         │       │ - Error handling   │        │
│  │ - PV model         │       │ - Statistics       │        │
│  └────────────────────┘       └────────────────────┘        │
│           │                                                   │
│           │                                                   │
│  ┌────────▼───────────┐                                      │
│  │  CloudSimulator    │                                      │
│  │                    │                                      │
│  │ - Event generation │                                      │
│  │ - Intensity calc   │                                      │
│  │ - Smooth edges     │                                      │
│  └────────────────────┘                                      │
└─────────────────────────────────────────────────────────────┘
```

### Dependencies

- **requests**: HTTP client with retry support
- **pytz** (optional): Timezone support
- Standard library: argparse, json, logging, math, random, datetime, dataclasses, enum

### Code Quality

- ✅ Type hints throughout
- ✅ Dataclasses for configuration
- ✅ Comprehensive docstrings
- ✅ Structured logging
- ✅ Error handling
- ✅ Clean separation of concerns
- ✅ Configurable parameters
- ✅ Production-ready

## Integration with Backend

### Expected Backend Endpoint

```
POST /api/readings
Content-Type: application/json

Body: {sensor reading JSON}
```

### Expected Response

```json
{
  "success": true,
  "message": "Reading stored successfully",
  "device_id": "tracker01",
  "timestamp": "2026-02-23T12:30:45+05:30",
  "inserted_id": "699c796dde15ec1e5c6c7797"
}
```

### Error Handling

The simulator handles:
- **Network timeouts**: Retries with backoff
- **Connection errors**: Logs warning, continues
- **HTTP errors**: Logs error, continues
- **Backend downtime**: Accumulates statistics, continues generating

## Future Enhancements

Potential additions:
- [ ] Real-time plotting (matplotlib)
- [ ] Export to CSV alongside posting
- [ ] WebSocket support for streaming
- [ ] Multiple device orchestration
- [ ] Configurable panel characteristics
- [ ] Historical weather data import
- [ ] Anomaly injection (sensor failures, shading)

## License

Part of the Solar Monitoring System project.

---

**Version**: 1.0.0  
**Last Updated**: 2026-02-23  
**Status**: Production Ready ✅

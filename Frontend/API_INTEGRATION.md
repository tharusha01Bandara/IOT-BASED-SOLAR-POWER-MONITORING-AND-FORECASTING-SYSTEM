# API Integration Guide

## Overview

The Solar Tracker frontend is now fully wired to your FastAPI backend! The application automatically connects to the backend on startup and falls back to demo mode if the backend is unavailable.

## Architecture

### API Client Layer (`src/api/`)

#### `client.ts` - Core HTTP Client
- Implements retry logic (2 retries by default)
- Request timeout handling (10 seconds)
- Automatic error handling and normalization
- Type-safe GET/POST methods
- Health check functionality

#### `endpoints.ts` - API Endpoint Functions
- `getLatestReading(deviceId)` - Fetch latest sensor data
- `getLatestPrediction(deviceId)` - Fetch ML prediction
- `getReadingHistory(deviceId, minutes)` - Fetch time-series data
- `getModelStatus(deviceId)` - Get ML model info
- `checkBackendHealth()` - Backend health check

All endpoints include:
- Response normalization
- Field validation with fallback values
- Proper error handling

### Data Fetching (`src/hooks/useSolarData.ts`)

#### Features Implemented:

1. **Auto-connect on Load**
   - Health check on mount
   - Automatic backend connection
   - Graceful fallback to demo mode

2. **Live Updates**
   - Fetches data every 10 seconds (configurable)
   - Pause/Resume functionality
   - Manual refresh button

3. **Device Switching**
   - Supports multiple devices (tracker01, tracker02)
   - Re-fetches data when device changes

4. **Error Handling**
   - Network errors trigger demo mode
   - Error messages shown in UI
   - No crashes on missing fields

5. **Alert Generation**
   - Temperature > 40°C → Overheat warning
   - Lux < 20,000 (daytime) → Low sunlight
   - Predicted power drop → Power alert
   - status !== 'ok' → Sensor error

### UI Components

#### Updated Components:

1. **AppLayout** - Added:
   - Demo mode banner
   - Error banner
   - Device selector state

2. **TopBar** - Added:
   - Device change handler
   - Demo mode indicator
   - Backend connection status (colored dot)

3. **Overview Page** - Added:
   - Voltage and Current KPI cards
   - Loading skeletons
   - LDR sensor data to ServoGauge

4. **ServoGauge** - Added:
   - LDR Left/Right bars
   - Auto-hide if data unavailable

## API Endpoints Expected

### Backend must provide:

```
GET /api/readings/latest?device_id=tracker01
→ Returns latest sensor reading

GET /api/prediction/latest?device_id=tracker01
→ Returns latest ML prediction

GET /api/readings/history?device_id=tracker01&minutes=60
→ Returns array of historical readings

GET /api/ml/status?device_id=tracker01
→ Returns model status and metrics

GET /api/health
→ Returns backend health status
```

### Expected Response Formats:

#### Reading Response:
```json
{
  "device_id": "tracker01",
  "timestamp": "2026-02-27T10:30:00Z",
  "power": 245.5,
  "voltage": 12.3,
  "current": 19.9,
  "lux": 42000,
  "temperature": 38.5,
  "humidity": 62,
  "servo_angle": 95,
  "fan_status": true,
  "status": "ok",
  "ldr_left": 512,
  "ldr_right": 498
}
```

#### Prediction Response:
```json
{
  "predicted_power_15min": 238.2,
  "confidence": 0.92,
  "timestamp": "2026-02-27T10:45:00Z",
  "model_version": "v1.2"
}
```

## Configuration

### Environment Variables

Create `Frontend/.env`:
```env
VITE_API_URL=http://localhost:8000
```

### Runtime Config (`src/lib/config.ts`)

```typescript
{
  apiUrl: 'http://localhost:8000',
  apiTimeout: 10000,      // 10 seconds
  refreshInterval: 10000,  // 10 seconds
  maxRetries: 2,
  retryDelay: 1000        // 1 second
}
```

## Demo Mode

### When Demo Mode Activates:

1. Backend health check fails on startup
2. API request fails (network error, timeout)
3. No data available in database

### Demo Mode Features:

- Shows amber "DEMO" badge in top bar
- Displays warning banner with reason
- Uses realistic mock data
- All UI features work normally
- Faster refresh rate (7 seconds)

### Exiting Demo Mode:

- Backend becomes available
- Successful API call
- Automatic reconnection on next refresh

## Field Mapping

### Backend → Frontend

| Backend Field | Frontend Field | Notes |
|--------------|----------------|-------|
| `power` | `power` | Direct mapping |
| `voltage` | `voltage` | Direct mapping |
| `current` | `current` | Direct mapping |
| `lux` | `lux` | Direct mapping |
| `temperature` | `temperature` | Direct mapping |
| `humidity` | `humidity` | Direct mapping |
| `servo_angle` | `servo_angle` | 0–180° |
| `fan_status` | `fan_status` | Boolean |
| `ldr_left` | `ldr_left` | Optional, 0–1023 |
| `ldr_right` | `ldr_right` | Optional, 0–1023 |
| `status` | `status` | Optional, triggers alert if not "ok" |

### Fallback Values

If a field is missing from the backend:
- Numeric fields → `0`
- Boolean fields → `false`
- Timestamp → Current time
- status → `"ok"`

## Testing

### With Backend Running:

1. Start Backend:
   ```powershell
   cd Backend
   .\run.ps1
   ```

2. Start Frontend:
   ```powershell
   cd Frontend
   npm run dev
   ```

3. Open: http://localhost:8080

### Without Backend:

Frontend automatically enters demo mode and shows simulated data.

## Error Handling

### Network Errors:
- Shown in red alert banner
- Fallback to demo mode
- Retry on next refresh

### Validation Errors:
- Missing fields use fallback values
- Logs errors to console
- UI never crashes

### Timeout Errors:
- 10-second timeout per request
- Automatic retry (2 attempts)
- Exponential backoff

## Performance

- Parallel data fetching (reading + prediction)
- Efficient re-rendering with React hooks
- Debounced time range changes
- Optimistic UI updates

## Security Notes

- CORS must be enabled on backend
- No sensitive data in frontend
- API errors don't expose backend details
- Proper TypeScript validation

## Browser Support

- Modern browsers (Chrome, Firefox, Edge, Safari)
- ES2020+ features required
- Fetch API required

---

**Status:** ✅ Fully Integrated

**Demo Mode:** ✅ Auto-fallback

**Real-time Updates:** ✅ 10-second refresh

**Error Resilience:** ✅ Never crashes

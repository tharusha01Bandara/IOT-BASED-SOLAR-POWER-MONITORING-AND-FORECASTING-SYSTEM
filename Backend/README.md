# Solar Monitoring System - Backend API

Production-ready FastAPI backend for IoT-based Solar Tracker Monitoring System. This application receives sensor data from ESP32 devices, stores it in MongoDB, and provides RESTful APIs for data retrieval and analytics.

## Features

✅ **FastAPI Framework** with async/await support  
✅ **MongoDB** with connection pooling and indexing  
✅ **Pydantic** data validation  
✅ **Clean Architecture** with separation of concerns  
✅ **Dependency Injection** pattern  
✅ **Structured Logging** with JSON support  
✅ **CORS** middleware configured  
✅ **Error Handling** with structured responses  
✅ **Health Check** endpoints  
✅ **Environment-based Configuration**  
✅ **API Documentation** (Swagger/ReDoc)

## Project Structure

```
Solar Tracker/
├── app/
│   ├── __init__.py
│   ├── main.py                    # FastAPI application entry point
│   ├── core/
│   │   ├── __init__.py
│   │   ├── config.py              # Configuration management
│   │   └── logging.py             # Logging setup
│   ├── db/
│   │   ├── __init__.py
│   │   └── mongodb.py             # MongoDB connection & pooling
│   ├── models/
│   │   ├── __init__.py
│   │   └── reading.py             # Database models & helpers
│   ├── schemas/
│   │   ├── __init__.py
│   │   └── readings.py            # Pydantic schemas
│   ├── services/
│   │   ├── __init__.py
│   │   ├── readings_service.py    # Business logic for readings
│   │   └── predictions_service.py # Business logic for predictions
│   └── routers/
│       ├── __init__.py
│       ├── readings.py            # Readings API endpoints
│       ├── predictions.py         # Predictions API endpoints
│       └── health.py              # Health check endpoints
├── .env.example                   # Example environment variables
├── .gitignore
├── requirements.txt               # Python dependencies
└── README.md                      # This file
```

## Requirements

- **Python**: 3.11 or higher
- **MongoDB**: 4.4 or higher
- **Operating System**: Windows, Linux, macOS

## Installation

### 1. Clone or Download the Project

```powershell
cd "e:\Solar Tracker"
```

### 2. Create Virtual Environment

```powershell
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On Windows PowerShell:
.\venv\Scripts\Activate.ps1

# On Windows CMD:
.\venv\Scripts\activate.bat

# On Linux/macOS:
source venv/bin/activate
```

### 3. Install Dependencies

```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Install and Setup MongoDB

**Option A: Local MongoDB Installation**

1. Download MongoDB Community Server from [mongodb.com](https://www.mongodb.com/try/download/community)
2. Install and start MongoDB service
3. Default connection: `mongodb://localhost:27017`

**Option B: MongoDB Atlas (Cloud)**

1. Create free account at [mongodb.com/atlas](https://www.mongodb.com/cloud/atlas)
2. Create a cluster and get connection string
3. Use connection string in `.env` file

**Option C: MongoDB with Docker**

```powershell
docker run -d -p 27017:27017 --name mongodb mongo:latest
```

### 5. Configure Environment Variables

Copy the example environment file and configure it:

```powershell
# Copy example file
Copy-Item .env.example .env

# Edit .env file with your configuration
notepad .env
```

**Minimum required configuration in `.env`:**

```env
# MongoDB Connection
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=solar_monitoring

# Server Configuration
HOST=0.0.0.0
PORT=8000
DEBUG=True
LOG_LEVEL=INFO

# CORS (add your frontend URL)
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

## Running the Application

### Development Mode (with auto-reload)

```powershell
# Method 1: Using Python directly
python -m app.main

# Method 2: Using uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Production Mode

```powershell
# Using uvicorn with multiple workers
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Using Environment Variables Directly

```powershell
$env:HOST="0.0.0.0"
$env:PORT="8000"
$env:DEBUG="False"
python -m app.main
```

## API Endpoints

### Base URL
```
http://localhost:8000
```

### API Documentation
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

### Endpoints Overview

#### 1. Health Check
```http
GET /api/health
GET /api/health/ping
```

#### 2. Store Sensor Reading
```http
POST /api/readings
Content-Type: application/json

{
  "device_id": "tracker01",
  "timestamp": "2026-02-23T10:30:00Z",
  "servo_angle": 45.5,
  "temperature": 28.3,
  "humidity": 65.2,
  "lux": 5420.0,
  "voltage": 18.5,
  "current": 2.3,
  "power": 42.55,
  "fan_status": "auto",
  "status": "online"
}
```

#### 3. Get Latest Reading
```http
GET /api/readings/latest?device_id=tracker01
```

#### 4. Get Reading History
```http
GET /api/readings/history?device_id=tracker01&minutes=60
```

#### 5. Get Device Statistics
```http
GET /api/readings/statistics?device_id=tracker01&minutes=60
```

#### 6. Get Latest Prediction
```http
GET /api/prediction/latest?device_id=tracker01
```

#### 7. Get Prediction History
```http
GET /api/prediction/history?device_id=tracker01&limit=100
```

## Testing the API

### Using cURL

```powershell
# Health check
curl http://localhost:8000/api/health

# Post a reading
curl -X POST http://localhost:8000/api/readings `
  -H "Content-Type: application/json" `
  -d '{
    "device_id": "tracker01",
    "timestamp": "2026-02-23T10:30:00Z",
    "servo_angle": 45.5,
    "temperature": 28.3,
    "humidity": 65.2,
    "lux": 5420.0,
    "voltage": 18.5,
    "current": 2.3,
    "power": 42.55,
    "fan_status": "auto",
    "status": "online"
  }'

# Get latest reading
curl "http://localhost:8000/api/readings/latest?device_id=tracker01"
```

### Using PowerShell (Invoke-RestMethod)

```powershell
# Health check
Invoke-RestMethod -Uri "http://localhost:8000/api/health"

# Post a reading
$reading = @{
    device_id = "tracker01"
    timestamp = "2026-02-23T10:30:00Z"
    servo_angle = 45.5
    temperature = 28.3
    humidity = 65.2
    lux = 5420.0
    voltage = 18.5
    current = 2.3
    power = 42.55
    fan_status = "auto"
    status = "online"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/readings" `
    -Method POST `
    -Body $reading `
    -ContentType "application/json"

# Get latest reading
Invoke-RestMethod -Uri "http://localhost:8000/api/readings/latest?device_id=tracker01"
```

### Using Python Requests

```python
import requests
from datetime import datetime

# API base URL
BASE_URL = "http://localhost:8000/api"

# Post a reading
reading = {
    "device_id": "tracker01",
    "timestamp": datetime.utcnow().isoformat() + "Z",
    "servo_angle": 45.5,
    "temperature": 28.3,
    "humidity": 65.2,
    "lux": 5420.0,
    "voltage": 18.5,
    "current": 2.3,
    "power": 42.55,
    "fan_status": "auto",
    "status": "online"
}

response = requests.post(f"{BASE_URL}/readings", json=reading)
print(response.json())

# Get latest reading
response = requests.get(f"{BASE_URL}/readings/latest?device_id=tracker01")
print(response.json())
```

## MongoDB Collections

### 1. readings_raw
Stores raw sensor data from ESP32 devices.

**Indexes:**
- `device_id` + `timestamp` (compound, descending)
- `timestamp` (descending)

**Document Structure:**
```json
{
  "_id": ObjectId("..."),
  "device_id": "tracker01",
  "timestamp": ISODate("2026-02-23T10:30:00Z"),
  "servo_angle": 45.5,
  "temperature": 28.3,
  "humidity": 65.2,
  "lux": 5420.0,
  "voltage": 18.5,
  "current": 2.3,
  "power": 42.55,
  "fan_status": "auto",
  "status": "online",
  "created_at": ISODate("2026-02-23T10:30:00Z")
}
```

### 2. predictions
Stores ML model predictions.

**Indexes:**
- `device_id` + `timestamp` (compound, descending)

**Document Structure:**
```json
{
  "_id": ObjectId("..."),
  "device_id": "tracker01",
  "timestamp": ISODate("2026-02-23T11:00:00Z"),
  "predicted_power": 45.2,
  "predicted_angle": 50.0,
  "confidence": 0.92,
  "model_version": "v1.0.0",
  "created_at": ISODate("2026-02-23T11:00:00Z")
}
```

## Configuration

### Environment Variables

| Variable | Description | Default | Required |
|----------|-------------|---------|----------|
| `APP_NAME` | Application name | Solar Monitoring System | No |
| `APP_VERSION` | Application version | 1.0.0 | No |
| `DEBUG` | Debug mode | False | No |
| `LOG_LEVEL` | Logging level | INFO | No |
| `HOST` | Server host | 0.0.0.0 | No |
| `PORT` | Server port | 8000 | No |
| `MONGODB_URL` | MongoDB connection URL | mongodb://localhost:27017 | Yes |
| `MONGODB_DB_NAME` | Database name | solar_monitoring | Yes |
| `MONGODB_MAX_POOL_SIZE` | Max connection pool size | 50 | No |
| `MONGODB_MIN_POOL_SIZE` | Min connection pool size | 10 | No |
| `COLLECTION_READINGS` | Readings collection name | readings_raw | No |
| `COLLECTION_PREDICTIONS` | Predictions collection name | predictions | No |
| `CORS_ORIGINS` | Allowed CORS origins (comma-separated) | http://localhost:3000 | No |
| `API_V1_PREFIX` | API route prefix | /api | No |
| `MAX_QUERY_MINUTES` | Maximum query time range | 10080 | No |

### Logging Levels

- `DEBUG`: Detailed information for debugging
- `INFO`: General informational messages (default)
- `WARNING`: Warning messages
- `ERROR`: Error messages
- `CRITICAL`: Critical error messages

## Error Handling

All API endpoints return structured error responses:

```json
{
  "success": false,
  "error": "ErrorType",
  "message": "Human-readable error message",
  "details": {},
  "timestamp": "2026-02-23T10:30:00Z"
}
```

### HTTP Status Codes

- `200 OK`: Success
- `201 Created`: Resource created successfully
- `400 Bad Request`: Invalid request data
- `404 Not Found`: Resource not found
- `422 Unprocessable Entity`: Validation error
- `500 Internal Server Error`: Server error

## Production Deployment

### Using Gunicorn + Uvicorn

```powershell
pip install gunicorn

gunicorn app.main:app `
    --workers 4 `
    --worker-class uvicorn.workers.UvicornWorker `
    --bind 0.0.0.0:8000 `
    --access-logfile - `
    --error-logfile -
```

### Using Docker

Create `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

ENV PYTHONUNBUFFERED=1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Build and run:

```powershell
docker build -t solar-monitoring-api .
docker run -d -p 8000:8000 --env-file .env solar-monitoring-api
```

### Production Checklist

- [ ] Set `DEBUG=False` in production
- [ ] Use strong MongoDB authentication
- [ ] Configure proper CORS origins
- [ ] Set up HTTPS/TLS (use reverse proxy like Nginx)
- [ ] Enable MongoDB authentication and encryption
- [ ] Set up monitoring and logging aggregation
- [ ] Configure rate limiting (use FastAPI Rate Limiter)
- [ ] Set up backup strategy for MongoDB
- [ ] Use environment-specific `.env` files
- [ ] Consider using managed MongoDB service (Atlas)

## Troubleshooting

### MongoDB Connection Failed

```
Error: Could not connect to MongoDB
```

**Solution:**
1. Verify MongoDB is running: `mongosh` or `mongo`
2. Check MongoDB URL in `.env` file
3. Verify firewall rules allow connection
4. Check MongoDB logs for errors

### Port Already in Use

```
Error: [Errno 10048] Only one usage of each socket address
```

**Solution:**
```powershell
# Find process using the port
netstat -ano | findstr :8000

# Kill the process (replace PID with actual process ID)
taskkill /F /PID <PID>
```

### Module Import Errors

```
ModuleNotFoundError: No module named 'fastapi'
```

**Solution:**
```powershell
# Ensure virtual environment is activated
.\venv\Scripts\Activate.ps1

# Reinstall dependencies
pip install -r requirements.txt
```

### Validation Errors

Check the API documentation at `/docs` for exact request format requirements.

## Performance Optimization

### Database Indexes

Indexes are automatically created on application startup:
- Compound index on `device_id` + `timestamp`
- Single index on `timestamp`

### Connection Pooling

MongoDB connection pooling is configured with:
- Max pool size: 50 connections
- Min pool size: 10 connections

Adjust in `.env`:
```env
MONGODB_MAX_POOL_SIZE=100
MONGODB_MIN_POOL_SIZE=20
```

### Query Optimization

- Use the `minutes` parameter wisely in history endpoints
- Default maximum query range is 7 days (10080 minutes)
- Results are limited and paginated for large datasets

## Security Best Practices

1. **Environment Variables**: Never commit `.env` to version control
2. **MongoDB Authentication**: Enable authentication in production
3. **CORS**: Configure specific origins, avoid `*` in production
4. **HTTPS**: Use reverse proxy (Nginx) with SSL/TLS
5. **Rate Limiting**: Implement rate limiting for API endpoints
6. **Input Validation**: Already handled by Pydantic schemas
7. **Error Messages**: Don't expose internal details in production

## Support & Contributing

For issues, questions, or suggestions:
1. Check existing documentation
2. Review error logs
3. Verify MongoDB connection
4. Check API documentation at `/docs`

## License

This project is for educational and commercial use.

## Author

Solar Monitoring System Backend v1.0.0

---

**Last Updated**: February 23, 2026

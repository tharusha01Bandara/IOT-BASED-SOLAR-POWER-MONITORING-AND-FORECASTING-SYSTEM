# Quick Start Guide - Solar Monitoring System Backend

## 🚀 Get Started in 3 Steps

### Step 1: Setup Environment
```powershell
# Navigate to project directory
cd "e:\Solar Tracker"

# Copy environment file
Copy-Item .env.example .env

# Edit .env with your MongoDB connection
notepad .env
```

### Step 2: Install Dependencies
```powershell
# Create and activate virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt
```

### Step 3: Run the Server
```powershell
# Option 1: Using the run script (recommended)
.\run.ps1

# Option 2: Direct Python
python -m app.main

# Option 3: Using uvicorn with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📍 Access Points

| Service | URL |
|---------|-----|
| **API Base** | http://localhost:8000 |
| **Swagger Docs** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |
| **Health Check** | http://localhost:8000/api/health |

## 🧪 Test the API

```powershell
# Run the test script
python test_api.py
```

## 📝 Quick API Examples

### Send a Reading (PowerShell)
```powershell
$reading = @{
    device_id = "tracker01"
    timestamp = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
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
```

### Get Latest Reading
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/readings/latest?device_id=tracker01"
```

### Get History (Last 60 minutes)
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/readings/history?device_id=tracker01&minutes=60"
```

## 🎯 Key Features Implemented

✅ **POST** /api/readings - Store sensor data from ESP32  
✅ **GET** /api/readings/latest - Get latest reading  
✅ **GET** /api/readings/history - Get historical data  
✅ **GET** /api/readings/statistics - Get aggregated stats  
✅ **GET** /api/prediction/latest - Get latest ML prediction  
✅ **GET** /api/health - Health check endpoint  

## 🗄️ MongoDB Collections

- **readings_raw**: Stores all sensor readings
- **predictions**: Stores ML model predictions

Collections are auto-indexed for optimal query performance.

## ⚙️ Configuration

Edit `.env` file to configure:

```env
# MongoDB
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=solar_monitoring

# Server
HOST=0.0.0.0
PORT=8000
DEBUG=True

# CORS
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

## 🛠️ Troubleshooting

### MongoDB Connection Failed
- Ensure MongoDB is running: `mongosh`
- Check MONGODB_URL in .env

### Port Already in Use
```powershell
# Find and kill process using port 8000
netstat -ano | findstr :8000
taskkill /F /PID <PID>
```

### Module Not Found
```powershell
# Activate venv and reinstall
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 📚 Full Documentation

See [README.md](README.md) for complete documentation.

## 🎓 Project Structure

```
app/
├── main.py              # FastAPI app entry point
├── core/                # Configuration & logging
├── db/                  # MongoDB connection
├── models/              # Data models
├── schemas/             # Pydantic validation
├── services/            # Business logic
└── routers/             # API endpoints
```

## 💡 Next Steps

1. ✅ Start the server: `.\run.ps1`
2. ✅ Test the API: `python test_api.py`
3. ✅ Check docs: http://localhost:8000/docs
4. ✅ Configure your ESP32 to send data to the API
5. ✅ Build your frontend application

---

**Need help?** Check the [README.md](README.md) or API documentation at `/docs`

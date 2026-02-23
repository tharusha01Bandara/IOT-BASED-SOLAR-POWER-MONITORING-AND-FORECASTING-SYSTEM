# MongoDB Setup Guide for Solar Monitoring System

## Problem
The error "No connection could be made because the target machine actively refused it" means MongoDB is not running on your system.

## Solutions

### Option 1: Install MongoDB Locally (Recommended for Development)

#### Step 1: Download MongoDB
1. Go to https://www.mongodb.com/try/download/community
2. Download MongoDB Community Server for Windows
3. Run the installer (keep default settings)
4. Make sure "Install MongoDB as a Service" is checked

#### Step 2: Start MongoDB Service
```powershell
# Check if MongoDB service is running
Get-Service -Name MongoDB

# Start MongoDB service if stopped
Start-Service -Name MongoDB

# Or use net command
net start MongoDB
```

#### Step 3: Verify MongoDB is Running
```powershell
# Check if MongoDB is listening on port 27017
Test-NetConnection -ComputerName localhost -Port 27017

# Or try connecting with mongo shell
mongosh
```

---

### Option 2: Use MongoDB with Docker (Easiest)

```powershell
# Install Docker Desktop for Windows first
# Then run:

# Start MongoDB container
docker run -d `
  --name mongodb-solar `
  -p 27017:27017 `
  -v mongodb-data:/data/db `
  mongo:latest

# Verify it's running
docker ps

# View logs
docker logs mongodb-solar

# Stop MongoDB
docker stop mongodb-solar

# Start MongoDB again
docker start mongodb-solar
```

---

### Option 3: Use MongoDB Atlas (Cloud - Free Tier Available)

1. Go to https://www.mongodb.com/cloud/atlas/register
2. Create a free account
3. Create a free cluster (M0 tier)
4. Get your connection string
5. Update `.env` file:
   ```env
   MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/solar_monitoring?retryWrites=true&w=majority
   ```

---

## Quick Fix for Local MongoDB

### If MongoDB is installed but not running:

```powershell
# Windows PowerShell (Run as Administrator)
Start-Service -Name MongoDB

# Or
net start MongoDB
```

### If MongoDB is not installed:

#### Quick Install with Chocolatey
```powershell
# Install Chocolatey if you don't have it
# Visit: https://chocolatey.org/install

# Install MongoDB
choco install mongodb

# Start MongoDB
net start MongoDB
```

---

## Verify MongoDB Connection

After starting MongoDB, test the connection:

```powershell
# Test from command line
mongosh --eval "db.adminCommand('ping')"

# Or use Python
python -c "from pymongo import MongoClient; client = MongoClient('mongodb://localhost:27017'); print('MongoDB connected:', client.admin.command('ping'))"
```

---

## Update Your Configuration

Make sure your `.env` file has the correct MongoDB URL:

```env
# For local MongoDB
MONGODB_URL=mongodb://localhost:27017

# For Docker MongoDB
MONGODB_URL=mongodb://localhost:27017

# For MongoDB Atlas
MONGODB_URL=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
```

---

## After MongoDB is Running

Start your FastAPI server:

```powershell
python -m app.main
```

You should see:
```
✅ Successfully connected to MongoDB database: solar_monitoring
✅ Application startup complete
```

---

## Troubleshooting

### Port 27017 is already in use
```powershell
# Find what's using the port
netstat -ano | findstr :27017

# Kill the process
taskkill /F /PID <PID>
```

### MongoDB service won't start
```powershell
# Check MongoDB logs
Get-Content "C:\Program Files\MongoDB\Server\7.0\log\mongod.log" -Tail 50
```

### Connection timeout
- Check if firewall is blocking port 27017
- Verify MongoDB is actually running
- Try connecting to 127.0.0.1 instead of localhost

---

## Next Steps

Once MongoDB is running:

1. Start the API server: `python -m app.main`
2. Access the API docs: http://localhost:8000/docs
3. Test the health endpoint: http://localhost:8000/api/health
4. Run test script: `python test_api.py`

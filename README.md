# IOT-BASED-SOLAR-POWER-MONITORING-AND-FORECASTING-SYSTEM

A comprehensive solar panel monitoring and prediction system with ML-powered analytics.

## Project Structure

```
Solar Tracker/
├── Backend/           # FastAPI backend application
│   ├── app/          # Main application code
│   │   ├── core/     # Configuration and logging
│   │   ├── db/       # Database connections
│   │   ├── models/   # Database models
│   │   ├── routers/  # API endpoints
│   │   ├── schemas/  # Pydantic schemas
│   │   └── services/ # Business logic
│   ├── ml_models/    # Trained ML models
│   ├── tests/        # Test files
│   ├── .env          # Environment configuration
│   ├── requirements.txt
│   ├── run.ps1       # Quick start script
│   └── README.md     # Backend documentation
│
├── Frontend/         # Web frontend (To be implemented)
│   └── README.md     # Frontend documentation
│
└── venv/            # Python virtual environment
```

## Quick Start

### Backend Setup

1. Navigate to the Backend folder:
   ```powershell
   cd Backend
   ```

2. Run the quick start script:
   ```powershell
   .\run.ps1
   ```

   This will:
   - Create/activate virtual environment
   - Install dependencies
   - Start the FastAPI server

3. Access the API:
   - API: http://localhost:8000
   - Interactive Docs: http://localhost:8000/docs
   - Health Check: http://localhost:8000/api/health

### Frontend Setup

Frontend implementation is pending. Check the [Frontend README](Frontend/README.md) for planned features.

## Features

### Backend
- ✅ Real-time solar panel data monitoring
- ✅ RESTful API with FastAPI
- ✅ MongoDB integration
- ✅ ML-powered predictions
- ✅ Data analytics and insights
- ✅ Comprehensive API documentation

### Frontend (Planned)
- 📋 Interactive dashboard
- 📋 Real-time data visualization
- 📋 ML predictions display
- 📋 Historical data analysis

## Documentation

- [Backend Documentation](Backend/README.md)
- [MongoDB Setup Guide](Backend/MONGODB_SETUP.md)
- [ML Integration Guide](Backend/ML_INTEGRATION_GUIDE.md)
- [Quick Start Guide](Backend/QUICKSTART.md)

## Technology Stack

### Backend
- **Framework**: FastAPI
- **Database**: MongoDB
- **ML**: scikit-learn, joblib
- **Language**: Python 3.8+

### Frontend (Planned)
- React/Vue.js/Angular
- Chart libraries
- WebSocket support

## Development

### Running Tests

```powershell
cd Backend
python test_api.py
python test_ml.py
python test_simple.py
```

### Environment Variables

Copy `.env.example` to `.env` in the Backend folder and configure:
- MongoDB connection string
- API settings
- ML model paths

## License

[Add your license information here]

## Contributors

[Add contributors here]

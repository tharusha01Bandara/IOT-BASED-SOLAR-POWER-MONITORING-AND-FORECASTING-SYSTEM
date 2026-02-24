"""
Solar Monitoring System - Main Application

This is the main FastAPI application that ties together all components
of the Solar Monitoring System backend.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pymongo.errors import PyMongoError
import logging

from app.core.config import get_settings
from app.core.logging import setup_logging, get_logger
from app.db.mongodb import mongodb_client
from app.routers import readings, predictions, health, ml, ml_management

# Get application settings
settings = get_settings()

# Setup logging
setup_logging(
    log_level=settings.log_level,
    use_json=not settings.debug  # Use JSON logging in production
)

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown events for the application.
    Establishes database connections on startup and closes them on shutdown.
    """
    # Startup
    logger.info(f"Starting {settings.app_name} v{settings.app_version}")
    logger.info(f"Debug mode: {settings.debug}")
    
    try:
        # Connect to MongoDB
        mongodb_client.connect(settings)
        logger.info("Application startup complete")
        
        yield  # Application runs here
        
    finally:
        # Shutdown
        logger.info("Shutting down application")
        mongodb_client.close()
        logger.info("Application shutdown complete")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Production-ready FastAPI backend for IoT-based Solar Monitoring System. "
        "Handles sensor data ingestion from ESP32 devices and provides analytics APIs."
    ),
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,  # Disable docs in production
    redoc_url="/redoc" if settings.debug else None,
    openapi_url="/openapi.json" if settings.debug else None,
)


# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins_list(),
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.get_cors_methods_list(),
    allow_headers=settings.get_cors_headers_list(),
)


# Custom exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    Handle Pydantic validation errors with detailed error messages.
    
    Returns a structured JSON response with validation error details.
    """
    logger.warning(f"Validation error on {request.url.path}: {exc.errors()}")
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "ValidationError",
            "message": "Request validation failed",
            "details": exc.errors()
        }
    )


@app.exception_handler(PyMongoError)
async def mongodb_exception_handler(request: Request, exc: PyMongoError):
    """
    Handle MongoDB errors globally.
    
    Provides a consistent error response for database errors.
    """
    logger.error(f"MongoDB error on {request.url.path}: {exc}")
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "DatabaseError",
            "message": "A database error occurred. Please try again later."
        }
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Global exception handler for unexpected errors.
    
    Logs the error and returns a generic error response.
    """
    logger.error(f"Unexpected error on {request.url.path}: {exc}", exc_info=True)
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "success": False,
            "error": "InternalServerError",
            "message": "An unexpected error occurred. Please try again later."
        }
    )


# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    Middleware to log all incoming requests.
    
    Logs request method, path, and response status code.
    """
    logger.info(f"Request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    logger.info(
        f"Response: {request.method} {request.url.path} - "
        f"Status: {response.status_code}"
    )
    
    return response


# Include routers with API prefix
app.include_router(
    readings.router,
    prefix=settings.api_v1_prefix
)

app.include_router(
    predictions.router,
    prefix=settings.api_v1_prefix
)

app.include_router(    ml.router,
    prefix=settings.api_v1_prefix
)

app.include_router(
    ml_management.router,
    prefix=settings.api_v1_prefix
)

app.include_router(    health.router,
    prefix=settings.api_v1_prefix
)


# Root endpoint
@app.get(
    "/",
    tags=["root"],
    summary="API root",
    description="Get basic API information"
)
async def root():
    """
    Root endpoint providing API information.
    
    Returns:
        Basic API metadata and available endpoints
    """
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "status": "running",
        "docs": "/docs" if settings.debug else "disabled",
        "endpoints": {
            "health": f"{settings.api_v1_prefix}/health",
            "readings": f"{settings.api_v1_prefix}/readings",
            "predictions": f"{settings.api_v1_prefix}/prediction"
        }
    }


# Main entry point for running with uvicorn
if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting uvicorn server on {settings.host}:{settings.port}")
    
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,  # Auto-reload in debug mode
        log_level=settings.log_level.lower(),
        access_log=True
    )

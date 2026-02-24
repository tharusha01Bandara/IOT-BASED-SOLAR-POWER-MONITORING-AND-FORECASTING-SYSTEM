"""
Readings API Router

This module defines API endpoints for sensor readings operations.
"""

from typing import Annotated, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.mongodb import get_readings_collection, get_predictions_collection
from app.schemas.readings import (
    ReadingCreate,
    ReadingResponse,
    ReadingSuccessResponse,
    ErrorResponse
)
from app.services.readings_service import ReadingsService
from app.services.ml_service import MLService

logger = get_logger(__name__)

router = APIRouter(
    prefix="/readings",
    tags=["readings"],
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
        400: {"model": ErrorResponse, "description": "Bad Request"}
    }
)


def get_readings_service(
    collection: Annotated[Collection, Depends(get_readings_collection)],
) -> ReadingsService:
    """
    Dependency to get ReadingsService instance.
    
    Args:
        collection: MongoDB collection from dependency injection
        
    Returns:
        ReadingsService instance
    """
    return ReadingsService(collection)


def get_ml_service(
    collection: Annotated[Collection, Depends(get_readings_collection)],
) -> MLService:
    """
    Dependency to get MLService instance.
    
    Args:
        collection: MongoDB collection from dependency injection
        
    Returns:
        MLService instance
    """
    return MLService(collection)


router = APIRouter(
    prefix="/readings",
    tags=["readings"],
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
        400: {"model": ErrorResponse, "description": "Bad Request"}
    }
)


@router.post(
    "",
    response_model=ReadingSuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Store new sensor reading",
    description="Accept sensor data from ESP32 device and store in database with optional ML prediction"
)
async def create_reading(
    reading: ReadingCreate,
    service: Annotated[ReadingsService, Depends(get_readings_service)],
    ml_service: Annotated[MLService, Depends(get_ml_service)],
    predictions_collection: Annotated[Collection, Depends(get_predictions_collection)],
    predict: bool = Query(
        default=False,
        description="Automatically make 15-min power prediction after storing reading"
    )
) -> ReadingSuccessResponse:
    """
    Store a new sensor reading from IoT device.
    
    This endpoint accepts JSON data from ESP32 devices containing
    sensor measurements and device status information. Optionally, it can
    also predict power output 15 minutes ahead using a trained ML model.
    
    Args:
        reading: Validated sensor reading data
        service: Readings service instance (injected)
        ml_service: ML service instance (injected)
        predictions_collection: Predictions collection (injected)
        predict: Whether to make power prediction (default: False)
        
    Returns:
        Success response with insertion details and optional prediction
        
    Raises:
        HTTPException: 400 if validation fails, 500 if database error
    """
    prediction: Optional[dict] = None
    
    try:
        # Convert Pydantic model to dict
        reading_dict = reading.model_dump()
        
        # Store reading using service
        result = await service.create_reading(reading_dict)
        
        # Make prediction if requested and model exists
        if predict:
            try:
                from datetime import datetime
                
                prediction_result = ml_service.predict_next_15min(
                    reading=reading_dict,
                    device_id=reading.device_id
                )
                
                # Store prediction in database
                prediction_doc = {
                    "device_id": reading.device_id,
                    "timestamp": prediction_result['predicted_at'],
                    "predicted_power_15min": prediction_result['predicted_power_15min'],
                    "confidence": prediction_result['confidence'],
                    "model_version": prediction_result['model_version'],
                    "current_power": reading.power,
                    "created_at": datetime.utcnow()
                }
                
                predictions_collection.insert_one(prediction_doc)
                
                prediction = {
                    "predicted_power_15min": prediction_result['predicted_power_15min'],
                    "confidence": prediction_result['confidence'],
                    "model_version": prediction_result['model_version']
                }
                
                logger.info(
                    f"Prediction made for device {reading.device_id}: "
                    f"{prediction_result['predicted_power_15min']:.2f}W"
                )
                
            except ValueError as e:
                # Model not found - not an error, just skip prediction
                logger.debug(f"No model available for prediction: {e}")
            except Exception as e:
                # Prediction error - log but don't fail the reading storage
                logger.warning(f"Failed to make prediction: {e}")
        
        # Build response message
        message = "Reading stored successfully"
        if prediction:
            message += f" with prediction: {prediction['predicted_power_15min']:.2f}W"
        
        # Return success response with optional prediction
        response = ReadingSuccessResponse(
            success=True,
            message=message,
            device_id=result["device_id"],
            timestamp=result["timestamp"],
            inserted_id=result["inserted_id"]
        )
        
        # Add prediction to response if available
        if prediction:
            response.prediction = prediction
        
        return response
        
    except PyMongoError as e:
        logger.error(f"Database error while creating reading: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "DatabaseError",
                "message": "Failed to store reading in database"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in create_reading endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "InternalError",
                "message": "An unexpected error occurred"
            }
        )


@router.get(
    "/latest",
    response_model=ReadingResponse,
    summary="Get latest reading",
    description="Retrieve the most recent sensor reading for a device"
)
async def get_latest_reading(
    service: Annotated[ReadingsService, Depends(get_readings_service)],
    device_id: str = Query(
        description="Device identifier",
        min_length=1,
        max_length=50,
        example="tracker01"
    )
) -> ReadingResponse:
    """
    Get the latest sensor reading for a specific device.
    
    Args:
        device_id: Unique device identifier
        service: Readings service instance (injected)
        
    Returns:
        Most recent reading data
        
    Raises:
        HTTPException: 404 if no readings found, 500 if database error
    """
    try:
        # Retrieve latest reading
        reading = await service.get_latest_reading(device_id)
        
        if not reading:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": "NotFound",
                    "message": f"No readings found for device: {device_id}"
                }
            )
        
        return ReadingResponse(**reading)
        
    except HTTPException:
        raise
    except PyMongoError as e:
        logger.error(f"Database error while retrieving latest reading: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "DatabaseError",
                "message": "Failed to retrieve reading from database"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_latest_reading endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "InternalError",
                "message": "An unexpected error occurred"
            }
        )


@router.get(
    "/history",
    response_model=List[ReadingResponse],
    summary="Get reading history",
    description="Retrieve historical readings within a time range"
)
async def get_reading_history(
    service: Annotated[ReadingsService, Depends(get_readings_service)],
    settings: Annotated[Settings, Depends(get_settings)],
    device_id: str = Query(
        description="Device identifier",
        min_length=1,
        max_length=50,
        example="tracker01"
    ),
    minutes: int = Query(
        default=60,
        description="Time window in minutes to look back",
        ge=1,
        le=10080,
        example=60
    )
) -> List[ReadingResponse]:
    """
    Get historical sensor readings within a time window.
    
    Returns readings sorted by timestamp in ascending order (oldest first).
    
    Args:
        device_id: Unique device identifier
        minutes: Number of minutes to look back (default: 60, max: 10080)
        service: Readings service instance (injected)
        settings: Application settings (injected)
        
    Returns:
        List of readings within the time range
        
    Raises:
        HTTPException: 500 if database error
    """
    try:
        # Retrieve reading history
        readings = await service.get_reading_history(
            device_id=device_id,
            minutes=minutes,
            max_minutes=settings.max_query_minutes
        )
        
        # Convert to response models
        return [ReadingResponse(**reading) for reading in readings]
        
    except PyMongoError as e:
        logger.error(f"Database error while retrieving reading history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "DatabaseError",
                "message": "Failed to retrieve readings from database"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_reading_history endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "InternalError",
                "message": "An unexpected error occurred"
            }
        )


@router.get(
    "/statistics",
    summary="Get device statistics",
    description="Calculate statistics for a device over a time period"
)
async def get_device_statistics(
    service: Annotated[ReadingsService, Depends(get_readings_service)],
    device_id: str = Query(
        description="Device identifier",
        example="tracker01"
    ),
    minutes: int = Query(
        default=60,
        description="Time window in minutes",
        ge=1,
        le=10080,
        example=60
    )
):
    """
    Get aggregated statistics for a device.
    
    Calculates average, min, max values for power and other sensors.
    
    Args:
        device_id: Unique device identifier
        minutes: Time window in minutes
        service: Readings service instance (injected)
        
    Returns:
        Statistics dictionary
        
    Raises:
        HTTPException: 500 if database error
    """
    try:
        stats = await service.get_device_statistics(device_id, minutes)
        return stats
        
    except PyMongoError as e:
        logger.error(f"Database error while calculating statistics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "DatabaseError",
                "message": "Failed to calculate statistics"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_device_statistics endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "InternalError",
                "message": "An unexpected error occurred"
            }
        )

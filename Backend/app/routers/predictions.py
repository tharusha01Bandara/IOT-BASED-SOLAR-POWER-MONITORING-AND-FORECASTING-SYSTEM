"""
Predictions API Router

This module defines API endpoints for ML predictions operations.
"""

from typing import Annotated, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.mongodb import get_predictions_collection
from app.schemas.readings import PredictionResponse, ErrorResponse
from app.services.predictions_service import PredictionsService

logger = get_logger(__name__)

router = APIRouter(
    prefix="/prediction",
    tags=["predictions"],
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
        404: {"model": ErrorResponse, "description": "Not Found"}
    }
)


def get_predictions_service(
    collection: Annotated[Collection, Depends(get_predictions_collection)],
) -> PredictionsService:
    """
    Dependency to get PredictionsService instance.
    
    Args:
        collection: MongoDB collection from dependency injection
        
    Returns:
        PredictionsService instance
    """
    return PredictionsService(collection)


@router.get(
    "/latest",
    response_model=PredictionResponse,
    summary="Get latest prediction",
    description="Retrieve the most recent ML prediction for a device"
)
async def get_latest_prediction(
    service: Annotated[PredictionsService, Depends(get_predictions_service)],
    device_id: str = Query(
        description="Device identifier",
        min_length=1,
        max_length=50,
        example="tracker01"
    )
) -> PredictionResponse:
    """
    Get the latest ML prediction for a specific device.
    
    Args:
        device_id: Unique device identifier
        service: Predictions service instance (injected)
        
    Returns:
        Most recent prediction data
        
    Raises:
        HTTPException: 404 if no predictions found, 500 if database error
    """
    try:
        # Retrieve latest prediction
        prediction = await service.get_latest_prediction(device_id)
        
        if not prediction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": "NotFound",
                    "message": f"No predictions found for device: {device_id}"
                }
            )
        
        return PredictionResponse(**prediction)
        
    except HTTPException:
        raise
    except PyMongoError as e:
        logger.error(f"Database error while retrieving latest prediction: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "DatabaseError",
                "message": "Failed to retrieve prediction from database"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_latest_prediction endpoint: {e}")
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
    response_model=List[PredictionResponse],
    summary="Get prediction history",
    description="Retrieve multiple predictions for a device"
)
async def get_prediction_history(
    service: Annotated[PredictionsService, Depends(get_predictions_service)],
    device_id: str = Query(
        description="Device identifier",
        min_length=1,
        max_length=50,
        example="tracker01"
    ),
    limit: int = Query(
        default=100,
        description="Maximum number of predictions to return",
        ge=1,
        le=1000,
        example=100
    )
) -> List[PredictionResponse]:
    """
    Get historical ML predictions for a device.
    
    Args:
        device_id: Unique device identifier
        limit: Maximum number of predictions to return (default: 100)
        service: Predictions service instance (injected)
        
    Returns:
        List of predictions sorted by timestamp descending
        
    Raises:
        HTTPException: 500 if database error
    """
    try:
        # Retrieve prediction history
        predictions = await service.get_all_predictions(device_id, limit)
        
        # Convert to response models
        return [PredictionResponse(**pred) for pred in predictions]
        
    except PyMongoError as e:
        logger.error(f"Database error while retrieving prediction history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "DatabaseError",
                "message": "Failed to retrieve predictions from database"
            }
        )
    except Exception as e:
        logger.error(f"Unexpected error in get_prediction_history endpoint: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "InternalError",
                "message": "An unexpected error occurred"
            }
        )

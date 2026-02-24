"""
Machine Learning API Router

This module defines API endpoints for ML operations including
training, prediction, and status checking.
"""

from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.mongodb import get_readings_collection, get_predictions_collection
from app.schemas.ml import (
    MLTrainRequest,
    MLTrainResponse,
    MLPredictRequest,
    MLPredictResponse,
    MLStatusResponse,
    PredictionStoreSchema
)
from app.schemas.readings import ErrorResponse
from app.services.ml_service import MLService

logger = get_logger(__name__)

router = APIRouter(
    prefix="/ml",
    tags=["machine-learning"],
    responses={
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
        400: {"model": ErrorResponse, "description": "Bad Request"}
    }
)


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


async def train_model_background(
    device_id: str,
    days: int,
    model_type: str,
    service: MLService
) -> None:
    """
    Background task for model training.
    
    Args:
        device_id: Device identifier
        days: Days of data to use
        model_type: Type of model to train
        service: ML service instance
    """
    try:
        logger.info(f"Background training started for device: {device_id}")
        result = service.train_model(device_id, days, model_type)
        logger.info(f"Background training completed: {result['message']}")
    except Exception as e:
        logger.error(f"Background training failed: {e}", exc_info=True)


@router.post(
    "/train",
    response_model=MLTrainResponse,
    status_code=status.HTTP_200_OK,
    summary="Train ML model",
    description="Train a machine learning model for power forecasting using historical data"
)
async def train_model(
    request: MLTrainRequest,
    background_tasks: BackgroundTasks,
    service: Annotated[MLService, Depends(get_ml_service)]
) -> MLTrainResponse:
    """
    Train ML model for a specific device.
    
    This endpoint trains a model asynchronously in the background to avoid
    blocking the API. The model will be available for predictions once training
    completes.
    
    Args:
        request: Training configuration
        background_tasks: FastAPI background tasks
        service: ML service instance (injected)
        
    Returns:
        Training status and task information
        
    Raises:
        HTTPException: 400 if invalid parameters, 500 if training fails
    """
    try:
        logger.info(
            f"Training request received - Device: {request.device_id}, "
            f"Days: {request.days}, Model: {request.model_type}"
        )
        
        # Check if data exists
        try:
            df = service.load_data_from_mongodb(request.device_id, request.days)
            if len(df) < 100:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={
                        "success": False,
                        "error": "InsufficientData",
                        "message": f"Not enough data for training. Found {len(df)} records, need at least 100."
                    }
                )
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "success": False,
                    "error": "NoData",
                    "message": str(e)
                }
            )
        
        # For smaller datasets, train synchronously
        # For larger datasets (>5000 records), use background task
        if len(df) > 5000:
            # Add to background tasks
            background_tasks.add_task(
                train_model_background,
                request.device_id,
                request.days,
                request.model_type,
                service
            )
            
            logger.info(f"Training scheduled in background for device: {request.device_id}")
            
            # Return immediate response
            return MLTrainResponse(
                success=True,
                message="Model training started in background. Check /ml/status for completion.",
                device_id=request.device_id,
                model_type=request.model_type,
                samples_used=len(df),
                features_used=[],
                metrics={},
                trained_at=datetime.utcnow(),
                model_version="training"
            )
        else:
            # Train synchronously for smaller datasets
            result = service.train_model(
                device_id=request.device_id,
                days=request.days,
                model_type=request.model_type
            )
            
            return MLTrainResponse(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in train endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "TrainingError",
                "message": f"Failed to train model: {str(e)}"
            }
        )


@router.post(
    "/predict",
    response_model=MLPredictResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict power output",
    description="Predict power output 15 minutes ahead using trained model"
)
async def predict_power(
    request: MLPredictRequest,
    service: Annotated[MLService, Depends(get_ml_service)],
    predictions_collection: Annotated[Collection, Depends(get_predictions_collection)]
) -> MLPredictResponse:
    """
    Predict power output 15 minutes ahead.
    
    Args:
        request: Sensor reading data for prediction
        service: ML service instance (injected)
        predictions_collection: MongoDB predictions collection (injected)
        
    Returns:
        Prediction result with confidence score
        
    Raises:
        HTTPException: 404 if model not found, 500 if prediction fails
    """
    try:
        logger.info(f"Prediction request for device: {request.device_id}")
        
        # Make prediction
        result = service.predict_next_15min(
            reading=request.model_dump(),
            device_id=request.device_id
        )
        
        # Store prediction if requested
        prediction_stored = False
        if request.store_prediction:
            try:
                prediction_doc = {
                    "device_id": request.device_id,
                    "timestamp": result['predicted_at'],
                    "predicted_power_15min": result['predicted_power_15min'],
                    "confidence": result['confidence'],
                    "model_version": result['model_version'],
                    "current_power": request.power,
                    "created_at": datetime.utcnow()
                }
                
                predictions_collection.insert_one(prediction_doc)
                prediction_stored = True
                logger.info(f"Prediction stored for device: {request.device_id}")
                
            except Exception as e:
                logger.error(f"Failed to store prediction: {e}")
        
        return MLPredictResponse(
            **result,
            prediction_stored=prediction_stored
        )
        
    except ValueError as e:
        # Model not found
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "success": False,
                "error": "ModelNotFound",
                "message": str(e)
            }
        )
    except Exception as e:
        logger.error(f"Error in predict endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "PredictionError",
                "message": f"Failed to make prediction: {str(e)}"
            }
        )


@router.get(
    "/status",
    response_model=MLStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Get model status",
    description="Get information about trained model including metrics and features"
)
async def get_model_status(
    service: Annotated[MLService, Depends(get_ml_service)],
    device_id: str = Query(
        description="Device identifier",
        min_length=1,
        max_length=50,
        example="tracker01"
    )
) -> MLStatusResponse:
    """
    Get status and metadata of trained model.
    
    Args:
        device_id: Device identifier
        service: ML service instance (injected)
        
    Returns:
        Model status including metrics, features, and training info
    """
    try:
        logger.info(f"Status request for device: {device_id}")
        
        status_info = service.get_model_status(device_id)
        
        return MLStatusResponse(**status_info)
        
    except Exception as e:
        logger.error(f"Error getting model status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "StatusError",
                "message": f"Failed to get model status: {str(e)}"
            }
        )


@router.delete(
    "/model",
    status_code=status.HTTP_200_OK,
    summary="Delete trained model",
    description="Delete trained model files for a specific device"
)
async def delete_model(
    service: Annotated[MLService, Depends(get_ml_service)],
    device_id: str = Query(
        description="Device identifier",
        example="tracker01"
    )
):
    """
    Delete trained model and metadata for a device.
    
    Args:
        device_id: Device identifier
        service: ML service instance (injected)
        
    Returns:
        Deletion status
    """
    try:
        import os
        
        model_path = service.MODEL_DIR / f"{device_id}_{service.MODEL_FILE}"
        metadata_path = service.MODEL_DIR / f"{device_id}_{service.METADATA_FILE}"
        
        deleted = False
        
        if model_path.exists():
            os.remove(model_path)
            deleted = True
            logger.info(f"Deleted model file: {model_path}")
        
        if metadata_path.exists():
            os.remove(metadata_path)
            logger.info(f"Deleted metadata file: {metadata_path}")
        
        # Clear from memory
        if service.metadata and service.metadata.get('device_id') == device_id:
            service.model = None
            service.metadata = None
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={
                    "success": False,
                    "error": "ModelNotFound",
                    "message": f"No model found for device: {device_id}"
                }
            )
        
        return {
            "success": True,
            "message": f"Model deleted for device: {device_id}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting model: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "DeletionError",
                "message": f"Failed to delete model: {str(e)}"
            }
        )


# Import datetime here to avoid circular imports
from datetime import datetime

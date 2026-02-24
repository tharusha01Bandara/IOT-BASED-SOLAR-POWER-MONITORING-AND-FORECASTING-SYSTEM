"""
ML Management API Router

Provides endpoints for managing models, training runs, and retraining.
"""

from typing import Annotated, Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks, status
from pymongo.collection import Collection
from pydantic import BaseModel, Field
from datetime import datetime

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.mongodb import get_readings_collection
from app.services.retrain_service import ModelRetrainService

logger = get_logger(__name__)
settings = get_settings()

router = APIRouter(
    prefix="/ml",
    tags=["ml-management"]
)


# ===============================================
# SCHEMAS
# ===============================================

class RetrainRequest(BaseModel):
    """Request schema for manual retraining"""
    device_id: str = Field(..., description="Device identifier", example="tracker01")
    days: int = Field(default=7, ge=1, le=90, description="Days of data to use")
    background: bool = Field(default=True, description="Run in background")


class RetrainResponse(BaseModel):
    """Response schema for retrain request"""
    success: bool
    message: str
    run_id: Optional[str] = None
    background: bool = False


class ModelRunResponse(BaseModel):
    """Response schema for training run"""
    run_id: str
    device_id: str
    trained_at: datetime
    days_used: int
    rows_used: int
    mae: Optional[float]
    rmse: Optional[float]
    r2: Optional[float]
    status: str
    promoted: bool
    error: Optional[str] = None


class ModelRunsListResponse(BaseModel):
    """Response schema for list of training runs"""
    total: int
    runs: List[ModelRunResponse]


class CurrentModelResponse(BaseModel):
    """Response schema for current model info"""
    model_exists: bool
    version: Optional[str] = None
    updated_at: Optional[datetime] = None
    model_path: Optional[str] = None
    metrics: Optional[dict] = None


# ===============================================
# DEPENDENCIES
# ===============================================

def get_model_runs_collection() -> Collection:
    """Dependency to get model_runs collection"""
    from pymongo import MongoClient
    client = MongoClient(settings.mongodb_url)
    db = client[settings.mongodb_db_name]
    return db[settings.collection_model_runs]


def get_retrain_service(
    readings_coll: Annotated[Collection, Depends(get_readings_collection)],
    model_runs_coll: Annotated[Collection, Depends(get_model_runs_collection)]
) -> ModelRetrainService:
    """Dependency to get ModelRetrainService instance"""
    return ModelRetrainService(readings_coll, model_runs_coll)


# ===============================================
# BACKGROUND TASKS
# ===============================================

async def background_retrain_task(
    device_id: str,
    days: int,
    service: ModelRetrainService
):
    """Background task for model retraining"""
    try:
        logger.info(f"Background retraining started for device: {device_id}")
        result = service.retrain_model(device_id, days)
        
        if result['success']:
            logger.info(f"Background retraining completed: {result['run_id']}")
        else:
            logger.error(f"Background retraining failed: {result.get('error')}")
    
    except Exception as e:
        logger.error(f"Background retraining error: {e}", exc_info=True)


# ===============================================
# ENDPOINTS
# ===============================================

@router.post(
    "/retrain",
    response_model=RetrainResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Trigger model retraining",
    description="Manually trigger model retraining for a device"
)
async def trigger_retrain(
    request: RetrainRequest,
    background_tasks: BackgroundTasks,
    service: Annotated[ModelRetrainService, Depends(get_retrain_service)]
) -> RetrainResponse:
    """
    Trigger model retraining manually.
    
    Can run in foreground (blocking) or background (non-blocking).
    Use background=True for production.
    """
    try:
        logger.info(f"Retrain request: device={request.device_id}, days={request.days}, bg={request.background}")
        
        if request.background:
            # Run in background
            background_tasks.add_task(
                background_retrain_task,
                request.device_id,
                request.days,
                service
            )
            
            return RetrainResponse(
                success=True,
                message="Retraining started in background",
                background=True
            )
        else:
            # Run in foreground (blocking)
            result = service.retrain_model(request.device_id, request.days)
            
            if result['success']:
                return RetrainResponse(
                    success=True,
                    message="Retraining completed successfully",
                    run_id=result['run_id'],
                    background=False
                )
            else:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Retraining failed: {result.get('error')}"
                )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error triggering retrain: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to trigger retraining: {str(e)}"
        )


@router.get(
    "/runs",
    response_model=ModelRunsListResponse,
    summary="Get training runs history",
    description="Retrieve history of model training runs"
)
async def get_training_runs(
    device_id: Optional[str] = Query(default=None, description="Filter by device ID"),
    limit: int = Query(default=20, ge=1, le=100, description="Maximum results"),
    skip: int = Query(default=0, ge=0, description="Number of records to skip"),
    model_runs_coll: Annotated[Collection, Depends(get_model_runs_collection)] = None
) -> ModelRunsListResponse:
    """
    Get training runs history with optional filtering.
    
    Results are sorted by trained_at descending (most recent first).
    """
    try:
        # Build query
        query = {}
        if device_id:
            query['device_id'] = device_id
        
        # Get total count
        total = model_runs_coll.count_documents(query)
        
        # Get runs
        cursor = model_runs_coll.find(query).sort('trained_at', -1).skip(skip).limit(limit)
        runs = list(cursor)
        
        # Convert to response models
        run_responses = []
        for run in runs:
            run_responses.append(ModelRunResponse(
                run_id=run['run_id'],
                device_id=run['device_id'],
                trained_at=run['trained_at'],
                days_used=run['days_used'],
                rows_used=run['rows_used'],
                mae=run.get('mae'),
                rmse=run.get('rmse'),
                r2=run.get('r2'),
                status=run['status'],
                promoted=run.get('promoted', False),
                error=run.get('error')
            ))
        
        return ModelRunsListResponse(
            total=total,
            runs=run_responses
        )
    
    except Exception as e:
        logger.error(f"Error getting training runs: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get training runs: {str(e)}"
        )


@router.get(
    "/model/current",
    response_model=CurrentModelResponse,
    summary="Get current model info",
    description="Get information about the currently active model"
)
async def get_current_model(
    service: Annotated[ModelRetrainService, Depends(get_retrain_service)]
) -> CurrentModelResponse:
    """
    Get information about the currently active/promoted model.
    """
    try:
        current_info = service.get_current_model_info()
        
        if current_info is None:
            return CurrentModelResponse(
                model_exists=False
            )
        
        return CurrentModelResponse(
            model_exists=True,
            version=current_info.get('version'),
            updated_at=datetime.fromisoformat(current_info.get('updated_at')),
            model_path=current_info.get('model_path'),
            metrics=current_info.get('metrics')
        )
    
    except Exception as e:
        logger.error(f"Error getting current model: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get current model: {str(e)}"
        )


@router.get(
    "/runs/{run_id}",
    response_model=ModelRunResponse,
    summary="Get specific training run",
    description="Get details of a specific training run by ID"
)
async def get_training_run(
    run_id: str,
    model_runs_coll: Annotated[Collection, Depends(get_model_runs_collection)] = None
) -> ModelRunResponse:
    """
    Get details of a specific training run.
    """
    try:
        run = model_runs_coll.find_one({'run_id': run_id})
        
        if run is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Training run not found: {run_id}"
            )
        
        return ModelRunResponse(
            run_id=run['run_id'],
            device_id=run['device_id'],
            trained_at=run['trained_at'],
            days_used=run['days_used'],
            rows_used=run['rows_used'],
            mae=run.get('mae'),
            rmse=run.get('rmse'),
            r2=run.get('r2'),
            status=run['status'],
            promoted=run.get('promoted', False),
            error=run.get('error')
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting training run: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get training run: {str(e)}"
        )


@router.delete(
    "/runs/{run_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete training run record",
    description="Delete a training run record (does not delete model files)"
)
async def delete_training_run(
    run_id: str,
    model_runs_coll: Annotated[Collection, Depends(get_model_runs_collection)] = None
):
    """
    Delete a training run record from database.
    
    Note: This only deletes the record, not the model files.
    """
    try:
        result = model_runs_coll.delete_one({'run_id': run_id})
        
        if result.deleted_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Training run not found: {run_id}"
            )
        
        logger.info(f"Deleted training run: {run_id}")
        return None
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting training run: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete training run: {str(e)}"
        )

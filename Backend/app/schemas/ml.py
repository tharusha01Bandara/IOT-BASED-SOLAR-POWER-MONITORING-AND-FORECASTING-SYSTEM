"""
Machine Learning Schemas for Request/Response Validation

This module contains Pydantic models for ML operations including
training, prediction, and model status.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class MLTrainRequest(BaseModel):
    """
    Schema for ML model training request.
    """
    
    device_id: str = Field(
        ...,
        description="Device identifier to train model for",
        min_length=1,
        max_length=50,
        examples=["tracker01"]
    )
    
    days: int = Field(
        default=7,
        description="Number of days of historical data to use for training",
        ge=1,
        le=90
    )
    
    model_type: str = Field(
        default="random_forest",
        description="Type of ML model to train",
        pattern="^(random_forest|linear_regression)$"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "device_id": "tracker01",
                "days": 7,
                "model_type": "random_forest"
            }
        }
    }


class MLTrainResponse(BaseModel):
    """
    Schema for ML model training response.
    """
    
    success: bool = Field(..., description="Training success status")
    message: str = Field(..., description="Status message")
    device_id: str = Field(..., description="Device identifier")
    model_type: str = Field(..., description="Model type used")
    samples_used: int = Field(..., description="Number of training samples")
    features_used: List[str] = Field(..., description="Features used in training")
    metrics: Dict[str, float] = Field(..., description="Model evaluation metrics")
    trained_at: datetime = Field(..., description="Training timestamp")
    model_version: str = Field(..., description="Model version identifier")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "Model trained successfully",
                "device_id": "tracker01",
                "model_type": "random_forest",
                "samples_used": 672,
                "features_used": ["servo_angle", "temperature", "humidity", "lux", "hour", "minute"],
                "metrics": {
                    "mae": 2.34,
                    "rmse": 3.45,
                    "r2_score": 0.92
                },
                "trained_at": "2026-02-23T16:00:00Z",
                "model_version": "1708704000"
            }
        }
    }


class MLPredictRequest(BaseModel):
    """
    Schema for prediction request.
    
    Accepts a single sensor reading and predicts power 15 minutes ahead.
    """
    
    device_id: str = Field(..., description="Device identifier")
    timestamp: datetime = Field(..., description="Reading timestamp")
    servo_angle: float = Field(..., ge=0.0, le=180.0)
    temperature: float = Field(..., ge=-50.0, le=100.0)
    humidity: float = Field(..., ge=0.0, le=100.0)
    lux: float = Field(..., ge=0.0)
    voltage: float = Field(..., ge=0.0)
    current: float = Field(..., ge=0.0)
    power: float = Field(..., ge=0.0)
    store_prediction: bool = Field(
        default=False,
        description="Whether to store prediction in database"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "device_id": "tracker01",
                "timestamp": "2026-02-23T10:30:00Z",
                "servo_angle": 45.5,
                "temperature": 28.3,
                "humidity": 65.2,
                "lux": 5420.0,
                "voltage": 18.5,
                "current": 2.3,
                "power": 42.55,
                "store_prediction": False
            }
        }
    }


class MLPredictResponse(BaseModel):
    """
    Schema for prediction response.
    """
    
    success: bool = Field(..., description="Prediction success status")
    device_id: str = Field(..., description="Device identifier")
    current_power: float = Field(..., description="Current power reading")
    predicted_power_15min: float = Field(..., description="Predicted power 15 minutes ahead")
    confidence: float = Field(..., description="Prediction confidence score (0-1)", ge=0.0, le=1.0)
    model_version: str = Field(..., description="Model version used")
    predicted_at: datetime = Field(..., description="Prediction timestamp")
    prediction_stored: bool = Field(..., description="Whether prediction was stored in DB")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "device_id": "tracker01",
                "current_power": 42.55,
                "predicted_power_15min": 45.23,
                "confidence": 0.89,
                "model_version": "1708704000",
                "predicted_at": "2026-02-23T10:30:00Z",
                "prediction_stored": False
            }
        }
    }


class MLStatusResponse(BaseModel):
    """
    Schema for ML model status response.
    """
    
    model_exists: bool = Field(..., description="Whether model file exists")
    device_id: Optional[str] = Field(None, description="Device ID model is trained for")
    model_type: Optional[str] = Field(None, description="Type of model")
    features: Optional[List[str]] = Field(None, description="Features used in model")
    metrics: Optional[Dict[str, float]] = Field(None, description="Model performance metrics")
    trained_at: Optional[datetime] = Field(None, description="Last training timestamp")
    model_version: Optional[str] = Field(None, description="Model version")
    samples_trained: Optional[int] = Field(None, description="Number of samples used in training")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "model_exists": True,
                "device_id": "tracker01",
                "model_type": "random_forest",
                "features": ["servo_angle", "temperature", "humidity", "lux", "hour", "minute"],
                "metrics": {
                    "mae": 2.34,
                    "rmse": 3.45,
                    "r2_score": 0.92
                },
                "trained_at": "2026-02-23T16:00:00Z",
                "model_version": "1708704000",
                "samples_trained": 672
            }
        }
    }


class PredictionStoreSchema(BaseModel):
    """
    Schema for storing predictions in MongoDB.
    """
    
    device_id: str
    timestamp: datetime
    predicted_power_15min: float
    confidence: float
    model_version: str
    current_power: Optional[float] = None
    features_used: Optional[List[str]] = None
    
    model_config = {
        "protected_namespaces": ()
    }

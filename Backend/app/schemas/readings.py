"""
Pydantic Schemas for Request and Response Validation

This module contains all Pydantic models used for validating
incoming requests from ESP32 devices and formatting API responses.
"""

from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field, validator, field_validator
from enum import Enum


class FanStatus(str, Enum):
    """Enumeration for fan status values"""
    ON = "on"
    OFF = "off"
    AUTO = "auto"


class DeviceStatus(str, Enum):
    """Enumeration for device status values"""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class ReadingBase(BaseModel):
    """
    Base schema for sensor readings from ESP32 device.
    
    This schema validates the data structure sent by IoT devices.
    All fields are required to ensure data integrity.
    """
    
    device_id: str = Field(
        ...,
        description="Unique identifier for the IoT device",
        min_length=1,
        max_length=50,
        examples=["tracker01"]
    )
    
    timestamp: datetime = Field(
        ...,
        description="ISO 8601 formatted timestamp of the reading"
    )
    
    servo_angle: float = Field(
        ...,
        description="Servo motor angle in degrees",
        ge=0.0,
        le=180.0
    )
    
    temperature: float = Field(
        ...,
        description="Temperature reading in Celsius",
        ge=-50.0,
        le=100.0
    )
    
    humidity: float = Field(
        ...,
        description="Relative humidity percentage",
        ge=0.0,
        le=100.0
    )
    
    lux: float = Field(
        ...,
        description="Light intensity in lux",
        ge=0.0
    )
    
    voltage: float = Field(
        ...,
        description="Solar panel voltage in volts",
        ge=0.0
    )
    
    current: float = Field(
        ...,
        description="Solar panel current in amperes",
        ge=0.0
    )
    
    power: float = Field(
        ...,
        description="Calculated power in watts",
        ge=0.0
    )
    
    fan_status: FanStatus = Field(
        ...,
        description="Current status of the cooling fan"
    )
    
    status: DeviceStatus = Field(
        ...,
        description="Overall device operational status"
    )
    
    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, v):
        """
        Parse timestamp from various formats.
        
        Accepts ISO 8601 string, Unix timestamp, or datetime object.
        """
        if isinstance(v, datetime):
            return v
        
        if isinstance(v, str):
            try:
                # Try parsing ISO format
                return datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError(f"Invalid timestamp format: {v}. Use ISO 8601 format.")
        
        if isinstance(v, (int, float)):
            # Unix timestamp in seconds
            return datetime.fromtimestamp(v)
        
        raise ValueError(f"Unsupported timestamp type: {type(v)}")
    
    @field_validator("power", mode="before")
    @classmethod
    def calculate_power_if_missing(cls, v, info):
        """
        Calculate power from voltage and current if not provided.
        """
        if v is None or v == 0:
            # Access other validated fields
            values = info.data
            if "voltage" in values and "current" in values:
                return values["voltage"] * values["current"]
        return v
    
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
                "fan_status": "auto",
                "status": "online"
            }
        }
    }


class ReadingCreate(ReadingBase):
    """
    Schema for creating a new reading (POST request).
    
    Inherits all fields from ReadingBase.
    """
    pass


class ReadingResponse(ReadingBase):
    """
    Schema for reading response (GET request).
    
    Includes additional metadata fields from database.
    """
    
    id: Optional[str] = Field(None, alias="_id", description="MongoDB document ID")
    
    model_config = {
        "populate_by_name": True,
        "from_attributes": True
    }


class PredictionResponse(BaseModel):
    """
    Schema for ML prediction response.
    
    Contains predicted values and model metadata.
    """
    
    device_id: str = Field(..., description="Device identifier")
    timestamp: datetime = Field(..., description="Prediction timestamp")
    predicted_power: Optional[float] = Field(None, description="Predicted power output in watts")
    predicted_angle: Optional[float] = Field(None, description="Predicted optimal angle")
    confidence: Optional[float] = Field(None, description="Prediction confidence score", ge=0.0, le=1.0)
    model_version: Optional[str] = Field(None, description="ML model version used")
    
    model_config = {
        "populate_by_name": True,
        "protected_namespaces": (),  # Allow 'model_' prefix in field names
        "json_schema_extra": {
            "example": {
                "device_id": "tracker01",
                "timestamp": "2026-02-23T11:00:00Z",
                "predicted_power": 45.2,
                "predicted_angle": 50.0,
                "confidence": 0.92,
                "model_version": "v1.0.0"
            }
        }
    }


class ReadingSuccessResponse(BaseModel):
    """
    Schema for successful reading insertion response.
    """
    
    success: bool = Field(True, description="Operation success status")
    message: str = Field(..., description="Success message")
    device_id: str = Field(..., description="Device that sent the reading")
    timestamp: datetime = Field(..., description="Reading timestamp")
    inserted_id: Optional[str] = Field(None, description="MongoDB document ID")
    prediction: Optional[dict] = Field(
        None,
        description="Optional ML prediction result (predicted_power_15min, confidence, model_version)"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "Reading stored successfully with prediction: 245.50W",
                "device_id": "tracker01",
                "timestamp": "2026-02-23T10:30:00Z",
                "inserted_id": "65f8a1b2c3d4e5f6g7h8i9j0",
                "prediction": {
                    "predicted_power_15min": 245.50,
                    "confidence": 0.92,
                    "model_version": "RandomForest_v1"
                }
            }
        }
    }


class ErrorResponse(BaseModel):
    """
    Schema for error responses.
    
    Provides structured error information to clients.
    """
    
    success: bool = Field(False, description="Operation success status")
    error: str = Field(..., description="Error type or code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(None, description="Additional error details")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Error timestamp")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": False,
                "error": "ValidationError",
                "message": "Invalid data format",
                "details": {"field": "temperature", "issue": "value out of range"},
                "timestamp": "2026-02-23T10:30:00Z"
            }
        }
    }


class HealthCheckResponse(BaseModel):
    """
    Schema for health check endpoint response.
    """
    
    status: str = Field(..., description="Service health status")
    database: str = Field(..., description="Database connection status")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    version: str = Field(..., description="API version")
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "database": "connected",
                "timestamp": "2026-02-23T10:30:00Z",
                "version": "1.0.0"
            }
        }
    }

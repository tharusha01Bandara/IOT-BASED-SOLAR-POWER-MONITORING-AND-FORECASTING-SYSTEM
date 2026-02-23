"""
Database Models

This module defines the structure of MongoDB documents
and provides helper functions for document conversion.
"""

from datetime import datetime
from typing import Any, Dict, Optional
from bson import ObjectId


class PyObjectId(ObjectId):
    """
    Custom ObjectId type for Pydantic compatibility.
    """
    
    @classmethod
    def __get_validators__(cls):
        yield cls.validate
    
    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)
    
    @classmethod
    def __get_pydantic_json_schema__(cls, field_schema):
        field_schema.update(type="string")


def reading_helper(reading: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert MongoDB reading document to JSON-serializable dictionary.
    
    Args:
        reading: MongoDB document from readings_raw collection
        
    Returns:
        Dict with converted ObjectId and datetime fields
    """
    if not reading:
        return {}
    
    return {
        "id": str(reading["_id"]) if "_id" in reading else None,
        "device_id": reading.get("device_id"),
        "timestamp": reading.get("timestamp"),
        "servo_angle": reading.get("servo_angle"),
        "temperature": reading.get("temperature"),
        "humidity": reading.get("humidity"),
        "lux": reading.get("lux"),
        "voltage": reading.get("voltage"),
        "current": reading.get("current"),
        "power": reading.get("power"),
        "fan_status": reading.get("fan_status"),
        "status": reading.get("status"),
    }


def prediction_helper(prediction: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert MongoDB prediction document to JSON-serializable dictionary.
    
    Args:
        prediction: MongoDB document from predictions collection
        
    Returns:
        Dict with converted ObjectId and datetime fields
    """
    if not prediction:
        return {}
    
    return {
        "id": str(prediction["_id"]) if "_id" in prediction else None,
        "device_id": prediction.get("device_id"),
        "timestamp": prediction.get("timestamp"),
        "predicted_power": prediction.get("predicted_power"),
        "predicted_angle": prediction.get("predicted_angle"),
        "confidence": prediction.get("confidence"),
        "model_version": prediction.get("model_version"),
    }


def prepare_reading_document(reading_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare reading data for MongoDB insertion.
    
    Ensures proper data types and adds metadata fields.
    
    Args:
        reading_data: Validated reading data from Pydantic model
        
    Returns:
        Dict ready for MongoDB insertion
    """
    document = reading_data.copy()
    
    # Ensure timestamp is datetime object
    if isinstance(document.get("timestamp"), str):
        document["timestamp"] = datetime.fromisoformat(
            document["timestamp"].replace('Z', '+00:00')
        )
    
    # Add insertion metadata
    document["created_at"] = datetime.utcnow()
    
    return document


def prepare_prediction_document(prediction_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare prediction data for MongoDB insertion.
    
    Args:
        prediction_data: Validated prediction data
        
    Returns:
        Dict ready for MongoDB insertion
    """
    document = prediction_data.copy()
    
    # Ensure timestamp is datetime object
    if isinstance(document.get("timestamp"), str):
        document["timestamp"] = datetime.fromisoformat(
            document["timestamp"].replace('Z', '+00:00')
        )
    
    # Add insertion metadata
    document["created_at"] = datetime.utcnow()
    
    return document

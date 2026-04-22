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


def serialize_datetime(dt: Any) -> Optional[str]:
    """Helper to safely serialize datetime to ISO format string."""
    if not dt:
        return None
    if isinstance(dt, datetime):
        iso_str = dt.isoformat()
        # Fast API backend standard typically appends Z for UTC if naive
        return iso_str if iso_str.endswith('Z') or '+' in iso_str else iso_str + 'Z'
    return str(dt)


def serialize_mongo_doc(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Reusable helper function to serialize MongoDB documents.
    Converts ObjectId to string and datetime to ISO format string.
    """
    if not doc:
        return {}
    
    serialized = {}
    for key, value in doc.items():
        if key == "_id":
            serialized["id"] = str(value)
        elif isinstance(value, ObjectId):
            serialized[key] = str(value)
        elif isinstance(value, datetime):
            serialized[key] = serialize_datetime(value)
        else:
            serialized[key] = value
    return serialized


def reading_helper(reading: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert MongoDB reading document to JSON-serializable dictionary.
    """
    if not reading:
        return {}

    # Base serialization for id and timestamp
    doc = serialize_mongo_doc(reading)
    return {
        "id": doc.get("id"),
        "device_id": doc.get("device_id"),
        "timestamp": doc.get("timestamp"),
        "device_timestamp": doc.get("device_timestamp"),
        "servo_angle": doc.get("servo_angle"),
        "temperature": doc.get("temperature"),
        "humidity": doc.get("humidity"),
        "lux": doc.get("lux"),
        "ldr_left": doc.get("ldr_left"),
        "ldr_right": doc.get("ldr_right"),
        "voltage": doc.get("voltage"),
        "current": doc.get("current"),
        "power": doc.get("power"),
        "fan_status": doc.get("fan_status"),
        "status": doc.get("status"),
    }


def history_helper(reading: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert MongoDB document to a lightweight format for charts.
    Includes core telemetry and formatted datetime as ISO string.
    """
    if not reading:
        return {}

    return {
        "timestamp": serialize_datetime(reading.get("timestamp")),
        "power": reading.get("power"),
        "voltage": reading.get("voltage"),
        "current": reading.get("current"),
        "temperature": reading.get("temperature"),
        "humidity": reading.get("humidity"),
        "lux": reading.get("lux"),
        "servo_angle": reading.get("servo_angle"),
        "ldr_left": reading.get("ldr_left"),
        "ldr_right": reading.get("ldr_right"),
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

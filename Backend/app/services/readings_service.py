"""
Readings Service

This module contains business logic for handling sensor readings.
It provides an abstraction layer between the API routes and database operations.
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.core.logging import get_logger
from app.models.reading import (
    reading_helper,
    history_helper,
    prepare_reading_document
)

logger = get_logger(__name__)


class ReadingsService:
    """
    Service class for managing sensor readings.
    
    Handles all business logic related to storing and retrieving
    sensor data from the MongoDB database.
    """
    
    def __init__(self, collection: Collection):
        """
        Initialize readings service.
        
        Args:
            collection: MongoDB collection for readings_raw
        """
        self.collection = collection
    
    async def create_reading(self, reading_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Store a new sensor reading in the database.
        
        Args:
            reading_data: Validated reading data from Pydantic schema
            
        Returns:
            Dict containing insertion result with inserted_id
            
        Raises:
            PyMongoError: If database operation fails
        """
        try:
            # Prepare document for insertion
            document = prepare_reading_document(reading_data)
            
            # Insert into MongoDB
            result = self.collection.insert_one(document)
            
            logger.info(
                f"Stored reading for device {reading_data['device_id']} "
                f"at {reading_data['timestamp']}, ID: {result.inserted_id}"
            )
            
            return {
                "success": True,
                "inserted_id": str(result.inserted_id),
                "device_id": reading_data["device_id"],
                "timestamp": reading_data["timestamp"]
            }
            
        except PyMongoError as e:
            logger.error(f"Failed to insert reading: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in create_reading: {e}")
            raise
    
    async def get_latest_reading(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the most recent reading for a specific device.
        
        Args:
            device_id: Unique identifier of the device
            
        Returns:
            Dict containing the latest reading, or None if not found
        """
        try:
            # Query for latest reading using index (device_id + timestamp desc)
            reading = self.collection.find_one(
                {"device_id": device_id},
                sort=[("timestamp", -1)]  # -1 for descending (latest first)
            )
            
            if reading:
                logger.debug(f"Retrieved latest reading for device {device_id}")
                return reading_helper(reading)
            
            logger.info(f"No readings found for device {device_id}")
            return None
            
        except PyMongoError as e:
            logger.error(f"Failed to retrieve latest reading: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_latest_reading: {e}")
            raise
    
    async def get_reading_history(
        self,
        device_id: str,
        limit: int = 50,
        max_limit: int = 1000
    ) -> List[Dict[str, Any]]:
        """
        Retrieve historical readings limited to N most recent, sorted ascending.
        
        Args:
            device_id: Unique identifier of the device
            limit: Number of recent readings to fetch (default: 50)
            max_limit: Maximum allowed limit to prevent excessive queries

        Returns:
            List of reading dictionaries sorted by timestamp ascending
        """
        try:
            # Validate limit
            if limit <= 0:
                logger.warning(f"Invalid limit value: {limit}, using default 50")
                limit = 50
                
            if limit > max_limit:
                logger.warning(
                    f"Requested limit ({limit}) exceeds maximum ({max_limit}), "
                    f"using maximum"
                )
                limit = max_limit

            # Query for the last N readings (recent first)
            cursor = self.collection.find(
                {"device_id": device_id},
                sort=[("timestamp", -1)]
            ).limit(limit)

            # Convert cursor to list, process with history_helper, and reverse for ascending order
            readings = [history_helper(reading) for reading in cursor]
            readings.reverse()

            logger.info(
                f"Retrieved {len(readings)} history records for device {device_id}"
            )

            return readings

        except PyMongoError as e:
            logger.error(f"Failed to retrieve reading history: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_reading_history: {e}")
            raise
    
    async def get_device_statistics(self, device_id: str, minutes: int = 60) -> Dict[str, Any]:
        """
        Calculate statistics for a device over a time period.
        
        Args:
            device_id: Unique identifier of the device
            minutes: Time window in minutes
            
        Returns:
            Dict containing calculated statistics
        """
        try:
            time_threshold = datetime.utcnow() - timedelta(minutes=minutes)
            
            # Use aggregation pipeline for efficient statistics calculation
            pipeline = [
                {
                    "$match": {
                        "device_id": device_id,
                        "timestamp": {"$gte": time_threshold}
                    }
                },
                {
                    "$group": {
                        "_id": "$device_id",
                        "count": {"$sum": 1},
                        "avg_power": {"$avg": "$power"},
                        "max_power": {"$max": "$power"},
                        "min_power": {"$min": "$power"},
                        "avg_temperature": {"$avg": "$temperature"},
                        "avg_lux": {"$avg": "$lux"}
                    }
                }
            ]
            
            result = list(self.collection.aggregate(pipeline))
            
            if result:
                stats = result[0]
                return {
                    "device_id": device_id,
                    "time_window_minutes": minutes,
                    "reading_count": stats.get("count", 0),
                    "average_power": round(stats.get("avg_power", 0), 2),
                    "max_power": round(stats.get("max_power", 0), 2),
                    "min_power": round(stats.get("min_power", 0), 2),
                    "average_temperature": round(stats.get("avg_temperature", 0), 2),
                    "average_lux": round(stats.get("avg_lux", 0), 2)
                }
            
            return {
                "device_id": device_id,
                "time_window_minutes": minutes,
                "reading_count": 0,
                "message": "No data available for the specified time period"
            }
            
        except PyMongoError as e:
            logger.error(f"Failed to calculate statistics: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_device_statistics: {e}")
            raise

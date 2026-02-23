"""
Predictions Service

This module contains business logic for handling ML predictions.
"""

from typing import Optional, Dict, Any, List
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.core.logging import get_logger
from app.models.reading import prediction_helper

logger = get_logger(__name__)


class PredictionsService:
    """
    Service class for managing predictions data.
    
    Handles retrieval of ML model predictions from MongoDB.
    """
    
    def __init__(self, collection: Collection):
        """
        Initialize predictions service.
        
        Args:
            collection: MongoDB collection for predictions
        """
        self.collection = collection
    
    async def get_latest_prediction(self, device_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve the most recent prediction for a specific device.
        
        Args:
            device_id: Unique identifier of the device
            
        Returns:
            Dict containing the latest prediction, or None if not found
        """
        try:
            # Query for latest prediction using index
            prediction = self.collection.find_one(
                {"device_id": device_id},
                sort=[("timestamp", -1)]
            )
            
            if prediction:
                logger.debug(f"Retrieved latest prediction for device {device_id}")
                return prediction_helper(prediction)
            
            logger.info(f"No predictions found for device {device_id}")
            return None
            
        except PyMongoError as e:
            logger.error(f"Failed to retrieve latest prediction: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_latest_prediction: {e}")
            raise
    
    async def get_all_predictions(self, device_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve multiple predictions for a device.
        
        Args:
            device_id: Unique identifier of the device
            limit: Maximum number of predictions to return
            
        Returns:
            List of prediction dictionaries
        """
        try:
            cursor = self.collection.find(
                {"device_id": device_id},
                sort=[("timestamp", -1)],
                limit=limit
            )
            
            predictions = [prediction_helper(pred) for pred in cursor]
            
            logger.info(f"Retrieved {len(predictions)} predictions for device {device_id}")
            
            return predictions
            
        except PyMongoError as e:
            logger.error(f"Failed to retrieve predictions: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error in get_all_predictions: {e}")
            raise

"""
MongoDB Connection and Database Management Module

This module handles MongoDB connection lifecycle, connection pooling,
and database operations. It provides a singleton database client that
is shared across the application.
"""

import logging
from typing import Optional, Annotated
from pymongo import MongoClient, ASCENDING, DESCENDING
from pymongo.database import Database
from pymongo.collection import Collection
from pymongo.errors import ConnectionFailure, ServerSelectionTimeoutError
from fastapi import Depends

from app.core.config import Settings, get_settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class MongoDBClient:
    """
    MongoDB client manager with connection pooling and lifecycle management.
    
    This class implements a singleton pattern to ensure only one MongoDB
    client exists throughout the application lifecycle.
    """
    
    def __init__(self):
        self.client: Optional[MongoClient] = None
        self.database: Optional[Database] = None
        self._settings: Optional[Settings] = None
    
    def connect(self, settings: Settings) -> None:
        """
        Establish connection to MongoDB with connection pooling.
        
        Args:
            settings: Application settings containing MongoDB configuration
            
        Raises:
            ConnectionFailure: If unable to connect to MongoDB
        """
        if self.client is not None:
            logger.warning("MongoDB client already connected. Skipping connection.")
            return
        
        self._settings = settings
        
        try:
            logger.info(f"Connecting to MongoDB at {settings.mongodb_url}")
            
            # Create MongoDB client with connection pooling
            self.client = MongoClient(
                settings.mongodb_url,
                maxPoolSize=settings.mongodb_max_pool_size,
                minPoolSize=settings.mongodb_min_pool_size,
                serverSelectionTimeoutMS=5000,  # 5 second timeout
                connectTimeoutMS=10000,  # 10 second connection timeout
                socketTimeoutMS=30000,  # 30 second socket timeout
            )
            
            # Verify connection by pinging the server
            self.client.admin.command('ping')
            
            # Get database instance
            self.database = self.client[settings.mongodb_db_name]
            
            logger.info(f"Successfully connected to MongoDB database: {settings.mongodb_db_name}")
            
            # Create indexes after successful connection
            self._create_indexes()
            
        except (ConnectionFailure, ServerSelectionTimeoutError) as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise ConnectionFailure(f"Could not connect to MongoDB: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during MongoDB connection: {e}")
            raise
    
    def close(self) -> None:
        """
        Close MongoDB connection and cleanup resources.
        """
        if self.client is not None:
            logger.info("Closing MongoDB connection")
            self.client.close()
            self.client = None
            self.database = None
            logger.info("MongoDB connection closed")
    
    def _create_indexes(self) -> None:
        """
        Create database indexes for optimized query performance.
        
        Indexes are created on:
        - readings_raw: timestamp (descending) + device_id
        - predictions: timestamp (descending) + device_id
        """
        if self.database is None or self._settings is None:
            logger.warning("Cannot create indexes: database not initialized")
            return
        
        try:
            # Index for readings_raw collection
            readings_collection = self.database[self._settings.collection_readings]
            
            # Compound index: device_id + timestamp (descending for latest queries)
            readings_collection.create_index(
                [("device_id", ASCENDING), ("timestamp", DESCENDING)],
                name="idx_device_timestamp",
                background=True
            )
            
            # Single index on timestamp for time-range queries
            readings_collection.create_index(
                [("timestamp", DESCENDING)],
                name="idx_timestamp",
                background=True
            )
            
            logger.info(f"Created indexes for collection: {self._settings.collection_readings}")
            
            # Index for predictions collection
            predictions_collection = self.database[self._settings.collection_predictions]
            
            # Compound index: device_id + timestamp (descending)
            predictions_collection.create_index(
                [("device_id", ASCENDING), ("timestamp", DESCENDING)],
                name="idx_device_timestamp",
                background=True
            )
            
            logger.info(f"Created indexes for collection: {self._settings.collection_predictions}")
            
        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            # Don't raise - indexes are optimization, not critical for startup
    
    def get_collection(self, collection_name: str) -> Collection:
        """
        Get a MongoDB collection instance.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection: PyMongo collection instance
            
        Raises:
            RuntimeError: If database is not initialized
        """
        if self.database is None:
            raise RuntimeError("Database not initialized. Call connect() first.")
        
        return self.database[collection_name]
    
    def health_check(self) -> bool:
        """
        Check if MongoDB connection is healthy.
        
        Returns:
            bool: True if connection is healthy, False otherwise
        """
        try:
            if self.client is not None:
                self.client.admin.command('ping')
                return True
        except Exception as e:
            logger.error(f"MongoDB health check failed: {e}")
        
        return False


# Global MongoDB client instance (singleton)
mongodb_client = MongoDBClient()


def get_database() -> Database:
    """
    FastAPI dependency to get database instance.
    
    Returns:
        Database: PyMongo database instance
        
    Raises:
        RuntimeError: If database is not initialized
    """
    if mongodb_client.database is None:
        raise RuntimeError("Database not initialized")
    return mongodb_client.database


def get_readings_collection(settings: Annotated[Settings, Depends(get_settings)]) -> Collection:
    """
    FastAPI dependency to get readings collection.
    
    Args:
        settings: Application settings (injected by FastAPI)
        
    Returns:
        Collection: PyMongo collection for readings_raw
    """
    return mongodb_client.get_collection(settings.collection_readings)


def get_predictions_collection(settings: Annotated[Settings, Depends(get_settings)]) -> Collection:
    """
    FastAPI dependency to get predictions collection.
    
    Args:
        settings: Application settings (injected by FastAPI)
        
    Returns:
        Collection: PyMongo collection for predictions
    """
    return mongodb_client.get_collection(settings.collection_predictions)

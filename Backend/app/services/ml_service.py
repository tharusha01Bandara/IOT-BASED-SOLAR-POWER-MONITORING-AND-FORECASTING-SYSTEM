"""
Machine Learning Service Module

This module handles all ML operations including:
- Data preparation from MongoDB
- Feature engineering
- Model training and evaluation
- Prediction pipeline
- Model persistence
"""

import os
import json
import joblib
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path

from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from pymongo.collection import Collection

from app.core.logging import get_logger

logger = get_logger(__name__)


class MLService:
    """
    Service class for Machine Learning operations on solar monitoring data.
    
    Handles data preparation, model training, predictions, and persistence.
    """
    
    # Model storage paths
    MODEL_DIR = Path("app/ml_models")
    MODEL_FILE = "model.pkl"
    METADATA_FILE = "model_meta.json"
    
    # Feature configuration
    BASE_FEATURES = ["servo_angle", "temperature", "humidity", "lux", "voltage", "current"]
    TIME_FEATURES = ["hour", "minute", "day_of_week"]
    TREND_FEATURES = ["power_diff", "lux_diff", "rolling_mean_power"]
    
    def __init__(self, collection: Collection):
        """
        Initialize ML service.
        
        Args:
            collection: MongoDB collection for readings_raw
        """
        self.collection = collection
        self.model = None
        self.metadata = None
        self._ensure_model_directory()
    
    def _ensure_model_directory(self) -> None:
        """Create model directory if it doesn't exist."""
        self.MODEL_DIR.mkdir(parents=True, exist_ok=True)
        logger.info(f"Model directory ensured at: {self.MODEL_DIR}")
    
    def load_data_from_mongodb(
        self,
        device_id: str,
        days: int = 7
    ) -> pd.DataFrame:
        """
        Load sensor data from MongoDB for a specific device.
        
        Args:
            device_id: Device identifier
            days: Number of days of historical data to load
            
        Returns:
            DataFrame with sensor readings sorted by timestamp
        """
        try:
            # Calculate time threshold
            time_threshold = datetime.utcnow() - timedelta(days=days)
            
            logger.info(f"Loading data for device {device_id} from last {days} days")
            
            # Query MongoDB
            cursor = self.collection.find(
                {
                    "device_id": device_id,
                    "timestamp": {"$gte": time_threshold}
                },
                sort=[("timestamp", 1)]
            )
            
            # Convert to DataFrame
            data = list(cursor)
            
            if not data:
                raise ValueError(f"No data found for device {device_id} in last {days} days")
            
            df = pd.DataFrame(data)
            
            # Convert timestamp to datetime if needed
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            logger.info(f"Loaded {len(df)} records for device {device_id}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading data from MongoDB: {e}")
            raise
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create time-based and trend features from raw data.
        
        Args:
            df: DataFrame with raw sensor readings
            
        Returns:
            DataFrame with engineered features
        """
        try:
            df = df.copy()
            
            # Time-based features
            df['hour'] = df['timestamp'].dt.hour
            df['minute'] = df['timestamp'].dt.minute
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            
            # Trend features
            df['power_diff'] = df['power'].diff().fillna(0)
            df['lux_diff'] = df['lux'].diff().fillna(0)
            df['rolling_mean_power'] = df['power'].rolling(window=5, min_periods=1).mean()
            
            logger.info(f"Engineered features: time={len(self.TIME_FEATURES)}, trend={len(self.TREND_FEATURES)}")
            
            return df
            
        except Exception as e:
            logger.error(f"Error engineering features: {e}")
            raise
    
    def create_supervised_dataset(
        self,
        df: pd.DataFrame,
        forecast_minutes: int = 15,
        tolerance_seconds: int = 30
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Create supervised learning dataset for power forecasting.
        
        For each reading, find the power value 15 minutes later.
        
        Args:
            df: DataFrame with features
            forecast_minutes: Minutes ahead to forecast
            tolerance_seconds: Tolerance window for matching future readings
            
        Returns:
            Tuple of (features DataFrame, labels Series)
        """
        try:
            df = df.copy().sort_values('timestamp').reset_index(drop=True)
            
            target_col = []
            
            forecast_delta = timedelta(minutes=forecast_minutes)
            tolerance_delta = timedelta(seconds=tolerance_seconds)
            
            logger.info(f"Creating supervised dataset with {forecast_minutes}min forecast")
            
            for idx, row in df.iterrows():
                target_time = row['timestamp'] + forecast_delta
                
                # Find readings within tolerance window
                time_mask = (
                    (df['timestamp'] >= target_time - tolerance_delta) &
                    (df['timestamp'] <= target_time + tolerance_delta)
                )
                
                future_readings = df[time_mask]
                
                if len(future_readings) > 0:
                    # Use the closest reading
                    future_readings = future_readings.copy()
                    future_readings['time_diff'] = abs(future_readings['timestamp'] - target_time)
                    closest = future_readings.nsmallest(1, 'time_diff')
                    target_col.append(closest['power'].values[0])
                else:
                    target_col.append(np.nan)
            
            df['target_power_15min'] = target_col
            
            # Drop rows with missing labels
            df_clean = df.dropna(subset=['target_power_15min'])
            
            samples_dropped = len(df) - len(df_clean)
            logger.info(f"Created supervised dataset: {len(df_clean)} samples ({samples_dropped} dropped)")
            
            if len(df_clean) == 0:
                raise ValueError("No valid samples after creating supervised dataset")
            
            # Select features
            feature_cols = self.BASE_FEATURES + self.TIME_FEATURES + self.TREND_FEATURES
            available_features = [f for f in feature_cols if f in df_clean.columns]
            
            X = df_clean[available_features]
            y = df_clean['target_power_15min']
            
            return X, y
            
        except Exception as e:
            logger.error(f"Error creating supervised dataset: {e}")
            raise
    
    def train_model(
        self,
        device_id: str,
        days: int = 7,
        model_type: str = "random_forest",
        test_size: float = 0.2
    ) -> Dict[str, Any]:
        """
        Train ML model for power forecasting.
        
        Args:
            device_id: Device identifier
            days: Days of historical data to use
            model_type: Type of model ("random_forest" or "linear_regression")
            test_size: Fraction of data for testing
            
        Returns:
            Dictionary with training results and metrics
        """
        try:
            logger.info(f"Starting model training for device {device_id}")
            logger.info(f"Model type: {model_type}, Days: {days}, Test size: {test_size}")
            
            # Step 1: Load data
            df = self.load_data_from_mongodb(device_id, days)
            
            # Step 2: Engineer features
            df = self.engineer_features(df)
            
            # Step 3: Create supervised dataset
            X, y = self.create_supervised_dataset(df)
            
            logger.info(f"Dataset shape: X={X.shape}, y={y.shape}")
            
            # Step 4: Train/test split (time-based to avoid leakage)
            split_idx = int(len(X) * (1 - test_size))
            X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
            
            logger.info(f"Train: {len(X_train)}, Test: {len(X_test)}")
            
            # Step 5: Train model
            if model_type == "random_forest":
                model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    min_samples_split=5,
                    min_samples_leaf=2,
                    random_state=42,
                    n_jobs=-1
                )
            elif model_type == "linear_regression":
                model = LinearRegression()
            else:
                raise ValueError(f"Unknown model type: {model_type}")
            
            logger.info("Training model...")
            model.fit(X_train, y_train)
            
            # Step 6: Evaluate
            y_pred = model.predict(X_test)
            
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2 = r2_score(y_test, y_pred)
            
            logger.info(f"Model evaluation - MAE: {mae:.3f}, RMSE: {rmse:.3f}, R²: {r2:.3f}")
            
            # Step 7: Save model
            trained_at = datetime.utcnow()
            model_version = str(int(trained_at.timestamp()))
            
            model_path = self.MODEL_DIR / f"{device_id}_{self.MODEL_FILE}"
            metadata_path = self.MODEL_DIR / f"{device_id}_{self.METADATA_FILE}"
            
            joblib.dump(model, model_path)
            logger.info(f"Model saved to: {model_path}")
            
            # Step 8: Save metadata
            metadata = {
                "device_id": device_id,
                "model_type": model_type,
                "features": list(X.columns),
                "metrics": {
                    "mae": float(mae),
                    "rmse": float(rmse),
                    "r2_score": float(r2)
                },
                "trained_at": trained_at.isoformat(),
                "model_version": model_version,
                "samples_trained": len(X_train),
                "samples_tested": len(X_test),
                "forecast_minutes": 15
            }
            
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            logger.info(f"Metadata saved to: {metadata_path}")
            
            # Cache in memory
            self.model = model
            self.metadata = metadata
            
            return {
                "success": True,
                "message": "Model trained successfully",
                "device_id": device_id,
                "model_type": model_type,
                "samples_used": len(X_train) + len(X_test),
                "features_used": list(X.columns),
                "metrics": {
                    "mae": float(mae),
                    "rmse": float(rmse),
                    "r2_score": float(r2)
                },
                "trained_at": trained_at,
                "model_version": model_version
            }
            
        except Exception as e:
            logger.error(f"Error training model: {e}", exc_info=True)
            raise
    
    def load_model(self, device_id: str) -> bool:
        """
        Load trained model from disk.
        
        Args:
            device_id: Device identifier
            
        Returns:
            True if model loaded successfully, False otherwise
        """
        try:
            model_path = self.MODEL_DIR / f"{device_id}_{self.MODEL_FILE}"
            metadata_path = self.MODEL_DIR / f"{device_id}_{self.METADATA_FILE}"
            
            if not model_path.exists():
                logger.warning(f"Model file not found: {model_path}")
                return False
            
            if not metadata_path.exists():
                logger.warning(f"Metadata file not found: {metadata_path}")
                return False
            
            # Load model
            self.model = joblib.load(model_path)
            
            # Load metadata
            with open(metadata_path, 'r') as f:
                self.metadata = json.load(f)
            
            logger.info(f"Model loaded for device: {device_id}")
            logger.info(f"Model version: {self.metadata.get('model_version')}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error loading model: {e}")
            return False
    
    def prepare_features_for_prediction(self, reading: Dict[str, Any]) -> pd.DataFrame:
        """
        Prepare features from a single reading for prediction.
        
        Args:
            reading: Dictionary with sensor reading data
            
        Returns:
            DataFrame with features in correct order
        """
        try:
            # Extract timestamp
            timestamp = reading.get('timestamp')
            if isinstance(timestamp, str):
                timestamp = pd.to_datetime(timestamp)
            elif not isinstance(timestamp, datetime):
                timestamp = datetime.utcnow()
            
            # Create feature dictionary
            features = {}
            
            # Base features
            for feat in self.BASE_FEATURES:
                features[feat] = reading.get(feat, 0.0)
            
            # Time features
            features['hour'] = timestamp.hour
            features['minute'] = timestamp.minute
            features['day_of_week'] = timestamp.weekday()
            
            # Trend features (use 0 for single prediction)
            features['power_diff'] = 0.0
            features['lux_diff'] = 0.0
            features['rolling_mean_power'] = reading.get('power', 0.0)
            
            # Create DataFrame
            df = pd.DataFrame([features])
            
            # Ensure correct feature order
            if self.metadata:
                expected_features = self.metadata.get('features', [])
                # Only use features that exist in both
                available = [f for f in expected_features if f in df.columns]
                df = df[available]
            
            return df
            
        except Exception as e:
            logger.error(f"Error preparing features: {e}")
            raise
    
    def predict_next_15min(
        self,
        reading: Dict[str, Any],
        device_id: str
    ) -> Dict[str, Any]:
        """
        Predict power output 15 minutes ahead.
        
        Args:
            reading: Dictionary with current sensor reading
            device_id: Device identifier
            
        Returns:
            Dictionary with prediction and confidence
        """
        try:
            # Load model if not loaded
            if self.model is None or self.metadata is None:
                success = self.load_model(device_id)
                if not success:
                    raise ValueError(f"No trained model found for device: {device_id}")
            
            # Verify device_id matches
            if self.metadata['device_id'] != device_id:
                logger.warning(f"Model device_id mismatch. Loading correct model...")
                self.model = None
                self.metadata = None
                success = self.load_model(device_id)
                if not success:
                    raise ValueError(f"No trained model found for device: {device_id}")
            
            # Prepare features
            X = self.prepare_features_for_prediction(reading)
            
            # Make prediction
            predicted_power = float(self.model.predict(X)[0])
            
            # Calculate confidence based on MAE
            mae = self.metadata['metrics'].get('mae', 5.0)
            mean_power = reading.get('power', 30.0)
            
            # Confidence: higher when MAE is low relative to mean power
            # confidence = max(0, 1 - (MAE / mean_power))
            confidence = max(0.0, min(1.0, 1.0 - (mae / (mean_power + 1e-6))))
            
            logger.info(f"Prediction: {predicted_power:.2f}W, Confidence: {confidence:.2f}")
            
            return {
                "success": True,
                "device_id": device_id,
                "current_power": reading.get('power', 0.0),
                "predicted_power_15min": predicted_power,
                "confidence": confidence,
                "model_version": self.metadata['model_version'],
                "predicted_at": datetime.utcnow()
            }
            
        except Exception as e:
            logger.error(f"Error making prediction: {e}")
            raise
    
    def get_model_status(self, device_id: str) -> Dict[str, Any]:
        """
        Get status of trained model.
        
        Args:
            device_id: Device identifier
            
        Returns:
            Dictionary with model status and metadata
        """
        try:
            model_path = self.MODEL_DIR / f"{device_id}_{self.MODEL_FILE}"
            metadata_path = self.MODEL_DIR / f"{device_id}_{self.METADATA_FILE}"
            
            if not model_path.exists():
                return {
                    "model_exists": False,
                    "message": f"No model found for device: {device_id}"
                }
            
            # Load metadata if not in memory
            if self.metadata is None or self.metadata.get('device_id') != device_id:
                with open(metadata_path, 'r') as f:
                    metadata = json.load(f)
            else:
                metadata = self.metadata
            
            return {
                "model_exists": True,
                "device_id": metadata.get('device_id'),
                "model_type": metadata.get('model_type'),
                "features": metadata.get('features'),
                "metrics": metadata.get('metrics'),
                "trained_at": metadata.get('trained_at'),
                "model_version": metadata.get('model_version'),
                "samples_trained": metadata.get('samples_trained')
            }
            
        except Exception as e:
            logger.error(f"Error getting model status: {e}")
            return {
                "model_exists": False,
                "error": str(e)
            }

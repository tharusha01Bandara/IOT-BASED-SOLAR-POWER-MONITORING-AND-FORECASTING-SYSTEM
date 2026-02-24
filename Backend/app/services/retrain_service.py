"""
Model Retraining Service

This module handles automated model retraining with versioning,
model comparison, and training run logging.
"""

import os
import json
import joblib
import uuid
import shutil
import numpy as np
import pandas as pd
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple, List
from pathlib import Path

from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from pymongo.collection import Collection
from pymongo.errors import PyMongoError

from app.core.logging import get_logger
from app.core.config import get_settings

logger = get_logger(__name__)
settings = get_settings()


class ModelRetrainService:
    """
    Service for handling model retraining with versioning and logging.
    
    Features:
    - Versioned model storage
    - Training run logging to MongoDB
    - Model performance comparison
    - Atomic model promotion
    """
    
    def __init__(
        self,
        readings_collection: Collection,
        model_runs_collection: Collection
    ):
        """
        Initialize retraining service.
        
        Args:
            readings_collection: MongoDB collection for sensor readings
            model_runs_collection: MongoDB collection for training run logs
        """
        self.readings_collection = readings_collection
        self.model_runs_collection = model_runs_collection
        
        self.model_dir = Path(settings.model_dir)
        self.versions_dir = Path(settings.model_versions_dir)
        self.current_pointer_file = Path(settings.model_current_pointer)
        
        self._ensure_directories()
    
    def _ensure_directories(self) -> None:
        """Create necessary directories if they don't exist."""
        self.model_dir.mkdir(parents=True, exist_ok=True)
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Model directories ensured: {self.model_dir}, {self.versions_dir}")
    
    def get_current_model_info(self) -> Optional[Dict[str, Any]]:
        """
        Get information about the currently active model.
        
        Returns:
            Dictionary with current model info, or None if no model exists
        """
        try:
            if not self.current_pointer_file.exists():
                logger.warning("No current model pointer file found")
                return None
            
            with open(self.current_pointer_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error reading current model pointer: {e}")
            return None
    
    def load_training_data(
        self,
        device_id: str,
        days: int = 7
    ) -> pd.DataFrame:
        """
        Load training data from MongoDB with time range filtering.
        
        Args:
            device_id: Device identifier
            days: Number of days of historical data
            
        Returns:
            DataFrame with sensor readings
        """
        from datetime import timedelta
        
        try:
            # Calculate time range
            end_time = datetime.now(timezone.utc)
            start_time = end_time - timedelta(days=days)
            
            logger.info(f"Loading data for device {device_id} from {start_time} to {end_time}")
            
            # Query MongoDB
            query = {
                "device_id": device_id,
                "timestamp": {"$gte": start_time, "$lte": end_time}
            }
            
            cursor = self.readings_collection.find(query).sort("timestamp", 1)
            documents = list(cursor)
            
            if not documents:
                raise ValueError(f"No data found for device {device_id} in last {days} days")
            
            df = pd.DataFrame(documents)
            
            # Drop MongoDB _id
            if '_id' in df.columns:
                df = df.drop(columns=['_id'])
            
            # Parse timestamps
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Filter by status
            if 'status' in df.columns:
                df = df[df['status'] == 'online']
            
            logger.info(f"Loaded {len(df)} records for training")
            
            return df
            
        except Exception as e:
            logger.error(f"Error loading training data: {e}")
            raise
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Engineer features from raw sensor data.
        
        Args:
            df: DataFrame with raw readings
            
        Returns:
            DataFrame with engineered features
        """
        try:
            df = df.copy()
            
            # Time features
            df['hour'] = df['timestamp'].dt.hour
            df['minute'] = df['timestamp'].dt.minute
            df['day_of_week'] = df['timestamp'].dt.dayofweek
            
            # Trend features
            df['power_diff'] = df['power'].diff().fillna(0)
            df['lux_diff'] = df['lux'].diff().fillna(0)
            df['rolling_mean_power_5'] = df['power'].rolling(window=5, min_periods=1).mean()
            df['rolling_mean_lux_5'] = df['lux'].rolling(window=5, min_periods=1).mean()
            
            # Binary features
            df['fan_on'] = 0
            if 'fan_status' in df.columns:
                df['fan_on'] = (df['fan_status'] == 'on').astype(int)
            
            return df
            
        except Exception as e:
            logger.error(f"Error engineering features: {e}")
            raise
    
    def create_supervised_dataset(
        self,
        df: pd.DataFrame,
        forecast_minutes: int = 15
    ) -> Tuple[pd.DataFrame, pd.Series]:
        """
        Create supervised learning dataset with target labels.
        
        Args:
            df: DataFrame with features
            forecast_minutes: Forecast horizon in minutes
            
        Returns:
            Tuple of (features, labels)
        """
        try:
            from datetime import timedelta
            
            df = df.copy().sort_values('timestamp').reset_index(drop=True)
            
            forecast_delta = timedelta(minutes=forecast_minutes)
            tolerance_delta = timedelta(seconds=30)
            
            target_col = []
            
            for idx, row in df.iterrows():
                target_time = row['timestamp'] + forecast_delta
                
                # Find readings within tolerance
                time_mask = (
                    (df['timestamp'] >= target_time - tolerance_delta) &
                    (df['timestamp'] <= target_time + tolerance_delta)
                )
                
                future_readings = df[time_mask]
                
                if len(future_readings) > 0:
                    # Use closest reading
                    future_readings = future_readings.copy()
                    future_readings['time_diff'] = abs(future_readings['timestamp'] - target_time)
                    closest = future_readings.nsmallest(1, 'time_diff')
                    target_col.append(closest['power'].values[0])
                else:
                    target_col.append(np.nan)
            
            df['target_power_15min'] = target_col
            
            # Drop rows with missing labels
            df_clean = df.dropna(subset=['target_power_15min'])
            
            logger.info(f"Created {len(df_clean)} supervised samples (dropped {len(df) - len(df_clean)})")
            
            if len(df_clean) < 100:
                raise ValueError(f"Insufficient training samples: {len(df_clean)} (need at least 100)")
            
            # Feature columns
            feature_cols = [
                'hour', 'minute', 'day_of_week',
                'servo_angle', 'temperature', 'humidity', 'lux',
                'voltage', 'current', 'power',
                'fan_on', 'power_diff', 'lux_diff',
                'rolling_mean_power_5', 'rolling_mean_lux_5'
            ]
            
            available_features = [f for f in feature_cols if f in df_clean.columns]
            
            X = df_clean[available_features]
            y = df_clean['target_power_15min']
            
            return X, y
            
        except Exception as e:
            logger.error(f"Error creating supervised dataset: {e}")
            raise
    
    def train_and_evaluate_model(
        self,
        X_train: pd.DataFrame,
        y_train: pd.Series,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        model_type: str = "RandomForest"
    ) -> Tuple[Any, Dict[str, Any]]:
        """
        Train and evaluate a model.
        
        Args:
            X_train, y_train: Training data
            X_test, y_test: Test data
            model_type: Type of model to train
            
        Returns:
            Tuple of (trained_model, metrics_dict)
        """
        try:
            logger.info(f"Training {model_type} model...")
            logger.info(f"Train samples: {len(X_train)}, Test samples: {len(X_test)}")
            
            # Train model
            if model_type == "RandomForest":
                model = RandomForestRegressor(
                    n_estimators=100,
                    max_depth=15,
                    min_samples_split=10,
                    min_samples_leaf=4,
                    max_features='sqrt',
                    random_state=42,
                    n_jobs=-1,
                    verbose=0
                )
            else:
                raise ValueError(f"Unknown model type: {model_type}")
            
            model.fit(X_train, y_train)
            
            # Evaluate on test set
            y_pred = model.predict(X_test)
            
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2 = r2_score(y_test, y_pred)
            
            metrics = {
                'mae': float(mae),
                'rmse': float(rmse),
                'r2': float(r2),
                'train_samples': len(X_train),
                'test_samples': len(X_test)
            }
            
            logger.info(f"Model trained - MAE: {mae:.4f}, RMSE: {rmse:.4f}, R²: {r2:.4f}")
            
            return model, metrics
            
        except Exception as e:
            logger.error(f"Error training model: {e}")
            raise
    
    def save_versioned_model(
        self,
        model: Any,
        metadata: Dict[str, Any],
        version_timestamp: str
    ) -> Tuple[Path, Path]:
        """
        Save model and metadata with version timestamp.
        
        Args:
            model: Trained model
            metadata: Model metadata
            version_timestamp: Version timestamp string
            
        Returns:
            Tuple of (model_path, metadata_path)
        """
        try:
            model_filename = f"model_{version_timestamp}.pkl"
            metadata_filename = f"model_{version_timestamp}_meta.json"
            
            model_path = self.versions_dir / model_filename
            metadata_path = self.versions_dir / metadata_filename
            
            # Save model
            joblib.dump(model, model_path)
            logger.info(f"Model saved: {model_path}")
            
            # Save metadata
            with open(metadata_path, 'w') as f:
                json.dump(metadata, f, indent=2, default=str)
            logger.info(f"Metadata saved: {metadata_path}")
            
            return model_path, metadata_path
            
        except Exception as e:
            logger.error(f"Error saving versioned model: {e}")
            raise
    
    def update_current_model_pointer(
        self,
        model_path: Path,
        metadata_path: Path,
        version_timestamp: str,
        metrics: Dict[str, Any]
    ) -> None:
        """
        Update the current model pointer to the new model.
        
        Uses atomic write to ensure consistency.
        
        Args:
            model_path: Path to model file
            metadata_path: Path to metadata file
            version_timestamp: Version timestamp
            metrics: Model metrics
        """
        try:
            pointer_data = {
                'model_path': str(model_path),
                'metadata_path': str(metadata_path),
                'version': version_timestamp,
                'updated_at': datetime.now(timezone.utc).isoformat(),
                'metrics': metrics
            }
            
            # Atomic write: write to temp file, then move
            temp_file = self.current_pointer_file.with_suffix('.tmp')
            with open(temp_file, 'w') as f:
                json.dump(pointer_data, f, indent=2, default=str)
            
            # Atomic move (rename)
            shutil.move(str(temp_file), str(self.current_pointer_file))
            
            logger.info(f"Current model pointer updated to version {version_timestamp}")
            
        except Exception as e:
            logger.error(f"Error updating current model pointer: {e}")
            raise
    
    def log_training_run(
        self,
        run_id: str,
        device_id: str,
        days_used: int,
        rows_used: int,
        metrics: Dict[str, Any],
        features: List[str],
        model_path: str,
        status: str,
        error: Optional[str] = None,
        promoted: bool = False
    ) -> None:
        """
        Log training run to MongoDB.
        
        Args:
            run_id: Unique run identifier
            device_id: Device identifier
            days_used: Days of data used
            rows_used: Number of rows used for training
            metrics: Model metrics
            features: Feature list
            model_path: Path to saved model
            status: Run status (success/failed)
            error: Error message if failed
            promoted: Whether model was promoted to current
        """
        try:
            run_doc = {
                'run_id': run_id,
                'device_id': device_id,
                'trained_at': datetime.now(timezone.utc),
                'days_used': days_used,
                'horizon_minutes': 15,
                'rows_used': rows_used,
                'mae': metrics.get('mae'),
                'rmse': metrics.get('rmse'),
                'r2': metrics.get('r2'),
                'train_samples': metrics.get('train_samples'),
                'test_samples': metrics.get('test_samples'),
                'features': features,
                'model_path': model_path,
                'status': status,
                'error': error,
                'promoted': promoted
            }
            
            self.model_runs_collection.insert_one(run_doc)
            logger.info(f"Training run logged: {run_id}")
            
        except PyMongoError as e:
            logger.error(f"Error logging training run to MongoDB: {e}")
            # Don't raise - logging failure shouldn't stop retraining
    
    def should_promote_model(
        self,
        new_mae: float,
        current_info: Optional[Dict[str, Any]]
    ) -> Tuple[bool, str]:
        """
        Decide whether to promote new model based on performance.
        
        Args:
            new_mae: MAE of newly trained model
            current_info: Current model info (None if no current model)
            
        Returns:
            Tuple of (should_promote: bool, reason: str)
        """
        if current_info is None:
            return True, "No current model exists"
        
        current_mae = current_info.get('metrics', {}).get('mae')
        
        if current_mae is None:
            return True, "Current model has no MAE metric"
        
        # Calculate percentage increase
        mae_increase_pct = ((new_mae - current_mae) / current_mae) * 100
        
        threshold = settings.mae_threshold_percent
        
        if mae_increase_pct <= threshold:
            if mae_increase_pct < 0:
                return True, f"New model is better (MAE improved by {abs(mae_increase_pct):.2f}%)"
            else:
                return True, f"New model is acceptable (MAE increased by {mae_increase_pct:.2f}%, within {threshold}% threshold)"
        else:
            return False, f"New model is worse (MAE increased by {mae_increase_pct:.2f}%, exceeds {threshold}% threshold)"
    
    def retrain_model(
        self,
        device_id: str,
        days: int = 7,
        test_size: float = 0.2
    ) -> Dict[str, Any]:
        """
        Complete model retraining workflow with versioning.
        
        Args:
            device_id: Device identifier
            days: Days of data to use
            test_size: Test set fraction
            
        Returns:
            Dictionary with run results
        """
        run_id = str(uuid.uuid4())
        version_timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        
        logger.info("="*70)
        logger.info(f"Starting model retraining - Run ID: {run_id}")
        logger.info(f"Device: {device_id}, Days: {days}, Test size: {test_size}")
        logger.info("="*70)
        
        try:
            # Step 1: Load data
            df = self.load_training_data(device_id, days)
            
            # Step 2: Engineer features
            df = self.engineer_features(df)
            
            # Step 3: Create supervised dataset
            X, y = self.create_supervised_dataset(df)
            
            # Step 4: Time-based split (no leakage)
            split_idx = int(len(X) * (1 - test_size))
            X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
            y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
            
            # Step 5: Train model
            model, metrics = self.train_and_evaluate_model(
                X_train, y_train, X_test, y_test
            )
            
            # Step 6: Save versioned model
            metadata = {
                'device_id': device_id,
                'version': version_timestamp,
                'trained_at': datetime.now(timezone.utc).isoformat(),
                'days_used': days,
                'rows_used': len(X),
                'features': list(X.columns),
                'metrics': metrics,
                'model_type': 'RandomForest'
            }
            
            model_path, metadata_path = self.save_versioned_model(
                model, metadata, version_timestamp
            )
            
            # Step 7: Check if should promote
            current_info = self.get_current_model_info()
            should_promote, reason = self.should_promote_model(
                metrics['mae'], current_info
            )
            
            logger.info(f"Promotion decision: {should_promote} - {reason}")
            
            # Step 8: Promote if approved
            if should_promote:
                self.update_current_model_pointer(
                    model_path, metadata_path, version_timestamp, metrics
                )
            
            # Step 9: Log training run
            self.log_training_run(
                run_id=run_id,
                device_id=device_id,
                days_used=days,
                rows_used=len(X),
                metrics=metrics,
                features=list(X.columns),
                model_path=str(model_path),
                status='success',
                promoted=should_promote
            )
            
            logger.info("="*70)
            logger.info("✓ Model retraining completed successfully")
            logger.info("="*70)
            
            return {
                'success': True,
                'run_id': run_id,
                'version': version_timestamp,
                'metrics': metrics,
                'promoted': should_promote,
                'promotion_reason': reason,
                'model_path': str(model_path)
            }
            
        except Exception as e:
            logger.error(f"✗ Model retraining failed: {e}", exc_info=True)
            
            # Log failed run
            self.log_training_run(
                run_id=run_id,
                device_id=device_id,
                days_used=days,
                rows_used=0,
                metrics={},
                features=[],
                model_path='',
                status='failed',
                error=str(e),
                promoted=False
            )
            
            return {
                'success': False,
                'run_id': run_id,
                'error': str(e)
            }

"""
Solar Power Prediction - ML Model Training Script

Trains RandomForest model for 15-minute-ahead power prediction.
Uses the dataset created by build_dataset.py.

Usage:
    python train_model.py --dataset ../data/solar_dataset.csv --output ../models/

Features:
- Automatic train/test split (80/20)
- Multiple model types (RandomForest, Gradient Boosting)
- Comprehensive evaluation metrics
- Model versioning with metadata
- Feature importance analysis
- Training report generation
"""

import argparse
import logging
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple
import json

import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score,
    mean_absolute_percentage_error
)
import joblib

# ===============================================
# CONFIGURATION
# ===============================================

FEATURE_COLUMNS = [
    'hour', 'minute', 'day_of_week',
    'servo_angle', 'temperature', 'humidity', 'lux',
    'voltage', 'current', 'power',
    'fan_on', 'power_diff', 'lux_diff',
    'rolling_mean_power_5', 'rolling_mean_lux_5'
]

TARGET_COLUMN = 'target_power_t_plus_15'

RANDOM_STATE = 42
TEST_SIZE = 0.2

MODEL_CONFIGS = {
    'RandomForest': {
        'class': RandomForestRegressor,
        'params': {
            'n_estimators': 100,
            'max_depth': 15,
            'min_samples_split': 10,
            'min_samples_leaf': 4,
            'max_features': 'sqrt',
            'random_state': RANDOM_STATE,
            'n_jobs': -1,
            'verbose': 0
        }
    },
    'GradientBoosting': {
        'class': GradientBoostingRegressor,
        'params': {
            'n_estimators': 100,
            'max_depth': 5,
            'learning_rate': 0.1,
            'min_samples_split': 10,
            'min_samples_leaf': 4,
            'random_state': RANDOM_STATE,
            'verbose': 0
        }
    }
}

# ===============================================
# LOGGING SETUP
# ===============================================

def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging"""
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    return logging.getLogger(__name__)


# ===============================================
# DATA LOADING
# ===============================================

def load_dataset(filepath: Path, logger: logging.Logger) -> pd.DataFrame:
    """
    Load and validate the training dataset.
    
    Args:
        filepath: Path to CSV dataset
        logger: Logger instance
        
    Returns:
        DataFrame with loaded data
    """
    logger.info(f"Loading dataset from: {filepath}")
    
    if not filepath.exists():
        raise FileNotFoundError(f"Dataset not found: {filepath}")
    
    # Load CSV
    df = pd.read_csv(filepath)
    
    logger.info(f"✓ Dataset loaded | Rows: {len(df):,} | Columns: {len(df.columns)}")
    
    # Validate required columns
    missing_features = [col for col in FEATURE_COLUMNS if col not in df.columns]
    if missing_features:
        raise ValueError(f"Missing feature columns: {missing_features}")
    
    if TARGET_COLUMN not in df.columns:
        raise ValueError(f"Missing target column: {TARGET_COLUMN}")
    
    # Check for missing values
    missing_counts = df[FEATURE_COLUMNS + [TARGET_COLUMN]].isnull().sum()
    total_missing = missing_counts.sum()
    
    if total_missing > 0:
        logger.warning(f"⚠ Found {total_missing} missing values:")
        for col, count in missing_counts[missing_counts > 0].items():
            logger.warning(f"   - {col}: {count}")
        
        # Drop rows with missing values
        df_clean = df[FEATURE_COLUMNS + [TARGET_COLUMN]].dropna()
        logger.info(f"Dropped {len(df) - len(df_clean)} rows with missing values")
        df = df_clean
    
    return df


# ===============================================
# DATA SPLITTING
# ===============================================

def split_data(
    df: pd.DataFrame,
    test_size: float,
    random_state: int,
    logger: logging.Logger
) -> Tuple[pd.DataFrame, pd.DataFrame, pd.Series, pd.Series]:
    """
    Split dataset into train/test sets.
    
    Args:
        df: Input dataframe
        test_size: Fraction for test set
        random_state: Random seed
        logger: Logger instance
        
    Returns:
        X_train, X_test, y_train, y_test
    """
    logger.info(f"Splitting data | Test size: {test_size:.0%}")
    
    # Extract features and target
    X = df[FEATURE_COLUMNS]
    y = df[TARGET_COLUMN]
    
    # Split
    X_train, X_test, y_train, y_test = train_test_split(
        X, y,
        test_size=test_size,
        random_state=random_state,
        shuffle=True  # Important for time series to avoid data leakage patterns
    )
    
    logger.info(f"✓ Split complete")
    logger.info(f"   - Training samples: {len(X_train):,}")
    logger.info(f"   - Test samples: {len(X_test):,}")
    logger.info(f"   - Features: {len(FEATURE_COLUMNS)}")
    
    return X_train, X_test, y_train, y_test


# ===============================================
# MODEL TRAINING
# ===============================================

def train_model(
    X_train: pd.DataFrame,
    y_train: pd.Series,
    model_type: str,
    logger: logging.Logger
) -> Any:
    """
    Train the ML model.
    
    Args:
        X_train: Training features
        y_train: Training target
        model_type: Type of model ('RandomForest' or 'GradientBoosting')
        logger: Logger instance
        
    Returns:
        Trained model
    """
    if model_type not in MODEL_CONFIGS:
        raise ValueError(f"Unknown model type: {model_type}. Choose from {list(MODEL_CONFIGS.keys())}")
    
    logger.info(f"Training {model_type} model...")
    
    config = MODEL_CONFIGS[model_type]
    model = config['class'](**config['params'])
    
    # Train
    start_time = datetime.now()
    model.fit(X_train, y_train)
    training_time = (datetime.now() - start_time).total_seconds()
    
    logger.info(f"✓ Training complete | Time: {training_time:.2f}s")
    
    return model


# ===============================================
# MODEL EVALUATION
# ===============================================

def evaluate_model(
    model: Any,
    X_train: pd.DataFrame,
    y_train: pd.Series,
    X_test: pd.DataFrame,
    y_test: pd.Series,
    logger: logging.Logger
) -> Dict[str, Any]:
    """
    Evaluate model performance on train and test sets.
    
    Args:
        model: Trained model
        X_train, y_train: Training data
        X_test, y_test: Test data
        logger: Logger instance
        
    Returns:
        Dictionary with evaluation metrics
    """
    logger.info("Evaluating model performance...")
    
    # Make predictions
    y_train_pred = model.predict(X_train)
    y_test_pred = model.predict(X_test)
    
    # Calculate metrics
    def calc_metrics(y_true, y_pred, set_name):
        mae = mean_absolute_error(y_true, y_pred)
        rmse = np.sqrt(mean_squared_error(y_true, y_pred))
        r2 = r2_score(y_true, y_pred)
        
        # MAPE (handle division by zero)
        mape = mean_absolute_percentage_error(y_true, y_pred) * 100
        
        logger.info(f"   {set_name} Metrics:")
        logger.info(f"      - MAE:  {mae:.4f} W")
        logger.info(f"      - RMSE: {rmse:.4f} W")
        logger.info(f"      - R²:   {r2:.4f}")
        logger.info(f"      - MAPE: {mape:.2f}%")
        
        return {
            'mae': float(mae),
            'rmse': float(rmse),
            'r2': float(r2),
            'mape': float(mape)
        }
    
    metrics = {
        'train': calc_metrics(y_train, y_train_pred, '📈 Train'),
        'test': calc_metrics(y_test, y_test_pred, '📊 Test')
    }
    
    logger.info("✓ Evaluation complete")
    
    return metrics, y_test_pred


# ===============================================
# FEATURE IMPORTANCE
# ===============================================

def analyze_feature_importance(
    model: Any,
    feature_names: list,
    logger: logging.Logger,
    top_n: int = 10
) -> Dict[str, float]:
    """
    Analyze and log feature importance.
    
    Args:
        model: Trained model with feature_importances_
        feature_names: List of feature names
        logger: Logger instance
        top_n: Number of top features to display
        
    Returns:
        Dictionary of feature importances
    """
    if not hasattr(model, 'feature_importances_'):
        logger.warning("Model does not support feature importance")
        return {}
    
    logger.info(f"Feature importance analysis (Top {top_n}):")
    
    importances = model.feature_importances_
    indices = np.argsort(importances)[::-1]
    
    importance_dict = {}
    for i in range(min(top_n, len(feature_names))):
        idx = indices[i]
        importance = importances[idx]
        feature = feature_names[idx]
        importance_dict[feature] = float(importance)
        logger.info(f"   {i+1:2d}. {feature:25s} : {importance:.4f}")
    
    return importance_dict


# ===============================================
# MODEL SAVING
# ===============================================

def save_model(
    model: Any,
    model_type: str,
    metrics: Dict[str, Any],
    feature_importance: Dict[str, float],
    output_dir: Path,
    logger: logging.Logger
) -> Dict[str, Path]:
    """
    Save trained model and metadata.
    
    Args:
        model: Trained model
        model_type: Type of model
        metrics: Evaluation metrics
        feature_importance: Feature importance scores
        output_dir: Directory to save model
        logger: Logger instance
        
    Returns:
        Dictionary with paths to saved files
    """
    logger.info(f"Saving model to: {output_dir}")
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Generate version timestamp
    version = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Save model
    model_filename = f"solar_power_model_{model_type}_{version}.pkl"
    model_path = output_dir / model_filename
    joblib.dump(model, model_path)
    logger.info(f"✓ Model saved: {model_filename}")
    
    # Save metadata
    metadata = {
        'model_type': model_type,
        'version': version,
        'trained_at': datetime.now().isoformat(),
        'features': FEATURE_COLUMNS,
        'target': TARGET_COLUMN,
        'metrics': metrics,
        'feature_importance': feature_importance,
        'model_params': MODEL_CONFIGS[model_type]['params']
    }
    
    metadata_filename = f"solar_power_model_{model_type}_{version}_metadata.json"
    metadata_path = output_dir / metadata_filename
    with open(metadata_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    logger.info(f"✓ Metadata saved: {metadata_filename}")
    
    # Save latest symlink info
    latest_info = {
        'model_file': model_filename,
        'metadata_file': metadata_filename,
        'version': version,
        'updated_at': datetime.now().isoformat()
    }
    
    latest_path = output_dir / f"latest_{model_type.lower()}.json"
    with open(latest_path, 'w') as f:
        json.dump(latest_info, f, indent=2)
    logger.info(f"✓ Latest info updated")
    
    return {
        'model': model_path,
        'metadata': metadata_path,
        'latest': latest_path
    }


# ===============================================
# MAIN
# ===============================================

def main():
    """Main training pipeline"""
    
    # Parse arguments
    parser = argparse.ArgumentParser(
        description='Train solar power prediction model',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python train_model.py --dataset ../data/solar_dataset.csv
  python train_model.py --dataset ../data/solar_dataset.csv --model GradientBoosting
  python train_model.py --dataset ../data/solar_dataset.csv --output ../models/ --verbose
        """
    )
    
    parser.add_argument(
        '--dataset',
        type=str,
        required=True,
        help='Path to training dataset CSV'
    )
    
    parser.add_argument(
        '--output',
        type=str,
        default='../models',
        help='Output directory for trained model (default: ../models)'
    )
    
    parser.add_argument(
        '--model',
        type=str,
        choices=list(MODEL_CONFIGS.keys()),
        default='RandomForest',
        help='Model type to train (default: RandomForest)'
    )
    
    parser.add_argument(
        '--test-size',
        type=float,
        default=TEST_SIZE,
        help=f'Test set size as fraction (default: {TEST_SIZE})'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Setup
    logger = setup_logging(args.verbose)
    logger.info("=" * 70)
    logger.info("SOLAR POWER ML MODEL TRAINING")
    logger.info("=" * 70)
    
    try:
        # Convert paths
        dataset_path = Path(args.dataset)
        output_dir = Path(args.output)
        
        # Load data
        df = load_dataset(dataset_path, logger)
        
        # Split data
        X_train, X_test, y_train, y_test = split_data(
            df, args.test_size, RANDOM_STATE, logger
        )
        
        # Train model
        model = train_model(X_train, y_train, args.model, logger)
        
        # Evaluate
        metrics, y_test_pred = evaluate_model(
            model, X_train, y_train, X_test, y_test, logger
        )
        
        # Feature importance
        feature_importance = analyze_feature_importance(
            model, FEATURE_COLUMNS, logger
        )
        
        # Save model
        saved_files = save_model(
            model, args.model, metrics, feature_importance, output_dir, logger
        )
        
        # Summary
        logger.info("=" * 70)
        logger.info("✓ TRAINING COMPLETE")
        logger.info("=" * 70)
        logger.info(f"Model: {saved_files['model'].name}")
        logger.info(f"Test R²: {metrics['test']['r2']:.4f}")
        logger.info(f"Test MAE: {metrics['test']['mae']:.4f} W")
        logger.info("=" * 70)
        
        return 0
        
    except Exception as e:
        logger.error(f"✗ Training failed: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())

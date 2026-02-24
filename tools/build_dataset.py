#!/usr/bin/env python3
"""
Solar Power Dataset Builder for ML Training

This script fetches IoT sensor readings from MongoDB, cleans the data,
engineers features, and creates a supervised learning dataset for 
15-minute-ahead power prediction.

Features:
- MongoDB data fetching with flexible filtering
- Data cleaning and validation
- Timezone-aware timestamp handling
- Feature engineering (temporal, rolling, differential)
- Supervised label creation with tolerance matching
- CSV and Parquet export
- Comprehensive data quality reporting

Usage:
    python build_dataset.py --days 7 --out_csv data/solar_dataset.csv

Author: Solar Monitoring System
Version: 1.0.0
"""

import argparse
import json
import logging
import os
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import pandas as pd
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, OperationFailure

try:
    from dotenv import load_dotenv
    HAS_DOTENV = True
except ImportError:
    HAS_DOTENV = False
    print("Warning: python-dotenv not installed. Environment variables won't be loaded from .env file.")

try:
    import pytz
    COLOMBO_TZ = pytz.timezone('Asia/Colombo')
    HAS_PYTZ = True
except ImportError:
    from datetime import timezone
    COLOMBO_TZ = timezone(timedelta(hours=5, minutes=30))
    HAS_PYTZ = False
    print("Warning: pytz not installed. Using UTC+5:30 offset. Install pytz for better timezone support.")


# ============================================================================
# Configuration and Constants
# ============================================================================

@dataclass
class DatasetConfig:
    """Configuration for dataset building"""
    mongo_uri: str
    db_name: str
    collection: str
    device_id: str
    days: int
    horizon_minutes: int
    tolerance_seconds: int
    out_csv: str
    out_parquet: Optional[str]
    out_report: str
    
    # Data validation ranges
    min_temperature: float = 0.0
    max_temperature: float = 60.0
    min_lux: float = 0.0
    min_voltage: float = 0.0
    min_current: float = 0.0
    min_power: float = 0.0
    
    # Feature engineering
    enable_rolling: bool = True
    rolling_window: int = 5
    enable_diffs: bool = True


@dataclass
class DataQualityReport:
    """Data quality metrics"""
    rows_fetched: int
    rows_after_cleaning: int
    rows_after_labeling: int
    rows_dropped_status: int
    rows_dropped_duplicates: int
    rows_dropped_invalid_ranges: int
    rows_dropped_no_label: int
    timestamp_min: str
    timestamp_max: str
    missing_values: Dict[str, int]
    power_stats: Dict[str, float]
    lux_stats: Dict[str, float]
    temperature_stats: Dict[str, float]
    label_match_failures: int
    total_timespan_hours: float


# ============================================================================
# Logging Setup
# ============================================================================

def setup_logging(verbose: bool = False) -> logging.Logger:
    """Configure logging with timestamps and levels"""
    log_level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s | %(levelname)-8s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    return logging.getLogger(__name__)


# ============================================================================
# MongoDB Data Fetching
# ============================================================================

class MongoDBFetcher:
    """Fetch sensor readings from MongoDB"""
    
    def __init__(self, config: DatasetConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.client: Optional[MongoClient] = None
        self.db = None
        self.collection = None
    
    def connect(self) -> bool:
        """Connect to MongoDB"""
        try:
            self.logger.info(f"Connecting to MongoDB: {self.config.db_name}.{self.config.collection}")
            
            self.client = MongoClient(
                self.config.mongo_uri,
                serverSelectionTimeoutMS=5000,
                connectTimeoutMS=10000
            )
            
            # Test connection
            self.client.admin.command('ping')
            
            self.db = self.client[self.config.db_name]
            self.collection = self.db[self.config.collection]
            
            # Get collection stats
            doc_count = self.collection.count_documents({})
            self.logger.info(f"✓ Connected to MongoDB | Total documents: {doc_count:,}")
            
            return True
            
        except ConnectionFailure as e:
            self.logger.error(f"✗ MongoDB connection failed: {e}")
            return False
        except Exception as e:
            self.logger.error(f"✗ Unexpected error connecting to MongoDB: {e}")
            return False
    
    def fetch_readings(self) -> pd.DataFrame:
        """
        Fetch readings from MongoDB for specified time range and device.
        
        Returns DataFrame with raw readings.
        """
        if self.collection is None:
            raise RuntimeError("MongoDB not connected. Call connect() first.")
        
        # Calculate time range
        end_time = datetime.now(COLOMBO_TZ)
        start_time = end_time - timedelta(days=self.config.days)
        
        self.logger.info(f"Fetching readings from {start_time} to {end_time}")
        self.logger.info(f"Device ID: {self.config.device_id} | Days: {self.config.days}")
        
        # Build query - just device_id, no date filter in MongoDB query
        query = {
            "device_id": self.config.device_id
        }
        
        # Fetch ALL documents for this device
        cursor = self.collection.find(query).sort("timestamp", ASCENDING)
        
        # Convert to list
        documents = list(cursor)
        
        self.logger.info(f"✓ Fetched {len(documents):,} total documents from MongoDB")
        
        if len(documents) == 0:
            self.logger.warning("No documents found matching criteria")
            return pd.DataFrame()
        
        # Convert to DataFrame
        df = pd.DataFrame(documents)
        
        # Drop MongoDB _id field
        if '_id' in df.columns:
            df = df.drop(columns=['_id'])
        
        # Parse timestamps WITHOUT date filtering yet
        if not df.empty:
            # Parse timestamps - let pandas auto-detect timezone from ISO format
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Log what we actually have BEFORE any filtering
            self.logger.info(f"Raw data range: {df['timestamp'].min()} to {df['timestamp'].max()}")
            self.logger.info(f"Raw data has {len(df)} rows spanning {(df['timestamp'].max() - df['timestamp'].min()).total_seconds() / 3600:.1f} hours")
            
            # Ensure timezone aware
            if df['timestamp'].dt.tz is None:
                # Localize naive timestamps to Colombo
                df['timestamp'] = df['timestamp'].dt.tz_localize(COLOMBO_TZ)
                self.logger.debug("Localized naive timestamps to Colombo timezone")
            elif HAS_PYTZ:
                # Convert to Colombo if different timezone
                try:
                    df['timestamp'] = df['timestamp'].dt.tz_convert(COLOMBO_TZ)
                    self.logger.debug("Converted timestamps to Colombo timezone")
                except:
                    pass  # Already in correct timezone
            
            # NOW apply date range filter
            self.logger.info(f"Applying date filter: {start_time} to {end_time}")
            
            # SKIP DATE FILTERING - Use ALL available data from MongoDB
            # This is useful when simulator generates future-dated data or you want full dataset
            # Original code applied date filter: df[(timestamp >= start) & (timestamp <= end)]
            # Now we keep ALL fetched data:
            self.logger.info(f"✓ Using ALL {len(df):,} readings (date filter disabled for simulated data)")
            
            # df_filtered = df[(df['timestamp'] >= start_time_cmp) & (df['timestamp'] <= end_time_cmp)]
            # df = df_filtered
        
        return df
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            self.logger.info("MongoDB connection closed")


# ============================================================================
# Data Cleaning and Validation
# ============================================================================

class DataCleaner:
    """Clean and validate sensor readings"""
    
    def __init__(self, config: DatasetConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.stats = {
            'rows_dropped_status': 0,
            'rows_dropped_duplicates': 0,
            'rows_dropped_invalid_ranges': 0
        }
    
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Apply all cleaning steps to raw DataFrame.
        
        Returns cleaned DataFrame.
        """
        self.logger.info(f"Starting data cleaning | Initial rows: {len(df):,}")
        
        if df.empty:
            return df
        
        # Step 1: Parse timestamps
        df = self._parse_timestamps(df)
        
        # Step 2: Filter by status
        df = self._filter_status(df)
        
        # Step 3: Remove duplicates
        df = self._remove_duplicates(df)
        
        # Step 4: Validate ranges
        df = self._validate_ranges(df)
        
        # Step 5: Sort by timestamp
        df = df.sort_values('timestamp').reset_index(drop=True)
        
        self.logger.info(f"✓ Cleaning complete | Final rows: {len(df):,}")
        self.logger.info(f"  - Dropped (status): {self.stats['rows_dropped_status']:,}")
        self.logger.info(f"  - Dropped (duplicates): {self.stats['rows_dropped_duplicates']:,}")
        self.logger.info(f"  - Dropped (invalid ranges): {self.stats['rows_dropped_invalid_ranges']:,}")
        
        return df
    
    def _parse_timestamps(self, df: pd.DataFrame) -> pd.DataFrame:
        """Parse timestamp strings to datetime objects"""
        self.logger.debug("Parsing timestamps...")
        
        try:
            # Parse ISO format timestamps
            df['timestamp'] = pd.to_datetime(df['timestamp'], utc=True)
            
            # Convert to Colombo timezone
            if HAS_PYTZ:
                df['timestamp'] = df['timestamp'].dt.tz_convert(COLOMBO_TZ)
            else:
                # Convert to UTC+5:30
                df['timestamp'] = df['timestamp'].dt.tz_convert(COLOMBO_TZ)
            
            self.logger.debug(f"✓ Parsed {len(df)} timestamps")
            
        except Exception as e:
            self.logger.error(f"Error parsing timestamps: {e}")
            raise
        
        return df
    
    def _filter_status(self, df: pd.DataFrame) -> pd.DataFrame:
        """Keep only readings with status == 'online'"""
        initial_count = len(df)
        
        # Keep only online status
        df = df[df['status'] == 'online'].copy()
        
        dropped = initial_count - len(df)
        self.stats['rows_dropped_status'] = dropped
        
        if dropped > 0:
            self.logger.debug(f"Filtered out {dropped} non-online readings")
        
        return df
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate timestamps"""
        initial_count = len(df)
        
        # Keep first occurrence of duplicate timestamps
        df = df.drop_duplicates(subset=['timestamp'], keep='first')
        
        dropped = initial_count - len(df)
        self.stats['rows_dropped_duplicates'] = dropped
        
        if dropped > 0:
            self.logger.debug(f"Removed {dropped} duplicate timestamps")
        
        return df
    
    def _validate_ranges(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove readings with impossible/invalid values"""
        initial_count = len(df)
        
        # Build boolean mask for valid rows
        valid_mask = (
            (df['lux'] >= self.config.min_lux) &
            (df['voltage'] >= self.config.min_voltage) &
            (df['current'] >= self.config.min_current) &
            (df['power'] >= self.config.min_power) &
            (df['temperature'] >= self.config.min_temperature) &
            (df['temperature'] <= self.config.max_temperature)
        )
        
        df = df[valid_mask].copy()
        
        dropped = initial_count - len(df)
        self.stats['rows_dropped_invalid_ranges'] = dropped
        
        if dropped > 0:
            self.logger.debug(f"Removed {dropped} readings with invalid ranges")
        
        return df


# ============================================================================
# Feature Engineering
# ============================================================================

class FeatureEngineer:
    """Create features from cleaned sensor data"""
    
    def __init__(self, config: DatasetConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
    
    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create all features from cleaned data.
        
        Returns DataFrame with engineered features.
        """
        self.logger.info("Starting feature engineering...")
        
        if df.empty:
            return df
        
        # Temporal features
        df = self._add_temporal_features(df)
        
        # Binary features
        df = self._add_binary_features(df)
        
        # Differential features
        if self.config.enable_diffs:
            df = self._add_differential_features(df)
        
        # Rolling features
        if self.config.enable_rolling:
            df = self._add_rolling_features(df)
        
        self.logger.info(f"✓ Feature engineering complete | Features: {len(df.columns)}")
        
        return df
    
    def _add_temporal_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract temporal features from timestamp"""
        self.logger.debug("Adding temporal features...")
        
        df['hour'] = df['timestamp'].dt.hour
        df['minute'] = df['timestamp'].dt.minute
        df['day_of_week'] = df['timestamp'].dt.dayofweek  # 0=Monday, 6=Sunday
        
        return df
    
    def _add_binary_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create binary indicator features"""
        self.logger.debug("Adding binary features...")
        
        # Fan status: on=1, off=0
        df['fan_on'] = (df['fan_status'] == 'on').astype(int)
        
        return df
    
    def _add_differential_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create difference features (current - previous).
        
        Important: These are past-looking only (no data leakage).
        """
        self.logger.debug("Adding differential features...")
        
        # Power difference
        df['power_diff'] = df['power'].diff()
        
        # Lux difference
        df['lux_diff'] = df['lux'].diff()
        
        # First row will have NaN diffs, fill with 0
        df['power_diff'] = df['power_diff'].fillna(0)
        df['lux_diff'] = df['lux_diff'].fillna(0)
        
        return df
    
    def _add_rolling_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create rolling window features (past-looking only).
        
        Important: min_periods=1 ensures no NaN at the start.
        """
        self.logger.debug(f"Adding rolling features (window={self.config.rolling_window})...")
        
        window = self.config.rolling_window
        
        # Rolling mean power (past values only)
        df['rolling_mean_power_5'] = df['power'].rolling(
            window=window,
            min_periods=1
        ).mean()
        
        # Rolling mean lux (past values only)
        df['rolling_mean_lux_5'] = df['lux'].rolling(
            window=window,
            min_periods=1
        ).mean()
        
        return df


# ============================================================================
# Label Creation (Supervised Learning)
# ============================================================================

class LabelCreator:
    """Create target labels for supervised learning"""
    
    def __init__(self, config: DatasetConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
        self.match_failures = 0
    
    def create_labels(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Create target_power_t_plus_15 column by matching future timestamps.
        
        For each row at time t, find the row at time t + horizon_minutes
        within tolerance_seconds and use its power value as the label.
        
        Rows without valid future matches are dropped.
        
        Returns labeled DataFrame.
        """
        self.logger.info(f"Creating labels | Horizon: {self.config.horizon_minutes} min | "
                        f"Tolerance: ±{self.config.tolerance_seconds} sec")
        
        if df.empty:
            return df
        
        initial_count = len(df)
        
        # Calculate target timestamps for each row
        horizon_delta = timedelta(minutes=self.config.horizon_minutes)
        tolerance_delta = timedelta(seconds=self.config.tolerance_seconds)
        
        target_timestamps = df['timestamp'] + horizon_delta
        
        # Create target column (initially NaN)
        df['target_power_t_plus_15'] = np.nan
        
        # Build a lookup dictionary: timestamp -> power
        # Use timestamp as string for exact matching
        timestamp_to_power = dict(zip(df['timestamp'], df['power']))
        
        # For each row, find matching future timestamp
        matched_count = 0
        
        for idx, target_ts in enumerate(target_timestamps):
            # Search window: target_ts ± tolerance
            search_start = target_ts - tolerance_delta
            search_end = target_ts + tolerance_delta
            
            # Find rows within tolerance window
            matches = df[
                (df['timestamp'] >= search_start) &
                (df['timestamp'] <= search_end)
            ]
            
            if not matches.empty:
                # Use closest match
                time_diffs = (matches['timestamp'] - target_ts).abs()
                closest_idx = time_diffs.idxmin()
                
                df.loc[idx, 'target_power_t_plus_15'] = matches.loc[closest_idx, 'power']
                matched_count += 1
        
        # Drop rows without valid labels
        df_labeled = df.dropna(subset=['target_power_t_plus_15']).copy()
        
        self.match_failures = initial_count - matched_count
        rows_dropped = initial_count - len(df_labeled)
        
        self.logger.info(f"✓ Label creation complete | Matched: {matched_count:,} | "
                        f"Dropped: {rows_dropped:,}")
        
        if self.match_failures > 0:
            self.logger.warning(f"⚠ {self.match_failures:,} rows could not be matched to future labels")
        
        return df_labeled


# ============================================================================
# Dataset Export
# ============================================================================

class DatasetExporter:
    """Export dataset to various formats"""
    
    def __init__(self, config: DatasetConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
    
    def export(self, df: pd.DataFrame) -> None:
        """Export dataset to CSV and optionally Parquet"""
        
        if df.empty:
            self.logger.warning("Cannot export empty dataset")
            return
        
        # Select final columns in desired order
        final_columns = [
            'timestamp',
            'hour', 'minute', 'day_of_week',
            'servo_angle', 'temperature', 'humidity',
            'lux', 'voltage', 'current', 'power',
            'fan_on'
        ]
        
        # Add optional features if they exist
        optional_columns = [
            'power_diff', 'lux_diff',
            'rolling_mean_power_5', 'rolling_mean_lux_5'
        ]
        
        for col in optional_columns:
            if col in df.columns:
                final_columns.append(col)
        
        # Add target column
        final_columns.append('target_power_t_plus_15')
        
        # Select columns
        df_export = df[final_columns].copy()
        
        # Convert timestamp to ISO string for CSV
        df_export['timestamp'] = df_export['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S%z')
        
        # Rename timestamp column to 'ts' for brevity
        df_export = df_export.rename(columns={'timestamp': 'ts'})
        
        # Export CSV
        self._export_csv(df_export)
        
        # Export Parquet if configured
        if self.config.out_parquet:
            self._export_parquet(df_export)
    
    def _export_csv(self, df: pd.DataFrame) -> None:
        """Export to CSV"""
        # Create output directory if needed
        out_path = Path(self.config.out_csv)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Exporting CSV to: {self.config.out_csv}")
        
        df.to_csv(self.config.out_csv, index=False)
        
        file_size_mb = out_path.stat().st_size / (1024 * 1024)
        self.logger.info(f"✓ CSV exported | Rows: {len(df):,} | Size: {file_size_mb:.2f} MB")
    
    def _export_parquet(self, df: pd.DataFrame) -> None:
        """Export to Parquet (requires pyarrow)"""
        try:
            # Create output directory if needed
            out_path = Path(self.config.out_parquet)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            
            self.logger.info(f"Exporting Parquet to: {self.config.out_parquet}")
            
            df.to_parquet(self.config.out_parquet, index=False, compression='snappy')
            
            file_size_mb = out_path.stat().st_size / (1024 * 1024)
            self.logger.info(f"✓ Parquet exported | Rows: {len(df):,} | Size: {file_size_mb:.2f} MB")
            
        except ImportError:
            self.logger.warning("pyarrow not installed. Skipping Parquet export.")
        except Exception as e:
            self.logger.error(f"Error exporting Parquet: {e}")


# ============================================================================
# Data Quality Report
# ============================================================================

class ReportGenerator:
    """Generate data quality report"""
    
    def __init__(self, config: DatasetConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
    
    def generate_report(
        self,
        df_raw: pd.DataFrame,
        df_cleaned: pd.DataFrame,
        df_labeled: pd.DataFrame,
        cleaner_stats: Dict[str, int],
        match_failures: int
    ) -> DataQualityReport:
        """
        Generate comprehensive data quality report.
        
        Returns DataQualityReport object.
        """
        self.logger.info("Generating data quality report...")
        
        # Calculate metrics
        rows_fetched = len(df_raw)
        rows_after_cleaning = len(df_cleaned)
        rows_after_labeling = len(df_labeled)
        
        # Missing values in final dataset
        missing_values = df_labeled.isnull().sum().to_dict()
        missing_values = {k: int(v) for k, v in missing_values.items() if v > 0}
        
        # Timestamp range
        if not df_labeled.empty:
            timestamp_min = df_labeled['timestamp'].min().isoformat()
            timestamp_max = df_labeled['timestamp'].max().isoformat()
            timespan_hours = (df_labeled['timestamp'].max() - df_labeled['timestamp'].min()).total_seconds() / 3600
        else:
            timestamp_min = "N/A"
            timestamp_max = "N/A"
            timespan_hours = 0.0
        
        # Statistics
        power_stats = self._compute_stats(df_labeled, 'power')
        lux_stats = self._compute_stats(df_labeled, 'lux')
        temperature_stats = self._compute_stats(df_labeled, 'temperature')
        
        report = DataQualityReport(
            rows_fetched=rows_fetched,
            rows_after_cleaning=rows_after_cleaning,
            rows_after_labeling=rows_after_labeling,
            rows_dropped_status=cleaner_stats['rows_dropped_status'],
            rows_dropped_duplicates=cleaner_stats['rows_dropped_duplicates'],
            rows_dropped_invalid_ranges=cleaner_stats['rows_dropped_invalid_ranges'],
            rows_dropped_no_label=rows_after_cleaning - rows_after_labeling,
            timestamp_min=timestamp_min,
            timestamp_max=timestamp_max,
            missing_values=missing_values,
            power_stats=power_stats,
            lux_stats=lux_stats,
            temperature_stats=temperature_stats,
            label_match_failures=match_failures,
            total_timespan_hours=round(timespan_hours, 2)
        )
        
        self.logger.info("✓ Report generated")
        
        return report
    
    def _compute_stats(self, df: pd.DataFrame, column: str) -> Dict[str, float]:
        """Compute basic statistics for a column"""
        if df.empty or column not in df.columns:
            return {}
        
        series = df[column]
        
        return {
            'mean': round(float(series.mean()), 3),
            'std': round(float(series.std()), 3),
            'min': round(float(series.min()), 3),
            'max': round(float(series.max()), 3),
            'median': round(float(series.median()), 3)
        }
    
    def save_report(self, report: DataQualityReport) -> None:
        """Save report to JSON file"""
        # Create output directory
        out_path = Path(self.config.out_report)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        
        self.logger.info(f"Saving report to: {self.config.out_report}")
        
        # Convert to dict and save
        report_dict = asdict(report)
        report_dict['generated_at'] = datetime.now(COLOMBO_TZ).isoformat()
        report_dict['config'] = {
            'device_id': self.config.device_id,
            'days': self.config.days,
            'horizon_minutes': self.config.horizon_minutes,
            'tolerance_seconds': self.config.tolerance_seconds
        }
        
        with open(self.config.out_report, 'w') as f:
            json.dump(report_dict, f, indent=2)
        
        self.logger.info("✓ Report saved")
        
        # Print summary to console
        self._print_summary(report)
    
    def _print_summary(self, report: DataQualityReport) -> None:
        """Print report summary to console"""
        print("\n" + "=" * 70)
        print("DATA QUALITY REPORT SUMMARY")
        print("=" * 70)
        print(f"Rows fetched:           {report.rows_fetched:,}")
        print(f"Rows after cleaning:    {report.rows_after_cleaning:,}")
        print(f"Rows after labeling:    {report.rows_after_labeling:,}")
        print(f"Total timespan:         {report.total_timespan_hours:.2f} hours")
        print()
        print("Rows Dropped:")
        print(f"  - Status filter:      {report.rows_dropped_status:,}")
        print(f"  - Duplicates:         {report.rows_dropped_duplicates:,}")
        print(f"  - Invalid ranges:     {report.rows_dropped_invalid_ranges:,}")
        print(f"  - No future label:    {report.rows_dropped_no_label:,}")
        print()
        print(f"Timestamp range:        {report.timestamp_min} to {report.timestamp_max}")
        print()
        print("Power Statistics:")
        for k, v in report.power_stats.items():
            print(f"  {k:8s}: {v:8.3f}")
        print()
        print("Lux Statistics:")
        for k, v in report.lux_stats.items():
            print(f"  {k:8s}: {v:8.1f}")
        print()
        print("Temperature Statistics:")
        for k, v in report.temperature_stats.items():
            print(f"  {k:8s}: {v:8.1f} °C")
        print("=" * 70)


# ============================================================================
# Main Pipeline
# ============================================================================

class DatasetBuilder:
    """Main pipeline orchestrator"""
    
    def __init__(self, config: DatasetConfig, logger: logging.Logger):
        self.config = config
        self.logger = logger
    
    def build(self) -> bool:
        """
        Execute full dataset building pipeline.
        
        Returns True if successful, False otherwise.
        """
        self.logger.info("=" * 70)
        self.logger.info("SOLAR POWER ML DATASET BUILDER")
        self.logger.info("=" * 70)
        
        try:
            # Step 1: Fetch data from MongoDB
            fetcher = MongoDBFetcher(self.config, self.logger)
            
            if not fetcher.connect():
                return False
            
            df_raw = fetcher.fetch_readings()
            fetcher.close()
            
            if df_raw.empty:
                self.logger.error("No data fetched. Cannot build dataset.")
                return False
            
            # Step 2: Clean data
            cleaner = DataCleaner(self.config, self.logger)
            df_cleaned = cleaner.clean(df_raw)
            
            if df_cleaned.empty:
                self.logger.error("All data was filtered out during cleaning. Cannot build dataset.")
                return False
            
            # Step 3: Engineer features
            engineer = FeatureEngineer(self.config, self.logger)
            df_features = engineer.engineer_features(df_cleaned)
            
            # Step 4: Create labels
            labeler = LabelCreator(self.config, self.logger)
            df_labeled = labeler.create_labels(df_features)
            
            if df_labeled.empty:
                self.logger.error("No valid labels could be created. Cannot build dataset.")
                return False
            
            # Step 5: Export dataset
            exporter = DatasetExporter(self.config, self.logger)
            exporter.export(df_labeled)
            
            # Step 6: Generate report
            reporter = ReportGenerator(self.config, self.logger)
            report = reporter.generate_report(
                df_raw=df_raw,
                df_cleaned=df_cleaned,
                df_labeled=df_labeled,
                cleaner_stats=cleaner.stats,
                match_failures=labeler.match_failures
            )
            reporter.save_report(report)
            
            self.logger.info("=" * 70)
            self.logger.info("✓ Dataset building complete!")
            self.logger.info("=" * 70)
            
            return True
            
        except Exception as e:
            self.logger.error(f"✗ Dataset building failed: {e}", exc_info=True)
            return False


# ============================================================================
# CLI Interface
# ============================================================================

def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Build ML dataset from solar tracker IoT readings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build dataset from last 7 days
  python build_dataset.py --days 7 --out_csv data/solar_dataset.csv

  # Build with custom horizon and tolerance
  python build_dataset.py --days 14 --horizon_minutes 30 --tolerance_seconds 60

  # Use custom MongoDB URI
  python build_dataset.py --mongo_uri "mongodb://localhost:27017" --days 7

  # Export both CSV and Parquet
  python build_dataset.py --days 7 --out_csv data/solar.csv --out_parquet data/solar.parquet

Notes:
  - MongoDB URI can be set via --mongo_uri or MONGODB_URI env variable
  - Use .env file for secrets (requires python-dotenv)
  - Output directories are created automatically
  - Install pytz for proper timezone support
  - Install pyarrow for Parquet export
        """
    )
    
    parser.add_argument(
        '--mongo_uri',
        type=str,
        help='MongoDB connection URI (default: from MONGODB_URI env variable)'
    )
    
    parser.add_argument(
        '--db_name',
        type=str,
        default='solar_db',
        help='MongoDB database name (default: solar_db)'
    )
    
    parser.add_argument(
        '--collection',
        type=str,
        default='readings_raw',
        help='MongoDB collection name (default: readings_raw)'
    )
    
    parser.add_argument(
        '--device_id',
        type=str,
        default='tracker01',
        help='Device ID to filter readings (default: tracker01)'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days to fetch (default: 7)'
    )
    
    parser.add_argument(
        '--horizon_minutes',
        type=int,
        default=15,
        help='Prediction horizon in minutes (default: 15)'
    )
    
    parser.add_argument(
        '--tolerance_seconds',
        type=int,
        default=30,
        help='Tolerance for matching future labels in seconds (default: 30)'
    )
    
    parser.add_argument(
        '--out_csv',
        type=str,
        default='data/solar_dataset.csv',
        help='Output CSV file path (default: data/solar_dataset.csv)'
    )
    
    parser.add_argument(
        '--out_parquet',
        type=str,
        help='Output Parquet file path (optional, requires pyarrow)'
    )
    
    parser.add_argument(
        '--out_report',
        type=str,
        default='data/dataset_report.json',
        help='Output report JSON file path (default: data/dataset_report.json)'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose debug logging'
    )
    
    return parser.parse_args()


def main():
    """Main entry point"""
    # Load environment variables from .env if available
    if HAS_DOTENV:
        load_dotenv()
    
    args = parse_arguments()
    
    # Setup logging
    logger = setup_logging(args.verbose)
    
    # Get MongoDB URI
    mongo_uri = args.mongo_uri or os.getenv('MONGODB_URI')
    
    if not mongo_uri:
        logger.error("MongoDB URI not provided. Use --mongo_uri or set MONGODB_URI environment variable.")
        sys.exit(1)
    
    # Create configuration
    config = DatasetConfig(
        mongo_uri=mongo_uri,
        db_name=args.db_name,
        collection=args.collection,
        device_id=args.device_id,
        days=args.days,
        horizon_minutes=args.horizon_minutes,
        tolerance_seconds=args.tolerance_seconds,
        out_csv=args.out_csv,
        out_parquet=args.out_parquet,
        out_report=args.out_report
    )
    
    # Build dataset
    builder = DatasetBuilder(config, logger)
    success = builder.build()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

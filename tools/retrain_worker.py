#!/usr/bin/env python3
"""
Model Retraining Worker Script

Standalone script for scheduled model retraining.
Can be run manually or scheduled via cron/Task Scheduler.

Usage:
    # Run once
    python retrain_worker.py --device tracker01 --days 7
    
    # Run in scheduler mode (keeps running)
    python retrain_worker.py --schedule --device tracker01
    
    # Dry run (no actual training)
    python retrain_worker.py --device tracker01 --dry-run
"""

import sys
import os
import argparse
import time
import signal
from datetime import datetime, time as dt_time
from pathlib import Path

# Add Backend to Python path
backend_dir = Path(__file__).parent.parent / "Backend"
sys.path.insert(0, str(backend_dir))

import logging
from typing import Optional
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

# Import after path setup
from app.core.config import get_settings
from app.services.retrain_service import ModelRetrainService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)-8s | %(name)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

# Global flag for graceful shutdown
shutdown_requested = False


def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    global shutdown_requested
    logger.info("Shutdown signal received. Finishing current operation...")
    shutdown_requested = True


def connect_mongodb(uri: str, db_name: str) -> tuple:
    """
    Connect to MongoDB and return collections.
    
    Args:
        uri: MongoDB connection URI
        db_name: Database name
        
    Returns:
        Tuple of (readings_collection, model_runs_collection)
    """
    try:
        logger.info(f"Connecting to MongoDB: {db_name}")
        client = MongoClient(uri, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.admin.command('ping')
        logger.info("✓ MongoDB connection established")
        
        db = client[db_name]
        readings_collection = db[settings.collection_readings]
        model_runs_collection = db[settings.collection_model_runs]
        
        return readings_collection, model_runs_collection
        
    except ConnectionFailure as e:
        logger.error(f"✗ MongoDB connection failed: {e}")
        raise
    except Exception as e:
        logger.error(f"✗ Error connecting to MongoDB: {e}")
        raise


def run_retraining(
    device_id: str,
    days: int,
    dry_run: bool = False
):
    """
    Execute model retraining.
    
    Args:
        device_id: Device identifier
        days: Days of data to use
        dry_run: If True, skip actual training
    """
    settings = get_settings()
    
    if dry_run:
        logger.info("=" * 70)
        logger.info("DRY RUN MODE - No actual training will occur")
        logger.info("=" * 70)
        return {
            'success': True,
            'dry_run': True,
            'message': 'Dry run completed'
        }
    
    try:
        # Connect to MongoDB
        readings_coll, model_runs_coll = connect_mongodb(
            settings.mongodb_url,
            settings.mongodb_db_name
        )
        
        # Create retraining service
        retrain_service = ModelRetrainService(
            readings_collection=readings_coll,
            model_runs_collection=model_runs_coll
        )
        
        # Execute retraining
        logger.info(f"Starting retraining for device: {device_id}")
        result = retrain_service.retrain_model(
            device_id=device_id,
            days=days
        )
        
        if result['success']:
            logger.info("✓ Retraining completed successfully")
            if result['promoted']:
                logger.info(f"✓ Model promoted: {result['promotion_reason']}")
            else:
                logger.info(f"⚠ Model NOT promoted: {result['promotion_reason']}")
        else:
            logger.error(f"✗ Retraining failed: {result.get('error')}")
        
        return result
        
    except Exception as e:
        logger.error(f"✗ Retraining execution failed: {e}", exc_info=True)
        return {
            'success': False,
            'error': str(e)
        }


def parse_time(time_str: str) -> dt_time:
    """
    Parse time string in HH:MM format.
    
    Args:
        time_str: Time string (e.g., "18:30")
        
    Returns:
        datetime.time object
    """
    try:
        hour, minute = map(int, time_str.split(':'))
        return dt_time(hour=hour, minute=minute)
    except Exception as e:
        raise ValueError(f"Invalid time format '{time_str}'. Expected HH:MM") from e


def should_run_now(target_time: dt_time, last_run: Optional[datetime]) -> bool:
    """
    Check if retraining should run now.
    
    Args:
        target_time: Target time of day to run
        last_run: Last run timestamp (None if never run)
        
    Returns:
        True if should run now
    """
    now = datetime.now()
    current_time = now.time()
    
    # Check if we're past the target time today
    if current_time < target_time:
        return False
    
    # Check if already ran today
    if last_run is not None:
        if last_run.date() == now.date():
            return False
    
    return True


def scheduler_loop(
    device_id: str,
    days: int,
    target_time: dt_time,
    check_interval: int = 60
):
    """
    Continuously check and run retraining at scheduled time.
    
    Args:
        device_id: Device identifier
        days: Days of data to use
        target_time: Time of day to run retraining
        check_interval: Seconds between checks
    """
    global shutdown_requested
    
    logger.info("=" * 70)
    logger.info("MODEL RETRAINING SCHEDULER STARTED")
    logger.info("=" * 70)
    logger.info(f"Device: {device_id}")
    logger.info(f"Days: {days}")
    logger.info(f"Scheduled time: {target_time.strftime('%H:%M')}")
    logger.info(f"Check interval: {check_interval} seconds")
    logger.info(f"Timezone: {settings.timezone}")
    logger.info("=" * 70)
    logger.info("Press Ctrl+C to stop")
    logger.info("=" * 70)
    
    last_run = None
    
    while not shutdown_requested:
        try:
            if should_run_now(target_time, last_run):
                logger.info("Scheduled time reached - starting retraining...")
                
                result = run_retraining(device_id, days, dry_run=False)
                
                if result['success']:
                    last_run = datetime.now()
                    logger.info(f"Next run scheduled for tomorrow at {target_time.strftime('%H:%M')}")
                else:
                    logger.error("Retraining failed, will retry tomorrow")
                    last_run = datetime.now()  # Still mark as run to avoid continuous retries
            
            # Sleep and check periodically
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            break
        except Exception as e:
            logger.error(f"Error in scheduler loop: {e}", exc_info=True)
            time.sleep(check_interval)
    
    logger.info("Scheduler stopped")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Model Retraining Worker',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run once
  python retrain_worker.py --device tracker01 --days 7
  
  # Run in scheduler mode
  python retrain_worker.py --schedule --device tracker01 --time 18:30
  
  # Dry run
  python retrain_worker.py --device tracker01 --dry-run
  
  # Custom interval
  python retrain_worker.py --schedule --device tracker01 --check-interval 300
        """
    )
    
    parser.add_argument(
        '--device',
        type=str,
        required=True,
        help='Device ID to retrain model for (e.g., tracker01)'
    )
    
    parser.add_argument(
        '--days',
        type=int,
        default=7,
        help='Number of days of data to use (default: 7)'
    )
    
    parser.add_argument(
        '--schedule',
        action='store_true',
        help='Run in scheduler mode (keeps running)'
    )
    
    parser.add_argument(
        '--time',
        type=str,
        default=None,
        help='Time of day to run in HH:MM format (default: from .env RETRAIN_TIME)'
    )
    
    parser.add_argument(
        '--check-interval',
        type=int,
        default=60,
        help='Seconds between schedule checks (default: 60)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode - no actual training'
    )
    
    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    # Set log level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Load settings
    global settings
    settings = get_settings()
    
    try:
        if args.schedule:
            # Parse target time
            time_str = args.time if args.time else settings.retrain_time
            target_time = parse_time(time_str)
            
            # Run scheduler
            scheduler_loop(
                device_id=args.device,
                days=args.days,
                target_time=target_time,
                check_interval=args.check_interval
            )
        else:
            # Run once
            result = run_retraining(
                device_id=args.device,
                days=args.days,
                dry_run=args.dry_run
            )
            
            # Exit with appropriate code
            sys.exit(0 if result['success'] else 1)
    
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(130)  # Standard exit code for Ctrl+C
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()

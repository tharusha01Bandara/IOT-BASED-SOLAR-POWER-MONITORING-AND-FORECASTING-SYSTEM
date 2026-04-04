import os
import sys
import json
import asyncio
from datetime import datetime
from paho.mqtt.client import Client, MQTTMessage
from paho.mqtt.enums import CallbackAPIVersion
from pydantic import ValidationError

# Ensure app imports work when running as standalone script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db.mongodb import mongodb_client
from app.schemas.readings import ReadingCreate
from app.services.readings_service import ReadingsService
from app.services.ml_service import MLService

logger = get_logger(__name__)
settings = get_settings()

MQTT_BROKER = os.getenv("MQTT_BROKER", "test.mosquitto.org")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "solarxxx5678934/tracker01/readings")

def on_connect(client: Client, userdata, flags, rc):
    """Callback when the client connects to the broker."""
    if rc == 0:
        logger.info(f"Connected to MQTT Broker at {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
        logger.info(f"Subscribed to topic: {MQTT_TOPIC}")
    else:
        logger.error(f"Failed to connect, return code {rc}")

def normalize_payload(payload: dict) -> dict:
    """Normalize payload before Pydantic validation."""
    # Move ESP32 string timestamp to device_timestamp
    if "timestamp" in payload:
        payload["device_timestamp"] = str(payload.pop("timestamp"))
    
    # Let Pydantic default_factory create datetime.utcnow() for 'timestamp'
    
    # Handle 'ok'/'ON' values gracefully
    if "status" in payload and payload["status"].lower() == "ok":
        payload["status"] = "ok" # allowed by our schema change
    
    if "fan_status" in payload and payload["fan_status"].upper() == "ON":
        payload["fan_status"] = "on" # or whatever is valid

    return payload

def on_message(client: Client, userdata, msg: MQTTMessage):
    """Callback when a PUBLISH message is received from the server."""
    logger.debug(f"Received message on topic {msg.topic}")
    
    try:
        payload = json.loads(msg.payload.decode('utf-8'))
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON payload: {e}")
        return

    # Normalize payload
    payload = normalize_payload(payload)

    # Validate using Pydantic schema
    try:
        reading_data = ReadingCreate(**payload)
        reading_dict = reading_data.model_dump()
    except ValidationError as e:
        logger.error(f"Validation error for incoming payload: {e.errors()}")
        return

    # Database initialization
    if mongodb_client.database is None:
        logger.error("Database connection not initialized")
        return

    readings_collection = mongodb_client.get_collection(settings.collection_readings)
    predictions_collection = mongodb_client.get_collection(settings.collection_predictions)
    
    readings_service = ReadingsService(readings_collection)
    ml_service = MLService(readings_collection)

    try:
        # We need to run the async create_reading method in a synchronous context
        # Or change it if readings_service is sync. Let's run it async.
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        result = loop.run_until_complete(readings_service.create_reading(reading_dict))
        loop.close()
        
        logger.info(f"Successfully inserted reading: {result['inserted_id']}")
        
        # Trigger ML prediction
        try:
            prediction_result = ml_service.predict_next_15min(
                reading=reading_dict,
                device_id=reading_data.device_id
            )
            
            # Store prediction
            prediction_doc = {
                "device_id": reading_data.device_id,
                "timestamp": prediction_result['predicted_at'],
                "predicted_power_15min": prediction_result['predicted_power_15min'],
                "confidence": prediction_result['confidence'],
                "model_version": prediction_result['model_version'],
                "current_power": reading_data.power,
                "created_at": datetime.utcnow()
            }
            predictions_collection.insert_one(prediction_doc)
            logger.info("Successfully stored prediction")

        except Exception as ml_err:
            logger.error(f"ML Prediction failed: {ml_err}")

    except Exception as db_err:
        logger.error(f"Database operation failed: {db_err}")

def start_subscriber():
    """Initialize database and start MQTT loop."""
    logger.info("Starting MQTT Subscriber...")
    mongodb_client.connect(settings)

    client = Client(CallbackAPIVersion.VERSION1)
    client.on_connect = on_connect
    client.on_message = on_message
    
    # Enable auth if needed
    # client.username_pw_set("user", "pass")
    
    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_forever()
    except Exception as e:
        logger.error(f"Error starting MQTT client: {e}")
        sys.exit(1)

if __name__ == "__main__":
    start_subscriber()
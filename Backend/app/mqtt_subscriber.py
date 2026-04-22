import os
import sys
import json
import asyncio
from datetime import datetime

from paho.mqtt.client import Client, MQTTMessage
from paho.mqtt.enums import CallbackAPIVersion
from pydantic import ValidationError

# Ensure app imports work when running as standalone script
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.config import get_settings
from app.db.mongodb import mongodb_client
from app.schemas.readings import ReadingCreate
from app.services.readings_service import ReadingsService
from app.services.ml_service import MLService

settings = get_settings()

MQTT_BROKER = os.getenv("MQTT_BROKER", "broker.hivemq.com")
MQTT_PORT = int(os.getenv("MQTT_PORT", 1883))
MQTT_TOPIC = os.getenv("MQTT_TOPIC", "solarxxx5678934/tracker01/readings")


def normalize_payload(payload: dict) -> dict:
    normalized = payload.copy()

    if "timestamp" in normalized:
        normalized["device_timestamp"] = str(normalized.pop("timestamp"))

    if "fan_status" in normalized and isinstance(normalized["fan_status"], str):
        normalized["fan_status"] = normalized["fan_status"].upper()

    if "status" in normalized and isinstance(normalized["status"], str):
        normalized["status"] = normalized["status"].lower()

    normalized.setdefault("lux", 0.0)
    normalized.setdefault("ldr_left", None)
    normalized.setdefault("ldr_right", None)
    normalized.setdefault("fan_status", "OFF")
    normalized.setdefault("status", "ok")

    return normalized


def on_connect(client: Client, userdata, flags, rc):
    print(f"on_connect called, rc = {rc}")

    if rc == 0:
        print(f"✅ Connected to MQTT Broker at {MQTT_BROKER}:{MQTT_PORT}")
        client.subscribe(MQTT_TOPIC)
        print(f"✅ Subscribed to topic: {MQTT_TOPIC}")
    else:
        print(f"❌ Failed to connect to MQTT broker, return code = {rc}")


def on_message(client: Client, userdata, msg: MQTTMessage):
    print(f"\n📩 Message received on topic: {msg.topic}")

    try:
        raw_payload = msg.payload.decode("utf-8")
        print(f"Raw payload: {raw_payload}")
        payload = json.loads(raw_payload)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON payload: {e}")
        return
    except Exception as e:
        print(f"❌ Unexpected error while decoding message: {e}")
        return

    payload = normalize_payload(payload)
    print(f"Normalized payload: {payload}")

    try:
        reading_data = ReadingCreate(**payload)
        reading_dict = reading_data.model_dump()
        print("✅ Pydantic validation successful")
    except ValidationError as e:
        print(f"❌ Pydantic validation failed: {e.errors()}")
        return

    if mongodb_client.database is None:
        print("❌ MongoDB database connection is not initialized")
        return

    try:
        readings_collection = mongodb_client.get_collection(settings.collection_readings)
        predictions_collection = mongodb_client.get_collection(settings.collection_predictions)

        readings_service = ReadingsService(readings_collection)
        ml_service = MLService(readings_collection)

        result = asyncio.run(readings_service.create_reading(reading_dict))
        print(f"✅ Inserted reading with ID: {result['inserted_id']}")
    except Exception as db_err:
        print(f"❌ Failed to store reading in database: {db_err}")
        return

    try:
        prediction_result = ml_service.predict_next_15min(
            reading=reading_dict,
            device_id=reading_data.device_id
        )

        prediction_doc = {
            "device_id": reading_data.device_id,
            "timestamp": prediction_result["predicted_at"],
            "predicted_power_15min": prediction_result["predicted_power_15min"],
            "confidence": prediction_result["confidence"],
            "model_version": prediction_result["model_version"],
            "current_power": reading_data.power,
            "created_at": datetime.utcnow(),
        }

        predictions_collection.insert_one(prediction_doc)
        print("✅ Stored ML prediction successfully")
    except Exception as ml_err:
        print(f"❌ ML prediction failed: {ml_err}")


def start_subscriber():
    print("1. Starting MQTT Subscriber...")
    print(f"2. MongoDB URL = {settings.mongodb_url}")
    print(f"3. MongoDB DB Name = {settings.mongodb_db_name}")
    print(f"4. MQTT Broker = {MQTT_BROKER}")
    print(f"5. MQTT Port = {MQTT_PORT}")
    print(f"6. MQTT Topic = {MQTT_TOPIC}")

    try:
        print("7. Connecting to MongoDB...")
        mongodb_client.connect(settings)
        print("8. ✅ MongoDB connected successfully")
    except Exception as e:
        print(f"❌ Failed to connect to MongoDB: {e}")
        sys.exit(1)

    print("9. Creating MQTT client...")
    client = Client(callback_api_version=CallbackAPIVersion.VERSION1)

    client.on_connect = on_connect
    client.on_message = on_message

    try:
        print(f"10. Connecting to broker {MQTT_BROKER}:{MQTT_PORT} ...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        print("11. connect() returned successfully")
        print("12. Waiting for MQTT messages...")
        client.loop_forever()
    except Exception as e:
        print(f"❌ Failed to start MQTT client: {e}")
        sys.exit(1)


if __name__ == "__main__":
    start_subscriber()
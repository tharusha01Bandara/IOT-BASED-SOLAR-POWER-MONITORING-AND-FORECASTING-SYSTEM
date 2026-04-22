import json
import time
import random
from datetime import datetime
import paho.mqtt.client as mqtt

# -------- MQTT CONFIG --------
BROKER = "broker.hivemq.com"
PORT = 1883
TOPIC = "solarxxy5678934/tracker01/readings"

client = mqtt.Client()
client.connect(BROKER, PORT, 60)

print("Simulator started... sending data")

servo_angle = 90
fan_on = False

while True:
    now = datetime.utcnow().isoformat()

    # -------- Generate realistic values --------
    lux = random.uniform(20000, 90000)

    temperature = random.uniform(28, 45)
    humidity = random.uniform(60, 90)

    voltage = random.uniform(5.5, 7.0)
    current = random.uniform(0.2, 0.8)

    power = voltage * current

    # Servo small movement
    servo_angle += random.randint(-2, 2)
    servo_angle = max(75, min(105, servo_angle))

    # Fan logic
    if temperature > 40:
        fan_on = True
    elif temperature < 38:
        fan_on = False

    fan_status = "ON" if fan_on else "OFF"

    # LDR fake values (optional)
    ldr_left = int(lux / 30 + random.randint(-50, 50))
    ldr_right = int(lux / 30 + random.randint(-50, 50))

    # Status (rare invalid)
    status = "ok"
    if random.random() < 0.02:
        status = "invalid"

    # -------- JSON payload --------
    payload = {
        "device_id": "tracker01",
        "timestamp": now,
        "servo_angle": round(servo_angle, 2),
        "temperature": round(temperature, 2),
        "humidity": round(humidity, 2),
        "lux": round(lux, 2),
        "ldr_left": ldr_left,
        "ldr_right": ldr_right,
        "voltage": round(voltage, 2),
        "current": round(current, 2),
        "power": round(power, 2),
        "fan_status": fan_status,
        "status": status
    }

    # -------- Publish --------
    client.publish(TOPIC, json.dumps(payload))

    print("Sent:", payload)

    time.sleep(5)  # every 5 seconds
import { SolarReading, PredictionData, ModelStatus, DataHealth, Alert, FanEvent } from "@/types/solar";

function randomBetween(min: number, max: number) {
  return Math.round((Math.random() * (max - min) + min) * 100) / 100;
}

function generateTimestamp(minutesAgo: number): string {
  return new Date(Date.now() - minutesAgo * 60000).toISOString();
}

export function generateCurrentReading(): SolarReading {
  const power = randomBetween(180, 320);
  return {
    timestamp: new Date().toISOString(),
    power,
    voltage: randomBetween(18, 22),
    current: Math.round((power / randomBetween(18, 22)) * 100) / 100,
    lux: randomBetween(30000, 85000),
    temperature: randomBetween(28, 48),
    humidity: randomBetween(30, 75),
    servo_angle: randomBetween(20, 160),
    fan_status: Math.random() > 0.4,
  };
}

export function generateHistoricalData(minutes: number): SolarReading[] {
  const points: SolarReading[] = [];
  const interval = minutes <= 15 ? 0.5 : minutes <= 60 ? 1 : minutes <= 360 ? 5 : 10;
  let basePower = 250;
  let baseLux = 60000;
  let baseTemp = 35;

  for (let i = minutes; i >= 0; i -= interval) {
    const timeOfDay = ((Date.now() - i * 60000) % 86400000) / 86400000;
    const solarFactor = Math.max(0, Math.sin(timeOfDay * Math.PI));
    basePower = 80 + solarFactor * 240 + randomBetween(-15, 15);
    baseLux = 5000 + solarFactor * 75000 + randomBetween(-2000, 2000);
    baseTemp = 25 + solarFactor * 20 + randomBetween(-2, 2);
    const humidity = 70 - solarFactor * 35 + randomBetween(-5, 5);
    const voltage = 17 + solarFactor * 5 + randomBetween(-0.5, 0.5);

    points.push({
      timestamp: generateTimestamp(i),
      power: Math.max(0, Math.round(basePower * 100) / 100),
      voltage: Math.max(0, Math.round(voltage * 100) / 100),
      current: Math.max(0, Math.round((basePower / Math.max(voltage, 1)) * 100) / 100),
      lux: Math.max(0, Math.round(baseLux)),
      temperature: Math.round(baseTemp * 10) / 10,
      humidity: Math.min(100, Math.max(0, Math.round(humidity * 10) / 10)),
      servo_angle: Math.round(20 + solarFactor * 140),
      fan_status: baseTemp > 40,
    });
  }
  return points;
}

export function generatePrediction(currentPower: number): PredictionData {
  return {
    predicted_power_15min: Math.round((currentPower + randomBetween(-30, 30)) * 100) / 100,
    confidence: randomBetween(0.82, 0.97),
    timestamp: new Date().toISOString(),
  };
}

export function generateModelStatus(): ModelStatus {
  return {
    status: "trained",
    last_trained_time: generateTimestamp(randomBetween(30, 300)),
    model_version: "v2.4.1",
    mae: randomBetween(3.5, 8.2),
    rmse: randomBetween(5.1, 12.8),
  };
}

export function generateDataHealth(): DataHealth {
  return {
    missing_rate: randomBetween(0, 3.5),
    invalid_readings: Math.floor(randomBetween(0, 12)),
    uptime: Math.random() > 0.05,
    last_check: new Date().toISOString(),
  };
}

export function generateAlerts(reading: SolarReading): Alert[] {
  const alerts: Alert[] = [];
  if (reading.lux < 35000) {
    alerts.push({ id: "a1", type: "low_lux", severity: "warning", message: `Low lux detected: ${reading.lux} lx`, timestamp: reading.timestamp, value: reading.lux });
  }
  if (reading.temperature > 42) {
    alerts.push({ id: "a2", type: "overheat", severity: reading.temperature > 45 ? "critical" : "warning", message: `Temperature high: ${reading.temperature}°C`, timestamp: reading.timestamp, value: reading.temperature });
  }
  if (reading.power < 120) {
    alerts.push({ id: "a3", type: "power_drop", severity: "warning", message: `Power output low: ${reading.power}W`, timestamp: reading.timestamp, value: reading.power });
  }
  if (Math.random() < 0.1) {
    alerts.push({ id: "a4", type: "sensor_invalid", severity: "critical", message: "Humidity sensor reporting invalid values", timestamp: reading.timestamp });
  }
  return alerts;
}

export function generateFanEvents(count: number): FanEvent[] {
  const events: FanEvent[] = [];
  let fanOn = false;
  for (let i = count; i >= 0; i--) {
    const temp = randomBetween(35, 48);
    if (!fanOn && temp > 40) {
      fanOn = true;
      events.push({ timestamp: generateTimestamp(i * 5), event_type: "fan_on", reason: `Temp exceeded 40°C threshold`, value: temp });
    } else if (fanOn && temp < 38) {
      fanOn = false;
      events.push({ timestamp: generateTimestamp(i * 5), event_type: "fan_off", reason: `Temp dropped below 38°C`, value: temp });
    }
  }
  return events;
}

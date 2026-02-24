export interface SolarReading {
  timestamp: string;
  power: number;
  voltage: number;
  current: number;
  lux: number;
  temperature: number;
  humidity: number;
  servo_angle: number;
  fan_status: boolean;
}

export interface PredictionData {
  predicted_power_15min: number;
  confidence: number;
  timestamp: string;
}

export interface ModelStatus {
  status: "trained" | "not_trained" | "training";
  last_trained_time: string;
  model_version: string;
  mae: number;
  rmse: number;
}

export interface DataHealth {
  missing_rate: number;
  invalid_readings: number;
  uptime: boolean;
  last_check: string;
}

export interface Alert {
  id: string;
  type: "low_lux" | "overheat" | "power_drop" | "sensor_invalid";
  severity: "warning" | "critical" | "info";
  message: string;
  timestamp: string;
  value?: number;
}

export interface FanEvent {
  timestamp: string;
  event_type: "fan_on" | "fan_off";
  reason: string;
  value: number;
}

export type TimeRange = "15m" | "1h" | "6h" | "24h";

export type StatusColor = "normal" | "warning" | "critical" | "offline";

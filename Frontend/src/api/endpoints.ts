/**
 * API Endpoints
 * Defines all backend API calls with type safety and validation
 */

import apiClient from './client';
import { SolarReading, PredictionData, ModelStatus } from '@/types/solar';

/**
 * Backend API response types (matches FastAPI schemas)
 */
interface BackendReadingResponse {
  device_id: string;
  timestamp: string;
  servo_angle: number;
  temperature: number;
  humidity: number;
  lux: number;
  voltage: number;
  current: number;
  power: number;
  fan_status: string;
  status?: string;
  ldr_left?: number;
  ldr_right?: number;
}

interface BackendPredictionResponse {
  predicted_power_15min: number;
  confidence: number;
  timestamp: string;
  model_version?: string;
  device_id?: string;
}

interface BackendHealthResponse {
  status: string;
  database: string;
  version: string;
}

/**
 * Normalize and validate reading data from backend
 */
function normalizeReading(data: any): SolarReading {
  return {
    timestamp: data.timestamp || new Date().toISOString(),
    power: typeof data.power === 'number' ? data.power : 0,
    voltage: typeof data.voltage === 'number' ? data.voltage : 0,
    current: typeof data.current === 'number' ? data.current : 0,
    lux: typeof data.lux === 'number' ? data.lux : 0,
    temperature: typeof data.temperature === 'number' ? data.temperature : 0,
    humidity: typeof data.humidity === 'number' ? data.humidity : 0,
    servo_angle: typeof data.servo_angle === 'number' ? data.servo_angle : 90,
    fan_status: typeof data.fan_status === 'string' ? data.fan_status : 'OFF',
    ldr_left: typeof data.ldr_left === 'number' ? data.ldr_left : undefined,
    ldr_right: typeof data.ldr_right === 'number' ? data.ldr_right : undefined,
    status: data.status || 'ok',
  };
}

/**
 * Normalize and validate prediction data from backend
 */
function normalizePrediction(data: any): PredictionData {
  return {
    predicted_power_15min: typeof data.predicted_power_15min === 'number' ? data.predicted_power_15min : 0,
    confidence: typeof data.confidence === 'number' ? data.confidence : 0.5,
    timestamp: data.timestamp || new Date().toISOString(),
    model_version: data.model_version,
  };
}

/**
 * Get latest sensor reading for a device
 */
export async function getLatestReading(deviceId: string): Promise<SolarReading> {
  try {
    const data = await apiClient.get<BackendReadingResponse>(
      `/api/readings/latest?device_id=${deviceId}`
    );
    return normalizeReading(data);
  } catch (error) {
    console.error('Failed to fetch latest reading:', error);
    throw error;
  }
}

/**
 * Get latest ML prediction for a device
 */
export async function getLatestPrediction(deviceId: string): Promise<PredictionData> {
  try {
    const data = await apiClient.get<BackendPredictionResponse>(
      `/api/prediction/latest?device_id=${deviceId}`
    );
    return normalizePrediction(data);
  } catch (error) {
    console.error('Failed to fetch latest prediction:', error);
    throw error;
  }
}

/**
 * Get historical readings for a device
 */
export async function getReadingHistory(
  deviceId: string,
  minutes: number
): Promise<SolarReading[]> {
  try {
    const data = await apiClient.get<BackendReadingResponse[]>(
      `/api/readings/history?device_id=${deviceId}&minutes=${minutes}`
    );
    
    // Normalize each reading
    return data.map(normalizeReading);
  } catch (error) {
    console.error('Failed to fetch reading history:', error);
    throw error;
  }
}

/**
 * Get model status for a device
 */
export async function getModelStatus(deviceId: string): Promise<ModelStatus | null> {
  try {
    const data = await apiClient.get<any>(`/api/ml/status?device_id=${deviceId}`);
    
    if (!data || !data.model_exists) {
      return null;
    }
    
    return {
      status: data.status || 'trained',
      last_trained_time: data.updated_at || new Date().toISOString(),
      model_version: data.version || '1.0',
      mae: data.metrics?.mae || 0,
      rmse: data.metrics?.rmse || 0,
    };
  } catch (error) {
    console.error('Failed to fetch model status:', error);
    return null;
  }
}

/**
 * Get device statistics
 */
export async function getDeviceStatistics(deviceId: string, minutes: number) {
  try {
    const data = await apiClient.get<any>(
      `/api/readings/statistics?device_id=${deviceId}&minutes=${minutes}`
    );
    return data;
  } catch (error) {
    console.error('Failed to fetch device statistics:', error);
    throw error;
  }
}

/**
 * Check backend health
 */
export async function checkBackendHealth(): Promise<boolean> {
  return apiClient.healthCheck();
}

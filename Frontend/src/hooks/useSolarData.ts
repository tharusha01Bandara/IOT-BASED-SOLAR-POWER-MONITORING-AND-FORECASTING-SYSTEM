import { useState, useEffect, useCallback, useRef } from "react";
import { SolarReading, PredictionData, ModelStatus, DataHealth, Alert, FanEvent, TimeRange } from "@/types/solar";
import {
  generateModelStatus,
  generateDataHealth,
  generateAlerts,
  generateFanEvents,
  generatePrediction
} from "@/data/mock";
import { config } from "@/lib/config";

const TIME_RANGE_MINUTES: Record<TimeRange, number> = {
  "15m": 15,
  "1h": 60,
  "6h": 360,
  "24h": 1440,
};

export function useSolarData() {
  const [currentReading, setCurrentReading] = useState<SolarReading | null>(null);
  const [prediction, setPrediction] = useState<PredictionData | null>(null);
  const [modelStatus, setModelStatus] = useState<ModelStatus>(generateModelStatus());
  const [dataHealth, setDataHealth] = useState<DataHealth>(generateDataHealth());
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [fanEvents, setFanEvents] = useState<FanEvent[]>(generateFanEvents(30));
  const [timeRange, setTimeRange] = useState<TimeRange>("1h");
  const [historicalData, setHistoricalData] = useState<SolarReading[]>([]);
  const [isLive, setIsLive] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [isLoading, setIsLoading] = useState(true);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const fetchLatest = async () => {
    try {
      const response = await fetch(`${config.apiUrl}/api/readings/latest?device_id=tracker01`);
      if (response.ok) {
        const data = await response.json();
        setCurrentReading(data);
        if (data.power) {
          setPrediction(generatePrediction(data.power));
        }
        setLastUpdated(new Date());
      }
    } catch (error) {
      console.error("Failed to fetch latest reading:", error);
    }
  };

  const fetchHistory = async () => {
    try {
      setIsLoading(true);
      const response = await fetch(`${config.apiUrl}/api/readings/history?device_id=tracker01&limit=50`);
      if (response.ok) {
        const data = await response.json();
        setHistoricalData(data);
      }
    } catch (error) {
      console.error("Failed to fetch history:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const refresh = useCallback(() => {
    fetchLatest();
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [timeRange]);

  useEffect(() => {
    if (isLive) {
      intervalRef.current = setInterval(refresh, 3000);
    }
    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [isLive, refresh]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  return {
    currentReading,
    prediction,
    modelStatus,
    dataHealth,
    alerts,
    fanEvents,
    historicalData,
    timeRange,
    setTimeRange,
    isLive,
    setIsLive,
    lastUpdated,
    isLoading,
    refresh,
  };
}

import { useState, useEffect, useCallback, useRef } from "react";
import { SolarReading, PredictionData, ModelStatus, DataHealth, Alert, FanEvent, TimeRange } from "@/types/solar";
import {
  generateCurrentReading,
  generateHistoricalData,
  generatePrediction,
  generateModelStatus,
  generateDataHealth,
  generateAlerts,
  generateFanEvents,
} from "@/data/mock";

const TIME_RANGE_MINUTES: Record<TimeRange, number> = {
  "15m": 15,
  "1h": 60,
  "6h": 360,
  "24h": 1440,
};

export function useSolarData() {
  const [currentReading, setCurrentReading] = useState<SolarReading>(generateCurrentReading());
  const [prediction, setPrediction] = useState<PredictionData>(generatePrediction(250));
  const [modelStatus, setModelStatus] = useState<ModelStatus>(generateModelStatus());
  const [dataHealth, setDataHealth] = useState<DataHealth>(generateDataHealth());
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [fanEvents, setFanEvents] = useState<FanEvent[]>(generateFanEvents(30));
  const [timeRange, setTimeRange] = useState<TimeRange>("1h");
  const [historicalData, setHistoricalData] = useState<SolarReading[]>(() => generateHistoricalData(60));
  const [isLive, setIsLive] = useState(true);
  const [lastUpdated, setLastUpdated] = useState(new Date());
  const [isLoading, setIsLoading] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval> | null>(null);

  const refresh = useCallback(() => {
    const reading = generateCurrentReading();
    setCurrentReading(reading);
    setPrediction(generatePrediction(reading.power));
    setAlerts(generateAlerts(reading));
    setDataHealth(generateDataHealth());
    setLastUpdated(new Date());
  }, []);

  useEffect(() => {
    setIsLoading(true);
    const timer = setTimeout(() => {
      setHistoricalData(generateHistoricalData(TIME_RANGE_MINUTES[timeRange]));
      setIsLoading(false);
    }, 300);
    return () => clearTimeout(timer);
  }, [timeRange]);

  useEffect(() => {
    if (isLive) {
      intervalRef.current = setInterval(refresh, 7000);
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

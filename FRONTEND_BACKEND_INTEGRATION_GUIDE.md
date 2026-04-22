/**
 * FRONTEND-BACKEND ML PREDICTION INTEGRATION GUIDE
 * 
 * This file explains the exact changes needed to properly connect the Frontend
 * with the Backend ML prediction endpoint.
 * 
 * Problem: Frontend currently uses mock predictions (hardcoded random data)
 * Solution: Integrate real predictions from /api/ml/predict endpoint
 */

// ============================================================================
// PART 1: UPDATE API ENDPOINTS FILE
// ============================================================================

/**
 * File: Frontend/src/api/endpoints.ts
 * 
 * CURRENT ISSUE:
 * The Frontend tries to call `/api/prediction/latest` (GET) which doesn't exist
 * 
 * SOLUTION:
 * Create a new function to call `/api/ml/predict` (POST) properly
 */

// ADD THIS NEW FUNCTION to Frontend/src/api/endpoints.ts:

export async function makePrediction(
  deviceId: string,
  reading: SolarReading
): Promise<PredictionData> {
  try {
    const payload = {
      device_id: deviceId,
      timestamp: reading.timestamp,
      servo_angle: reading.servo_angle,
      temperature: reading.temperature,
      humidity: reading.humidity,
      lux: reading.lux,
      voltage: reading.voltage,
      current: reading.current,
      power: reading.power,
      store_prediction: false  // Change to true if you want to save predictions
    };

    const data = await apiClient.post<any>(
      `/api/ml/predict`,
      payload
    );

    // Transform backend response to PredictionData
    return normalizePrediction({
      predicted_power_15min: data.predicted_power_15min,
      confidence: data.confidence,
      timestamp: data.predicted_at,
      model_version: data.model_version
    });
  } catch (error) {
    console.error('Failed to make prediction:', error);
    throw error;
  }
}

// ============================================================================
// PART 2: UPDATE API CLIENT IF NEEDED
// ============================================================================

/**
 * File: Frontend/src/api/client.ts
 * 
 * Make sure apiClient has a .post() method, or update to use:
 */

// Option 1: Using fetch (if apiClient doesn't support POST)
export async function makePrediction(
  deviceId: string,
  reading: SolarReading
): Promise<PredictionData> {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/ml/predict', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        device_id: deviceId,
        timestamp: reading.timestamp,
        servo_angle: reading.servo_angle,
        temperature: reading.temperature,
        humidity: reading.humidity,
        lux: reading.lux,
        voltage: reading.voltage,
        current: reading.current,
        power: reading.power,
        store_prediction: false
      })
    });

    if (!response.ok) {
      throw new Error(`Prediction failed: ${response.statusText}`);
    }

    const data = await response.json();
    return normalizePrediction(data);
  } catch (error) {
    console.error('Prediction error:', error);
    throw error;
  }
}

// ============================================================================
// PART 3: UPDATE ANALYTICS PAGE
// ============================================================================

/**
 * File: Frontend/src/pages/Analytics.tsx
 * 
 * CURRENT CODE (problematic):
 * 
 * const chartData = useMemo(() =>
 *   historicalData.map((d) => ({
 *     time: formatTime(d.timestamp),
 *     power: d.power,
 *     lux: d.lux,
 *     temperature: d.temperature,
 *     predicted: Math.max(0, d.power + (Math.random() - 0.5) * 30),  // MOCK DATA!
 *   })),
 *   [historicalData]
 * );
 * 
 * SOLUTION: Replace with real predictions
 */

// NEW CODE for Analytics.tsx:
import { useState, useEffect, useMemo } from "react";
import { makePrediction } from "@/api/endpoints";

export default function Analytics() {
  const { historicalData, timeRange, currentReading } = useSolarContext();
  const [predictions, setPredictions] = useState<Map<string, number>>(new Map());
  const [confidenceScores, setConfidenceScores] = useState<Map<string, number>>(new Map());
  const [isLoadingPrediction, setIsLoadingPrediction] = useState(false);

  // Fetch predictions for each reading
  useEffect(() => {
    const fetchPredictions = async () => {
      if (!historicalData || historicalData.length === 0) return;

      setIsLoadingPrediction(true);
      const predictionMap = new Map<string, number>();
      const confidenceMap = new Map<string, number>();

      try {
        // Only fetch prediction for current reading
        // (fetching for all historical would be expensive)
        if (currentReading) {
          const prediction = await makePrediction('tracker01', currentReading);
          const timestamp = new Date(currentReading.timestamp).toISOString();
          predictionMap.set(timestamp, prediction.predicted_power_15min);
          confidenceMap.set(timestamp, prediction.confidence);
        }

        setPredictions(predictionMap);
        setConfidenceScores(confidenceMap);
      } catch (error) {
        console.error('Failed to fetch predictions:', error);
      } finally {
        setIsLoadingPrediction(false);
      }
    };

    fetchPredictions();
  }, [historicalData, currentReading]);

  const chartData = useMemo(() =>
    historicalData.map((d) => {
      const timestamp = new Date(d.timestamp).toISOString();
      const predictedValue = predictions.get(timestamp);
      
      return {
        time: formatTime(d.timestamp),
        power: d.power,
        lux: d.lux,
        temperature: d.temperature,
        predicted: predictedValue !== undefined ? predictedValue : null,
        confidence: confidenceScores.get(timestamp)
      };
    }),
    [historicalData, predictions, confidenceScores]
  );

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      {/* Loading indicator while fetching predictions */}
      {isLoadingPrediction && (
        <div className="bg-yellow-500/10 border border-yellow-500/20 rounded-lg p-3">
          <p className="text-sm text-yellow-500">⏳ Fetching ML predictions...</p>
        </div>
      )}

      {/* Existing chart code */}
      <div>
        <h1 className="text-xl md:text-2xl font-bold">Analytics</h1>
        <p className="text-sm text-muted-foreground mt-0.5">
          Historical trends and correlations ({timeRange})
        </p>
      </div>

      {/* Power over Time Chart */}
      {/* ... existing chart code ... */}

      {/* Predicted vs Actual Chart - UPDATED */}
      <div className="glass-card rounded-xl p-4 animate-fade-in">
        <h3 className="text-sm font-semibold mb-4">Predicted vs Actual Power</h3>
        <div className="h-64 md:h-80">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" className="opacity-20" />
              <XAxis dataKey="time" tick={{ fontSize: 10 }} />
              <YAxis tick={{ fontSize: 10 }} />
              <Tooltip 
                contentStyle={{ background: "hsl(222, 25%, 12%)", border: "1px solid hsl(222, 20%, 18%)", borderRadius: "8px", fontSize: 12 }}
                formatter={(value) => {
                  if (typeof value === 'number') {
                    return [value.toFixed(2) + 'W', ''];
                  }
                  return [value, ''];
                }}
              />
              <Legend />
              <Line 
                type="monotone" 
                dataKey="power" 
                stroke="hsl(174, 72%, 45%)" 
                strokeWidth={2} 
                dot={false} 
                name="Actual (W)" 
              />
              <Line 
                type="monotone" 
                dataKey="predicted" 
                stroke="hsl(265, 60%, 60%)" 
                strokeWidth={2} 
                dot={false} 
                strokeDasharray="5 5" 
                name="Predicted (W)" 
                isAnimationActive={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Confidence Score Display */}
        {confidenceScores.size > 0 && (
          <div className="mt-4 pt-4 border-t border-muted">
            <div className="flex items-center justify-between">
              <span className="text-sm text-muted-foreground">Model Confidence</span>
              <div className="flex items-center gap-2">
                {Array.from(confidenceScores.values()).map((conf, idx) => (
                  <div
                    key={idx}
                    className={`w-3 h-3 rounded-full ${
                      conf > 0.95 ? 'bg-green-500' :
                      conf > 0.80 ? 'bg-yellow-500' :
                      'bg-red-500'
                    }`}
                    title={`${(conf * 100).toFixed(1)}%`}
                  />
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Rest of charts... */}
    </div>
  );
}

// ============================================================================
// PART 4: ADD PREDICTION DISPLAY COMPONENT
// ============================================================================

/**
 * Create: Frontend/src/components/PredictionCard.tsx
 * 
 * A reusable component to display prediction results with confidence
 */

import { TrendingUp } from "lucide-react";

interface PredictionCardProps {
  currentPower: number;
  predictedPower: number;
  confidence: number;
  modelVersion: string;
}

export function PredictionCard({
  currentPower,
  predictedPower,
  confidence,
  modelVersion
}: PredictionCardProps) {
  const trend = predictedPower > currentPower ? "up" : predictedPower < currentPower ? "down" : "stable";
  const powerDelta = predictedPower - currentPower;
  const confidencePercent = (confidence * 100).toFixed(1);
  const confidenceColor = 
    confidence > 0.95 ? "text-green-500" :
    confidence > 0.80 ? "text-yellow-500" :
    "text-red-500";

  return (
    <div className="glass-card rounded-xl p-5 animate-fade-in">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-semibold flex items-center gap-2">
          <TrendingUp className="w-5 h-5 text-primary" />
          Power Forecast (15 min)
        </h3>
        <span className={`text-xs font-mono ${confidenceColor}`}>
          {confidencePercent}% confidence
        </span>
      </div>

      <div className="grid grid-cols-2 gap-4">
        <div>
          <p className="text-xs text-muted-foreground mb-1">Current</p>
          <p className="text-2xl font-bold">{currentPower.toFixed(2)}W</p>
        </div>
        <div>
          <p className="text-xs text-muted-foreground mb-1">Predicted</p>
          <p className="text-2xl font-bold">{predictedPower.toFixed(2)}W</p>
        </div>
      </div>

      <div className="mt-4 pt-4 border-t border-muted">
        <div className="flex items-center justify-between">
          <span className="text-sm text-muted-foreground">
            {trend === "up" && "📈 Power increasing"}
            {trend === "down" && "📉 Power decreasing"}
            {trend === "stable" && "➡️ Power stable"}
          </span>
          <span className={`text-sm font-mono ${powerDelta >= 0 ? "text-green-500" : "text-red-500"}`}>
            {powerDelta >= 0 ? "+" : ""}{powerDelta.toFixed(2)}W
          </span>
        </div>
      </div>

      <div className="mt-3 text-xs text-muted-foreground">
        Model v{modelVersion}
      </div>
    </div>
  );
}

// ============================================================================
// PART 5: USE IN DASHBOARD
// ============================================================================

/**
 * File: Frontend/src/pages/Overview.tsx or Dashboard
 * 
 * Add prediction card to main dashboard
 */

import { PredictionCard } from "@/components/PredictionCard";

export default function Overview() {
  const { currentReading, latestPrediction, modelStatus } = useSolarContext();

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="grid md:grid-cols-2 gap-4">
        {/* Existing KPI Cards */}
        
        {/* New Prediction Card */}
        {latestPrediction && (
          <PredictionCard
            currentPower={currentReading?.power || 0}
            predictedPower={latestPrediction.predicted_power_15min}
            confidence={latestPrediction.confidence}
            modelVersion={latestPrediction.model_version || "unknown"}
          />
        )}
      </div>
    </div>
  );
}

// ============================================================================
// PART 6: ERROR HANDLING
// ============================================================================

/**
 * Handle common prediction errors gracefully
 */

async function safeMakePrediction(
  deviceId: string,
  reading: SolarReading
): Promise<PredictionData | null> {
  try {
    const prediction = await makePrediction(deviceId, reading);
    return prediction;
  } catch (error: any) {
    if (error.response?.status === 404) {
      console.warn("Model not found for device:", deviceId);
      console.warn("Hint: Train a model first using /api/ml/train");
      return null;
    }
    
    if (error.response?.status === 400) {
      console.error("Invalid request data:", error.response.data);
      return null;
    }

    console.error("Prediction failed:", error);
    return null;
  }
}

// ============================================================================
// PART 7: PERFORMANCE CONSIDERATIONS
// ============================================================================

/**
 * OPTIMIZATION TIPS:
 * 
 * 1. Caching
 *    - Cache predictions for 1-2 minutes to avoid repeated requests
 *    - Use a Map with timestamp as key
 * 
 * 2. Debouncing
 *    - Don't make prediction on every reading update
 *    - Use debounce to limit API calls to 1 per 30-60 seconds
 * 
 * 3. Selective Updates
 *    - Only fetch predictions for "significant" power changes
 *    - Skip predictions for zero power (nighttime)
 * 
 * 4. Fallback Display
 *    - Show last known prediction if current request fails
 *    - Display "prediction unavailable" instead of error
 * 
 * Example debouncing:
 */

import { useCallback, useRef } from "react";

export function useDebounce<T>(
  callback: (arg: T) => void,
  delay: number
) {
  const timeoutRef = useRef<NodeJS.Timeout>();

  return useCallback((arg: T) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }
    timeoutRef.current = setTimeout(() => callback(arg), delay);
  }, [callback, delay]);
}

// Usage:
const debouncedFetchPrediction = useDebounce(async (reading: SolarReading) => {
  const prediction = await makePrediction('tracker01', reading);
  setCurrentPrediction(prediction);
}, 30000); // Only fetch every 30 seconds

// ============================================================================
// PART 8: TESTING THE INTEGRATION
// ============================================================================

/**
 * TEST STEPS:
 * 
 * 1. Verify Backend is Running
 *    - Visit: http://127.0.0.1:8000/docs
 *    - Try prediction endpoint in Swagger UI
 * 
 * 2. Test API Connection from Frontend
 *    - Open browser console (F12)
 *    - Run test command:
 * 
 *    fetch('http://127.0.0.1:8000/api/ml/predict', {
 *      method: 'POST',
 *      headers: { 'Content-Type': 'application/json' },
 *      body: JSON.stringify({
 *        device_id: 'tracker01',
 *        timestamp: new Date().toISOString(),
 *        servo_angle: 45,
 *        temperature: 28,
 *        humidity: 60,
 *        lux: 75000,
 *        voltage: 21,
 *        current: 3.5,
 *        power: 73.5,
 *        store_prediction: false
 *      })
 *    }).then(r => r.json()).then(console.log)
 * 
 * 3. Check Response
 *    - Should show:
 *    {
 *      "success": true,
 *      "device_id": "tracker01",
 *      "current_power": 73.5,
 *      "predicted_power_15min": 0.XXX,
 *      "confidence": 0.99X,
 *      "model_version": "XXXXXXXXX",
 *      "predicted_at": "2026-04-22T..."
 *    }
 * 
 * 4. Troubleshooting
 *    - CORS Error: Backend needs CORS middleware
 *    - 404 Error: Endpoint URL is wrong
 *    - 500 Error: Backend error, check logs
 *    - Timeout: Backend is slow, increase timeout
 */

console.log("Frontend-Backend Integration Guide Loaded");

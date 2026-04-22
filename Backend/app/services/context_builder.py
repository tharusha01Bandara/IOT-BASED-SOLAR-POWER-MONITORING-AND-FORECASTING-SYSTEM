from typing import Dict, Any, List
from datetime import datetime, timedelta
from pymongo.collection import Collection
from app.schemas.chat import ChatContextSummary

class ContextBuilder:
    def __init__(self, readings_collection: Collection, predictions_collection: Collection):
        self.readings = readings_collection
        self.predictions = predictions_collection

    def _get_active_alerts(self, reading: Dict[str, Any]) -> List[str]:
        alerts = []
        if not reading:
            return alerts
            
        temp = reading.get("temperature", 0.0)
        if temp is None: temp = 0.0
            
        lux = reading.get("lux", 0.0)
        if lux is None: lux = 0.0
            
        status = reading.get("status", "ok")
        fan = reading.get("fan_status", "OFF")
        
        if float(temp) > 40:
            alerts.append("overheating alert")
        if float(lux) < 1000 and "day" in str(status).lower(): # Simple logic
            alerts.append("low light alert")
        elif float(lux) < 100:
            alerts.append("low light alert")
            
        if status != "ok":
            alerts.append(f"system issue: {status}")
        if fan == "ON":
            alerts.append("cooling active")
            
        return alerts

    def _get_trend_summary(self, history: List[Dict[str, Any]]) -> str:
        if len(history) < 2:
            return "Not enough data for trend."
            
        first = history[0]
        last = history[-1]
        
        def trend_str(val1, val2):
            v1, v2 = float(val1 or 0), float(val2 or 0)
            if v1 == 0: return "stable"
            if v2 > v1 * 1.05: return "rising"
            if v2 < v1 * 0.95: return "falling"
            return "stable"
            
        p_trend = trend_str(first.get("power", 0), last.get("power", 0))
        l_trend = trend_str(first.get("lux", 0), last.get("lux", 0))
        t_trend = trend_str(first.get("temperature", 0), last.get("temperature", 0))
        
        return f"Power is {p_trend}, lux is {l_trend}, temperature is {t_trend}."

    async def build_context(self) -> ChatContextSummary:
        latest_reading = self.readings.find_one({}, sort=[("timestamp", -1)]) or {}
        
        history_cursor = self.readings.find({}).sort("timestamp", -1).limit(60)
        history_list = list(history_cursor)
        history_list.reverse()
        
        latest_pred = self.predictions.find_one({}, sort=[("timestamp", -1)]) or {}
        
        alerts = self._get_active_alerts(latest_reading)
        trend = self._get_trend_summary(history_list)
        
        pred_val = latest_pred.get("predicted_power_15min", latest_pred.get("predicted_power"))
        
        return ChatContextSummary(
            latest_power=latest_reading.get("power"),
            latest_lux=latest_reading.get("lux"),
            latest_temperature=latest_reading.get("temperature"),
            latest_humidity=latest_reading.get("humidity"),
            latest_servo_angle=latest_reading.get("servo_angle"),
            latest_fan_status=latest_reading.get("fan_status"),
            latest_status=latest_reading.get("status"),
            latest_prediction=pred_val,
            prediction_confidence=latest_pred.get("confidence"),
            active_alerts=alerts,
            recent_trend_summary=trend,
        )

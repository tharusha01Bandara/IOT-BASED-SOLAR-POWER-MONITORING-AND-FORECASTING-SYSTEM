"""
Grounded chat service for conversational visual analytics.

Design principles:
- Always fetch real backend data first (grounding)
- Use LLM only for synthesis and explanation
- Return machine-verifiable evidence with every answer
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta
from statistics import mean
from typing import Any, Dict, List, Optional

import requests
from pymongo.collection import Collection

from app.core.config import Settings
from app.core.logging import get_logger
from app.services.readings_service import ReadingsService

logger = get_logger(__name__)


class ChatService:
    """Service class for grounded conversational analytics."""

    TIME_RANGE_TO_MINUTES = {
        "15m": 15,
        "1h": 60,
        "6h": 360,
        "24h": 1440,
        "7d": 10080,
    }

    SOURCE_ENDPOINTS = [
        "/api/readings/latest",
        "/api/readings/history",
        "/api/readings/statistics",
        "/api/prediction/latest",
        "/api/prediction/history",
        "/api/ml/status",
    ]

    PERSONA_QUESTIONS = {
        "operator": [
            "Is power output trending down in the last hour?",
            "Which metric is most abnormal right now?",
            "What immediate action should I take?",
        ],
        "energy_manager": [
            "How does current output compare to the previous hour?",
            "What is the expected power in the next 15 minutes?",
            "What factors most influence power right now?",
        ],
        "maintenance_technician": [
            "Explain the latest anomaly and likely root cause.",
            "Is fan behavior consistent with temperature thresholds?",
            "Are there signs of sensor drift or invalid readings?",
        ],
        "academic_evaluator": [
            "What is the current model confidence and status?",
            "How accurate are recent predictions versus actual values?",
            "Which variables appear most correlated with power?",
        ],
    }

    def __init__(
        self,
        settings: Settings,
        readings_collection: Collection,
        predictions_collection: Collection,
    ):
        self.settings = settings
        self.readings_collection = readings_collection
        self.predictions_collection = predictions_collection
        self.readings_service = ReadingsService(readings_collection)

    async def answer_query(
        self,
        device_id: str,
        query: str,
        time_range: str,
        visual_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Answer chat query using grounded data plus LLM synthesis."""
        minutes = self.TIME_RANGE_TO_MINUTES.get(time_range, 60)
        grounded = await self._build_grounded_context(device_id, minutes)
        intent = self._classify_intent(query)

        evidence = {
            "stats": grounded["stats"],
            "points": grounded["points"],
            "source_endpoints": self.SOURCE_ENDPOINTS,
        }

        prompt = self._build_prompt(query, intent, grounded, visual_context or {})
        answer = self._call_llm(prompt)

        return {
            "answer": answer,
            "intent": intent,
            "confidence": grounded["confidence"],
            "evidence": evidence,
            "suggested_actions": grounded["suggested_actions"],
            "follow_up_questions": grounded["follow_up_questions"],
        }

    async def explain_anomaly(
        self,
        device_id: str,
        timestamp: datetime,
        window_minutes: int,
    ) -> Dict[str, Any]:
        """Return deterministic anomaly explanation centered around timestamp."""
        start = timestamp - timedelta(minutes=window_minutes)
        end = timestamp + timedelta(minutes=window_minutes)

        cursor = self.readings_collection.find(
            {
                "device_id": device_id,
                "timestamp": {"$gte": start, "$lte": end},
            },
            sort=[("timestamp", 1)],
        )
        readings = list(cursor)

        if len(readings) < 5:
            return {
                "anomaly_summary": "Insufficient readings around the selected timestamp.",
                "likely_causes": ["Collect more data around the target period."],
                "supporting_metrics": {"reading_count": len(readings)},
                "operator_recommendation": "Retry after additional data ingestion.",
            }

        powers = [float(r.get("power", 0.0)) for r in readings]
        temperatures = [float(r.get("temperature", 0.0)) for r in readings]
        luxes = [float(r.get("lux", 0.0)) for r in readings]

        power_drop = round((max(powers) - min(powers)), 3)
        temp_peak = round(max(temperatures), 3)
        lux_variability = round(max(luxes) - min(luxes), 3)

        causes = []
        if power_drop > 20:
            causes.append("Significant short-window power volatility was detected.")
        if temp_peak >= 40:
            causes.append("High panel temperature may have reduced efficiency.")
        if lux_variability > 10000:
            causes.append("Rapid irradiance changes likely contributed to output instability.")
        if not causes:
            causes.append("No severe physical anomaly; variation appears within normal operational behavior.")

        recommendation = (
            "Check panel cleanliness and thermal management, then verify sensor calibration "
            "if volatility continues for multiple windows."
        )

        return {
            "anomaly_summary": "Anomaly explanation generated from actual sensor window around selected timestamp.",
            "likely_causes": causes,
            "supporting_metrics": {
                "reading_count": len(readings),
                "power_drop_w": power_drop,
                "temperature_peak_c": temp_peak,
                "lux_variability": lux_variability,
                "window_start": start.isoformat(),
                "window_end": end.isoformat(),
            },
            "operator_recommendation": recommendation,
        }

    def suggested_questions(self, persona: str) -> Dict[str, Any]:
        """Return curated suggested prompts by persona."""
        key = (persona or "").strip().lower()
        if key not in self.PERSONA_QUESTIONS:
            key = "operator"

        return {
            "persona": key,
            "questions": self.PERSONA_QUESTIONS[key],
        }

    async def _build_grounded_context(self, device_id: str, minutes: int) -> Dict[str, Any]:
        latest = await self.readings_service.get_latest_reading(device_id)
        history = await self.readings_service.get_reading_history(device_id=device_id, minutes=minutes)
        stats = await self.readings_service.get_device_statistics(device_id=device_id, minutes=minutes)

        pred_latest_doc = self.predictions_collection.find_one(
            {"device_id": device_id},
            sort=[("timestamp", -1)],
        )

        prediction_value = None
        prediction_confidence = None
        prediction_ts = None
        if pred_latest_doc:
            prediction_value = pred_latest_doc.get("predicted_power_15min", pred_latest_doc.get("predicted_power"))
            prediction_confidence = pred_latest_doc.get("confidence")
            prediction_ts = pred_latest_doc.get("timestamp")

        points = [
            {
                "timestamp": r.get("timestamp").isoformat() if r.get("timestamp") else None,
                "power": r.get("power"),
                "lux": r.get("lux"),
                "temperature": r.get("temperature"),
                "humidity": r.get("humidity"),
            }
            for r in history[-50:]
        ]

        trend = self._compute_trend(history)
        anomalies = self._quick_anomalies(history)

        grounded_stats = {
            "window_minutes": minutes,
            "reading_count": len(history),
            "current_power": latest.get("power") if latest else None,
            "current_temperature": latest.get("temperature") if latest else None,
            "current_lux": latest.get("lux") if latest else None,
            "average_power": stats.get("average_power"),
            "max_power": stats.get("max_power"),
            "min_power": stats.get("min_power"),
            "average_temperature": stats.get("average_temperature"),
            "average_lux": stats.get("average_lux"),
            "predicted_power_15min": prediction_value,
            "prediction_confidence": prediction_confidence,
            "prediction_timestamp": prediction_ts.isoformat() if hasattr(prediction_ts, "isoformat") else prediction_ts,
            "power_trend_percent": trend,
            "anomaly_flags": anomalies,
        }

        follow_ups = [
            "Do you want a comparison with the previous time window?",
            "Should I break down likely causes for power changes?",
            "Do you want an action recommendation for operators?",
        ]

        actions = self._action_suggestions(grounded_stats)

        return {
            "stats": grounded_stats,
            "points": points,
            "confidence": self._estimate_confidence(len(history), prediction_confidence),
            "suggested_actions": actions,
            "follow_up_questions": follow_ups,
        }

    @staticmethod
    def _compute_trend(history: List[Dict[str, Any]]) -> float:
        if len(history) < 2:
            return 0.0

        first = float(history[0].get("power", 0.0))
        last = float(history[-1].get("power", 0.0))
        if abs(first) < 1e-9:
            return 0.0

        return round(((last - first) / first) * 100.0, 3)

    @staticmethod
    def _quick_anomalies(history: List[Dict[str, Any]]) -> List[str]:
        if len(history) < 5:
            return []

        powers = [float(r.get("power", 0.0)) for r in history]
        temps = [float(r.get("temperature", 0.0)) for r in history]
        luxes = [float(r.get("lux", 0.0)) for r in history]

        flags: List[str] = []
        if max(temps) >= 42.0:
            flags.append("overheat_risk")
        if mean(powers) > 0 and min(powers) < mean(powers) * 0.4:
            flags.append("power_drop")
        if max(luxes) > 0 and min(luxes) < max(luxes) * 0.25:
            flags.append("low_irradiance_period")

        return flags

    @staticmethod
    def _classify_intent(query: str) -> str:
        q = query.lower()
        if any(k in q for k in ["trend", "increasing", "decreasing", "over time"]):
            return "trend"
        if any(k in q for k in ["compare", "versus", "vs", "difference"]):
            return "comparison"
        if any(k in q for k in ["anomaly", "abnormal", "drop", "spike", "why"]):
            return "anomaly"
        if any(k in q for k in ["factor", "influence", "driver", "cause"]):
            return "factor"
        if any(k in q for k in ["recommend", "action", "should", "decision"]):
            return "recommendation"
        return "general"

    @staticmethod
    def _estimate_confidence(reading_count: int, pred_conf: Optional[float]) -> float:
        base = 0.45
        count_bonus = min(0.4, reading_count / 1000.0)
        pred_bonus = (pred_conf or 0.0) * 0.15
        return round(min(0.99, base + count_bonus + pred_bonus), 3)

    @staticmethod
    def _action_suggestions(stats: Dict[str, Any]) -> List[str]:
        actions: List[str] = []

        temp = stats.get("current_temperature")
        if isinstance(temp, (int, float)) and temp >= 40:
            actions.append("Enable or verify active cooling to reduce thermal losses.")

        trend = stats.get("power_trend_percent")
        if isinstance(trend, (int, float)) and trend < -15:
            actions.append("Inspect for shading, cloud cover, or panel misalignment due to downward power trend.")

        pred = stats.get("predicted_power_15min")
        cur = stats.get("current_power")
        if isinstance(pred, (int, float)) and isinstance(cur, (int, float)) and pred < cur * 0.8:
            actions.append("Prepare short-term load planning for expected output reduction in next 15 minutes.")

        if not actions:
            actions.append("Maintain current operation; no urgent intervention indicated in this window.")

        return actions

    def _build_prompt(
        self,
        query: str,
        intent: str,
        grounded: Dict[str, Any],
        visual_context: Dict[str, Any],
    ) -> str:
        system_instruction = (
            "You are an analytics copilot for a solar monitoring system. "
            "Only use grounded data provided in JSON. Do not invent values. "
            "If data is insufficient, state that clearly and suggest next checks. "
            "Focus on concise decision-support guidance."
        )

        payload = {
            "intent": intent,
            "user_query": query,
            "grounded_stats": grounded.get("stats", {}),
            "recent_points": grounded.get("points", [])[:20],
            "visual_context": visual_context,
        }

        return (
            f"SYSTEM:\n{system_instruction}\n\n"
            f"DATA:\n{json.dumps(payload, default=str)}\n\n"
            "TASK:\n"
            "1) Answer the user question with concrete values from data.\n"
            "2) Mention uncertainty when needed.\n"
            "3) End with one practical operator recommendation."
        )

    def _call_llm(self, prompt: str) -> str:
        """
        Call OpenAI-compatible Chat Completions endpoint.

        This keeps dependencies minimal by using requests against a standard API.
        """
        if not self.settings.llm_enabled:
            raise ValueError("Chat LLM integration is disabled. Set LLM_ENABLED=True.")

        if not self.settings.llm_api_key:
            raise ValueError("Missing LLM_API_KEY in environment.")

        api_url = self.settings.llm_api_url.rstrip("/")
        api_path = (self.settings.llm_api_path or "").strip()
        if api_url.endswith("/chat/completions"):
            url = api_url
        else:
            if not api_path.startswith("/"):
                api_path = f"/{api_path}" if api_path else "/chat/completions"
            url = api_url + api_path
        headers = {
            "Authorization": f"Bearer {self.settings.llm_api_key}",
            "Content-Type": "application/json",
        }
        body = {
            "model": self.settings.llm_model,
            "temperature": self.settings.llm_temperature,
            "max_tokens": self.settings.llm_max_tokens,
            "messages": [
                {"role": "user", "content": prompt},
            ],
        }

        try:
            response = requests.post(
                url,
                headers=headers,
                json=body,
                timeout=self.settings.llm_timeout_seconds,
            )
            response.raise_for_status()
            data = response.json()
            choices = data.get("choices", [])
            if not choices:
                raise ValueError("LLM returned no choices")

            content = choices[0].get("message", {}).get("content", "")
            if not content.strip():
                raise ValueError("LLM returned empty content")

            return content.strip()
        except Exception as exc:
            logger.error(f"LLM request failed: {exc}", exc_info=True)
            raise ValueError(f"Failed to generate LLM response: {exc}") from exc

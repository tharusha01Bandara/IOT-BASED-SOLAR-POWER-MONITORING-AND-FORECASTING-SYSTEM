import os
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from app.core.config import Settings
from app.schemas.chat import ChatResponse, ChatContextSummary

class LLMService:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.api_key = self.settings.gemini_api_key
        self.model_name = self.settings.gemini_model or "gemini-2.5-flash"
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(self.model_name)
        else:
            self.model = None

    def is_available(self) -> bool:
        return self.model is not None

    async def generate_response(self, question: str, context: ChatContextSummary) -> ChatResponse:
        if not self.is_available():
            raise Exception("LLM provider missing API Key")
        
        system_prompt = (
            "You are a solar analytics assistant for a Smart Single-Axis Solar Tracker dashboard.\n"
            "You must answer user questions based ONLY on the provided dashboard data context below.\n"
            "Explain things clearly for non-technical users.\n"
            "Mention dashboard components (charts, alerts panel) when helpful.\n"
            "Keep your answers brief but meaningful.\n"
            "Do NOT make up values or external facts if they are not in the context.\n"
        )
        
        alerts_str = ", ".join(context.active_alerts) if context.active_alerts else "None"
        
        context_str = (
            f"--- LIVE DATA CONTEXT ---\n"
            f"Power: {context.latest_power}W\n"
            f"Lux: {context.latest_lux}\n"
            f"Temperature: {context.latest_temperature}C\n"
            f"Humidity: {context.latest_humidity}%\n"
            f"Servo Angle: {context.latest_servo_angle} degrees\n"
            f"Fan Status: {context.latest_fan_status}\n"
            f"System Status: {context.latest_status}\n"
            f"Predicted 15-min Power: {context.latest_prediction}W (Confidence: {context.prediction_confidence})\n"
            f"Active Alerts: {alerts_str}\n"
            f"Recent Trend (Last hour): {context.recent_trend_summary}\n"
            "------------------------"
        )
        
        full_prompt = f"{system_prompt}\n\n{context_str}\n\nUser Question: {question}\n\nAnswer:"
        
        response = await self.model.generate_content_async(
            full_prompt,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            }
        )
        
        return ChatResponse(
            answer=response.text.strip(),
            context_summary=context,
            suggested_questions=[
                "What is the current system status?",
                "Why is power low right now?",
                "Is there overheating risk?",
                "What influences power the most?",
                "Explain the current alert",
                "What trend do you see in the last hour?"
            ]
        )

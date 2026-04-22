from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, description="The natural language question to ask the chatbot.")

class ChatContextSummary(BaseModel):
    latest_power: Optional[float] = None
    latest_lux: Optional[float] = None
    latest_temperature: Optional[float] = None
    latest_humidity: Optional[float] = None
    latest_servo_angle: Optional[float] = None
    latest_fan_status: Optional[str] = None
    latest_status: Optional[str] = None
    latest_prediction: Optional[float] = None
    prediction_confidence: Optional[float] = None
    active_alerts: List[str] = []
    recent_trend_summary: Optional[str] = None
    
class ChatResponse(BaseModel):
    answer: str
    context_summary: ChatContextSummary
    suggested_questions: List[str] = []

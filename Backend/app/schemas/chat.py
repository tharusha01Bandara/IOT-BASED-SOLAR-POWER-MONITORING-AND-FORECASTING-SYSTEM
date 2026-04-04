"""
Chat schemas for grounded conversational analytics.

These schemas define the API contract for chat-driven
visual analytics exploration and decision support.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Literal
from pydantic import BaseModel, Field


TimeRange = Literal["15m", "1h", "6h", "24h", "7d"]
ChatIntent = Literal["trend", "comparison", "anomaly", "factor", "recommendation", "general"]


class ChatVisualContext(BaseModel):
    """Current dashboard state sent by the frontend."""

    selected_chart: Optional[str] = Field(default=None, max_length=100)
    selected_window_start: Optional[datetime] = Field(default=None)
    selected_window_end: Optional[datetime] = Field(default=None)
    selected_metric: Optional[Literal["power", "lux", "temperature", "humidity", "prediction"]] = Field(default=None)
    filters: Dict[str, Any] = Field(default_factory=dict)


class ChatQueryRequest(BaseModel):
    """Primary chat query request."""

    session_id: str = Field(..., min_length=1, max_length=100)
    device_id: str = Field(..., min_length=1, max_length=50)
    query: str = Field(..., min_length=2, max_length=2000)
    time_range: TimeRange = Field(default="1h")
    visual_context: Optional[ChatVisualContext] = Field(default=None)


class ChatEvidence(BaseModel):
    """Data-backed evidence used to generate the response."""

    stats: Dict[str, Any] = Field(default_factory=dict)
    points: List[Dict[str, Any]] = Field(default_factory=list)
    source_endpoints: List[str] = Field(default_factory=list)


class ChatQueryResponse(BaseModel):
    """Chat response payload."""

    answer: str
    intent: ChatIntent
    confidence: float = Field(..., ge=0.0, le=1.0)
    evidence: ChatEvidence
    suggested_actions: List[str] = Field(default_factory=list)
    follow_up_questions: List[str] = Field(default_factory=list)


class ExplainAnomalyRequest(BaseModel):
    """Request for anomaly explanation near a specific timestamp."""

    device_id: str = Field(..., min_length=1, max_length=50)
    timestamp: datetime
    window_minutes: int = Field(default=60, ge=15, le=1440)


class ExplainAnomalyResponse(BaseModel):
    """Structured anomaly explanation response."""

    anomaly_summary: str
    likely_causes: List[str] = Field(default_factory=list)
    supporting_metrics: Dict[str, Any] = Field(default_factory=dict)
    operator_recommendation: str


class SuggestedQuestionsResponse(BaseModel):
    """Persona-specific suggested questions."""

    persona: str
    questions: List[str] = Field(default_factory=list)

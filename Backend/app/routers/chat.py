"""
Chat API router for grounded conversational analytics.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pymongo.collection import Collection

from app.core.config import Settings, get_settings
from app.core.logging import get_logger
from app.db.mongodb import get_predictions_collection, get_readings_collection
from app.schemas.chat import (
    ChatQueryRequest,
    ChatQueryResponse,
    ExplainAnomalyRequest,
    ExplainAnomalyResponse,
    SuggestedQuestionsResponse,
)
from app.schemas.readings import ErrorResponse
from app.services.chat_service import ChatService

logger = get_logger(__name__)

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
    responses={
        400: {"model": ErrorResponse, "description": "Bad Request"},
        500: {"model": ErrorResponse, "description": "Internal Server Error"},
        503: {"model": ErrorResponse, "description": "LLM Service Unavailable"},
    },
)


def get_chat_service(
    settings: Annotated[Settings, Depends(get_settings)],
    readings_collection: Annotated[Collection, Depends(get_readings_collection)],
    predictions_collection: Annotated[Collection, Depends(get_predictions_collection)],
) -> ChatService:
    """Dependency provider for chat service."""
    return ChatService(
        settings=settings,
        readings_collection=readings_collection,
        predictions_collection=predictions_collection,
    )


@router.post(
    "/query",
    response_model=ChatQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Ask grounded analytics question",
    description="Answers natural-language questions using real backend data plus LLM synthesis.",
)
async def chat_query(
    request: ChatQueryRequest,
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> ChatQueryResponse:
    """Grounded chat endpoint."""
    try:
        result = await service.answer_query(
            device_id=request.device_id,
            query=request.query,
            time_range=request.time_range,
            visual_context=request.visual_context.model_dump() if request.visual_context else None,
        )
        return ChatQueryResponse(**result)
    except ValueError as exc:
        message = str(exc)
        # LLM misconfiguration or upstream LLM errors should be explicit.
        if "LLM" in message or "llm" in message or "Missing LLM_API_KEY" in message:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail={
                    "success": False,
                    "error": "LLMUnavailable",
                    "message": message,
                },
            ) from exc

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "ChatValidationError",
                "message": message,
            },
        ) from exc
    except Exception as exc:
        logger.error(f"Unexpected error in /chat/query: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "ChatInternalError",
                "message": "Failed to process chat query.",
            },
        ) from exc


@router.post(
    "/explain-anomaly",
    response_model=ExplainAnomalyResponse,
    status_code=status.HTTP_200_OK,
    summary="Explain anomaly at a timestamp",
    description="Produces structured anomaly explanation using reading history around the target time.",
)
async def explain_anomaly(
    request: ExplainAnomalyRequest,
    service: Annotated[ChatService, Depends(get_chat_service)],
) -> ExplainAnomalyResponse:
    """Anomaly explanation endpoint."""
    try:
        result = await service.explain_anomaly(
            device_id=request.device_id,
            timestamp=request.timestamp,
            window_minutes=request.window_minutes,
        )
        return ExplainAnomalyResponse(**result)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "success": False,
                "error": "AnomalyValidationError",
                "message": str(exc),
            },
        ) from exc
    except Exception as exc:
        logger.error(f"Unexpected error in /chat/explain-anomaly: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "AnomalyInternalError",
                "message": "Failed to explain anomaly.",
            },
        ) from exc


@router.get(
    "/suggested-questions",
    response_model=SuggestedQuestionsResponse,
    status_code=status.HTTP_200_OK,
    summary="Get suggested question starters",
    description="Returns persona-specific question starters for dashboard exploration.",
)
async def suggested_questions(
    service: Annotated[ChatService, Depends(get_chat_service)],
    persona: str = Query(default="operator", max_length=80),
) -> SuggestedQuestionsResponse:
    """Suggested prompts endpoint."""
    try:
        result = service.suggested_questions(persona=persona)
        return SuggestedQuestionsResponse(**result)
    except Exception as exc:
        logger.error(f"Unexpected error in /chat/suggested-questions: {exc}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "success": False,
                "error": "SuggestedQuestionsInternalError",
                "message": "Failed to load suggested questions.",
            },
        ) from exc

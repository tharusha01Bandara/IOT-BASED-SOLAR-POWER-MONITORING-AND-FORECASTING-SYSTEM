from fastapi import APIRouter, Depends
from pymongo.collection import Collection
from typing import Annotated

from app.core.config import Settings, get_settings
from app.db.mongodb import get_readings_collection, get_predictions_collection
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.chat_service import ChatService

router = APIRouter(
    prefix="/chat",
    tags=["chat"],
)

def get_chat_service(
    settings: Annotated[Settings, Depends(get_settings)],
    readings_collection: Annotated[Collection, Depends(get_readings_collection)],
    predictions_collection: Annotated[Collection, Depends(get_predictions_collection)],
) -> ChatService:
    return ChatService(
        settings=settings,
        readings_collection=readings_collection,
        predictions_collection=predictions_collection,
    )

@router.post("/query", response_model=ChatResponse)
async def chat_query(
    request: ChatRequest,
    service: Annotated[ChatService, Depends(get_chat_service)],
):
    return await service.process_query(request)

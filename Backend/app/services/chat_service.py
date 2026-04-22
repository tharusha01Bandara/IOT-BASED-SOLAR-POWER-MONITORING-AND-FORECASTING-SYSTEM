from pymongo.collection import Collection
from app.core.config import Settings
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.context_builder import ContextBuilder
from app.services.llm_service import LLMService
from app.services.fallback_chat_service import FallbackChatService

class ChatService:
    def __init__(self, settings: Settings, readings_collection: Collection, predictions_collection: Collection):
        self.settings = settings
        self.context_builder = ContextBuilder(readings_collection, predictions_collection)
        self.llm_service = LLMService(settings)
        self.fallback_service = FallbackChatService()
        
    async def process_query(self, request: ChatRequest) -> ChatResponse:
        context = await self.context_builder.build_context()
        
        if self.llm_service.is_available():
            try:
                return await self.llm_service.generate_response(request.question, context)
            except Exception as e:
                print(f"Error calling LLM: {e}")
                if self.settings.chat_fallback_enabled:
                    return self.fallback_service.generate_response(request.question, context, error_msg=str(e))
                raise e
        else:
            if self.settings.chat_fallback_enabled:
                return self.fallback_service.generate_response(request.question, context, error_msg="LLM Provider not initialized (Missing API Key via environment variables).")
            else:
                raise Exception("LLM provider unavailable and fallback disabled.")

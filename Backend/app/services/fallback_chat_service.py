from app.schemas.chat import ChatResponse, ChatContextSummary

class FallbackChatService:
    @staticmethod
    def generate_response(question: str, context: ChatContextSummary, error_msg: str = "") -> ChatResponse:
        q_lower = question.lower()
        
        answer = "I'm sorry, I am currently operating in fallback mode and cannot fully understand your question. Please ensure the Gemini API key is configured and valid."
        if error_msg:
            answer += f" (System Error: {error_msg})"
            
        
        if "status" in q_lower:
            answer = f"The current system status is {context.latest_status}. Power is {context.latest_power}W and temperature is {context.latest_temperature}C."
        elif "overheat" in q_lower or "temperature" in q_lower:
            if context.latest_temperature and float(context.latest_temperature) > 40:
                answer = "The panel temperature is high (over 40C). Yes, there is overheating risk. Check the active cooling fan."
            else:
                answer = f"The panel temperature is {context.latest_temperature}C, which is currently normal."
        elif "why is power" in q_lower and "low" in q_lower:
            answer = "Low power could be due to low lux levels, high temperature causing efficiency loss, or dirt on the panel. Check the active alerts."
        elif "alert" in q_lower:
            if context.active_alerts:
                answer = f"There are active alerts: {', '.join(context.active_alerts)}. Please check the dashboard panels."
            else:
                answer = "There are currently no active alerts."
        elif "trend" in q_lower:
            answer = f"In the last hour: {context.recent_trend_summary}"
        elif "influence" in q_lower or "factor" in q_lower:
            answer = "Lux (light intensity) is the strongest positive factor for power. High temperature has a slight negative effect. The servo angle helps optimize lux."
            
        return ChatResponse(
            answer=answer,
            context_summary=context,
            suggested_questions=[
                "What is the current system status?",
                "Is there overheating risk?",
                "Explain the current alert"
            ]
        )

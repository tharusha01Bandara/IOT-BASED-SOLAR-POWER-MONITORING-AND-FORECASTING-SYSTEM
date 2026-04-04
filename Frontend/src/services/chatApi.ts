import {
  ChatPersona,
  ChatQueryRequest,
  ChatQueryResponse,
  ExplainAnomalyRequest,
  ExplainAnomalyResponse,
  SuggestedQuestionsResponse,
} from "@/types/chat";

const API_BASE_URL =
  (globalThis as { __API_BASE_URL__?: string }).__API_BASE_URL__ ?? "http://localhost:8000";

class ChatApiError extends Error {
  status: number;

  constructor(message: string, status: number) {
    super(message);
    this.name = "ChatApiError";
    this.status = status;
  }
}

async function parseJsonResponse<T>(response: Response): Promise<T> {
  if (response.ok) {
    return response.json() as Promise<T>;
  }

  let errorMessage = `Request failed with status ${response.status}`;

  try {
    const payload = await response.json();
    if (payload?.detail) {
      errorMessage = typeof payload.detail === "string" ? payload.detail : JSON.stringify(payload.detail);
    }
  } catch {
    // Keep fallback message if response is not JSON.
  }

  throw new ChatApiError(errorMessage, response.status);
}

export async function sendChatQuery(payload: ChatQueryRequest): Promise<ChatQueryResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat/query`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<ChatQueryResponse>(response);
}

export async function explainAnomaly(payload: ExplainAnomalyRequest): Promise<ExplainAnomalyResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat/explain-anomaly`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

  return parseJsonResponse<ExplainAnomalyResponse>(response);
}

export async function getSuggestedQuestions(persona: ChatPersona): Promise<SuggestedQuestionsResponse> {
  const response = await fetch(`${API_BASE_URL}/api/chat/suggested-questions?persona=${encodeURIComponent(persona)}`);
  return parseJsonResponse<SuggestedQuestionsResponse>(response);
}

export { ChatApiError };

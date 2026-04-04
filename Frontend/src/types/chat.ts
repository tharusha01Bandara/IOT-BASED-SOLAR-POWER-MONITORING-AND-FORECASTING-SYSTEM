export type ChatIntent =
  | "trend"
  | "comparison"
  | "anomaly"
  | "factor"
  | "recommendation"
  | "general";

export type ChatPersona =
  | "operator"
  | "energy_manager"
  | "maintenance_technician"
  | "academic_evaluator";

export interface ChatEvidencePoint {
  timestamp: string;
  value: number;
}

export interface ChatEvidence {
  stats: Record<string, string | number | boolean | null>;
  points: ChatEvidencePoint[];
  source_endpoints: string[];
}

export interface ChatQueryRequest {
  device_id: string;
  query: string;
  time_range: "15m" | "1h" | "6h" | "24h" | "7d";
  visual_context?: Record<string, unknown>;
}

export interface ChatQueryResponse {
  answer: string;
  intent: ChatIntent;
  confidence: number;
  evidence: ChatEvidence;
  suggested_actions: string[];
  follow_up_questions: string[];
}

export interface ExplainAnomalyRequest {
  device_id: string;
  timestamp: string;
}

export interface ExplainAnomalyResponse {
  summary: string;
  likely_causes: string[];
  confidence: number;
  suggested_actions: string[];
  evidence: ChatEvidence;
}

export interface SuggestedQuestionsResponse {
  persona: ChatPersona;
  questions: string[];
}

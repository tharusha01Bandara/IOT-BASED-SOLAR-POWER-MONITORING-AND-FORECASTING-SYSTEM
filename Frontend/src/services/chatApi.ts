import apiClient from '../api/client';

export interface ChatResponse {
  answer: string;
  context_summary: Record<string, any>;
  suggested_questions?: string[];
}

export const chatQuery = async (question: string): Promise<ChatResponse> => {
  return apiClient.post<ChatResponse>('/api/chat/query', { 
    question 
  });
};

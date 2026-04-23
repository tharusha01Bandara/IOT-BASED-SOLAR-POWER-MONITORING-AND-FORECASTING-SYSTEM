import { useState } from 'react';
import { chatQuery } from '../services/chatApi';

export interface Message {
  id: string;
  type: 'user' | 'assistant';
  text: string;
  suggested_questions?: string[];
}

export const useChat = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const sendMessage = async (question: string) => {
    if (!question.trim()) return;
    
    const userMsg: Message = { id: Date.now().toString(), type: 'user', text: question };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await chatQuery(question);
      const assistantMsg: Message = { 
        id: (Date.now() + 1).toString(), 
        type: 'assistant', 
        text: response.answer,
        suggested_questions: response.suggested_questions
      };
      setMessages(prev => [...prev, assistantMsg]);
    } catch (err: any) {
      setError(err.message || 'An error occurred while fetching the response.');
    } finally {
      setIsLoading(false);
    }
  };

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    setMessages
  };
};

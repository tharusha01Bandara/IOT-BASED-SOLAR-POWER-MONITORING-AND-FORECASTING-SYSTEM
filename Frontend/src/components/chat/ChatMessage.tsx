import React from 'react';
import type { Message } from '../../hooks/useChat';
import { Bot, User } from 'lucide-react';
import { Button } from '../ui/button';

interface ChatMessageProps {
  message: Message;
  onSuggestionClick: (suggestion: string) => void;
  isLast: boolean;
}

export const ChatMessage: React.FC<ChatMessageProps> = ({ message, onSuggestionClick, isLast }) => {
  const isUser = message.type === 'user';
  
  return (
    <div className={`flex flex-col gap-2 ${isUser ? 'items-end' : 'items-start'} mb-4 w-full`}>
      <div className={`flex items-start max-w-[85%] gap-2 ${isUser ? 'flex-row-reverse' : 'flex-row'}`}>
        <div className={`p-2 rounded-full flex-shrink-0 ${isUser ? 'bg-primary text-primary-foreground' : 'bg-secondary text-secondary-foreground'}`}>
          {isUser ? <User size={16} /> : <Bot size={16} />}
        </div>
        
        <div className={`p-3 rounded-lg text-sm ${isUser ? 'bg-primary text-primary-foreground rounded-tr-none' : 'bg-muted text-foreground rounded-tl-none'}`}>
          {message.text}
        </div>
      </div>
      
      {!isUser && message.suggested_questions && message.suggested_questions.length > 0 && isLast && (
        <div className="flex flex-wrap gap-2 mt-2 ml-10">
          <span className="text-xs text-muted-foreground w-full mb-1">Suggested follow-ups:</span>
          {message.suggested_questions.filter(q => q && q.trim() !== "").map((q, i) => (
            <Button 
                key={i} 
                variant="outline" 
                size="sm" 
                className="text-xs h-7 rounded-full bg-background"
                onClick={() => onSuggestionClick(q)}
            >
              {q}
            </Button>
          ))}
        </div>
      )}
    </div>
  );
};

import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, X, Send, AlertCircle } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { useChat } from '../../hooks/useChat';
import { ChatMessage } from './ChatMessage';

export const ChatWidget: React.FC = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);
  
  const { messages, isLoading, error, sendMessage, setMessages } = useChat();

  const handleSend = () => {
    if (input.trim()) {
      sendMessage(input);
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleSend();
    }
  };

  const handleSuggestionClick = (suggestion: string) => {
    sendMessage(suggestion);
  };

  // Auto-scroll to bottom when messages change
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
      // Scroll area structure is tricky sometimes, so we also look for viewport inside scroll area
      const viewport = scrollRef.current.querySelector('[data-radix-scroll-area-viewport]');
      if (viewport) {
        viewport.scrollTop = viewport.scrollHeight;
      }
    }
  }, [messages, isLoading]);

  // Initial welcome message
  useEffect(() => {
    if (isOpen && messages.length === 0) {
      setMessages([
        {
          id: 'welcome',
          type: 'assistant',
          text: 'Hello! I am your Solar Analytics Assistant. I can help answer questions about the current state, trends, predictions, and alerts. How can I help you today?',
          suggested_questions: [
            "What is the current system status?",
            "Why is power low right now?",
            "Is there overheating risk?",
            "What influences power the most?",
            "Explain the current alert",
            "What trend do you see in the last hour?"
          ]
        }
      ]);
    }
  }, [isOpen, messages.length, setMessages]);

  return (
    <>
      {!isOpen && (
        <Button
          onClick={() => setIsOpen(true)}
          className="fixed bottom-6 right-6 h-14 w-14 rounded-full shadow-lg p-0 z-50 bg-primary text-primary-foreground hover:scale-105 transition-transform"
        >
          <MessageCircle size={28} />
        </Button>
      )}

      {isOpen && (
        <div className="fixed bottom-6 right-6 w-[380px] h-[550px] max-h-[85vh] bg-background border rounded-xl shadow-2xl z-50 flex flex-col overflow-hidden animate-in slide-in-from-bottom-5">
          <div className="bg-primary p-4 flex justify-between items-center text-primary-foreground">
            <div className="flex items-center gap-2">
              <MessageCircle size={20} />
              <div>
                <h3 className="font-semibold text-sm">Solar Assistant</h3>
                <p className="text-[10px] opacity-80">Answers are based on live dashboard data</p>
              </div>
            </div>
            <Button variant="ghost" size="icon" className="h-8 w-8 hover:bg-white/20 rounded-full" onClick={() => setIsOpen(false)}>
              <X size={18} />
            </Button>
          </div>

          <div className="flex-1 overflow-y-auto p-4 flex flex-col gap-1" ref={scrollRef}>
            {messages.map((msg, i) => (
              <ChatMessage 
                key={msg.id} 
                message={msg} 
                isLast={i === messages.length - 1}
                onSuggestionClick={handleSuggestionClick} 
              />
            ))}
            
            {isLoading && (
              <div className="flex items-start max-w-[85%] gap-2 mb-4">
                <div className="p-2 rounded-full flex-shrink-0 bg-secondary text-secondary-foreground">
                  <MessageCircle size={16} className="animate-pulse" />
                </div>
                <div className="bg-muted p-3 rounded-lg rounded-tl-none flex gap-1">
                  <div className="w-2 h-2 rounded-full bg-primary/40 animate-bounce" />
                  <div className="w-2 h-2 rounded-full bg-primary/40 animate-bounce" style={{ animationDelay: '0.2s' }} />
                  <div className="w-2 h-2 rounded-full bg-primary/40 animate-bounce" style={{ animationDelay: '0.4s' }} />
                </div>
              </div>
            )}
            
            {error && (
              <div className="flex items-start gap-2 max-w-[85%] text-destructive mt-2">
                <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
                <span className="text-xs">{error}</span>
              </div>
            )}
          </div>

          <div className="p-3 border-t bg-muted/50">
            <div className="flex gap-2 relative">
              <Input
                placeholder="Ask about your solar data..."
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                disabled={isLoading}
                className="pr-10 bg-background"
              />
              <Button
                size="icon"
                className="absolute right-1 top-1 h-8 w-8 bg-primary text-primary-foreground hover:bg-primary/90"
                onClick={handleSend}
                disabled={!input.trim() || isLoading}
              >
                <Send size={16} />
              </Button>
            </div>
          </div>
        </div>
      )}
    </>
  );
};

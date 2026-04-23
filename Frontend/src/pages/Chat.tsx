import React, { useState, useRef, useEffect } from 'react';
import { MessageCircle, Send, AlertCircle } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { useChat } from '@/hooks/useChat';
import { ChatMessage } from '@/components/chat/ChatMessage';

export default function Chat() {
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

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  useEffect(() => {
    if (messages.length === 0) {
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
  }, [messages.length, setMessages]);

  return (
    <div className="flex flex-col h-[calc(100vh-8rem)] max-w-4xl mx-auto bg-background border rounded-xl shadow-sm">
      <div className="bg-primary p-4 rounded-t-xl flex justify-between items-center text-primary-foreground">
        <div className="flex items-center gap-2">
          <MessageCircle size={24} />
          <div>
            <h2 className="font-semibold text-lg">Solar Analytics Assistant</h2>
            <p className="text-xs opacity-90">Answers are based on live dashboard data</p>
          </div>
        </div>
      </div>

      <div className="flex-1 overflow-y-auto p-6 flex flex-col gap-2" ref={scrollRef}>
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
             <div className="bg-muted p-4 rounded-lg rounded-tl-none flex gap-2">
                <div className="w-2.5 h-2.5 rounded-full bg-primary/40 animate-bounce" />
                <div className="w-2.5 h-2.5 rounded-full bg-primary/40 animate-bounce" style={{ animationDelay: '0.2s' }} />
                <div className="w-2.5 h-2.5 rounded-full bg-primary/40 animate-bounce" style={{ animationDelay: '0.4s' }} />
             </div>
          </div>
        )}
        
        {error && (
          <div className="flex items-start gap-2 max-w-[85%] text-destructive mt-2">
            <AlertCircle size={16} className="mt-0.5 flex-shrink-0" />
            <span className="text-sm">{error}</span>
          </div>
        )}
      </div>

      <div className="p-4 border-t bg-muted/30 rounded-b-xl">
        <div className="flex gap-3 relative max-w-3xl mx-auto">
          <Input
            placeholder="Ask about your solar data..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            disabled={isLoading}
            className="pr-12 bg-background py-6"
          />
          <Button
            size="icon"
            className="absolute right-2 top-2 h-8 w-8 bg-primary text-primary-foreground hover:bg-primary/90"
            onClick={handleSend}
            disabled={!input.trim() || isLoading}
          >
            <Send size={18} />
          </Button>
        </div>
      </div>
    </div>
  );
}

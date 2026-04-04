import { FormEvent, useEffect, useMemo, useState } from "react";
import { Bot, Loader2, SendHorizontal, UserRound, Wrench } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Textarea } from "@/components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { useSolarContext } from "@/contexts/SolarDataContext";
import { ChatApiError, getSuggestedQuestions, sendChatQuery } from "@/services/chatApi";
import { ChatPersona, ChatQueryResponse } from "@/types/chat";

type ChatRole = "user" | "assistant";

interface ChatMessage {
  id: string;
  role: ChatRole;
  text: string;
  timestamp: string;
  payload?: ChatQueryResponse;
}

const PERSONA_LABELS: Record<ChatPersona, string> = {
  operator: "Operator",
  energy_manager: "Energy Manager",
  maintenance_technician: "Maintenance Technician",
  academic_evaluator: "Academic Evaluator",
};

const DEVICE_ID = "tracker01";

function getFriendlyError(error: unknown) {
  if (error instanceof ChatApiError) {
    if (error.status === 503) {
      return "LLM service is unavailable. Check backend LLM settings and API key.";
    }
    return error.message;
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "Unable to process your request right now.";
}

function toPercentage(value: number) {
  return `${Math.round(value * 100)}%`;
}

export default function Chat() {
  const { timeRange, currentReading } = useSolarContext();
  const [persona, setPersona] = useState<ChatPersona>("operator");
  const [input, setInput] = useState("");
  const [messages, setMessages] = useState<ChatMessage[]>([
    {
      id: "assistant-initial",
      role: "assistant",
      text: "Ask me about trends, anomalies, power predictions, or recommendations for this device.",
      timestamp: new Date().toISOString(),
    },
  ]);
  const [suggestions, setSuggestions] = useState<string[]>([]);
  const [isLoadingSuggestions, setIsLoadingSuggestions] = useState(false);
  const [isSending, setIsSending] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;

    async function loadSuggestions() {
      setIsLoadingSuggestions(true);
      setError(null);

      try {
        const result = await getSuggestedQuestions(persona);
        if (!cancelled) {
          setSuggestions(result.questions);
        }
      } catch (err) {
        if (!cancelled) {
          setSuggestions([]);
          setError(getFriendlyError(err));
        }
      } finally {
        if (!cancelled) {
          setIsLoadingSuggestions(false);
        }
      }
    }

    loadSuggestions();
    return () => {
      cancelled = true;
    };
  }, [persona]);

  const canSubmit = useMemo(() => input.trim().length > 0 && !isSending, [input, isSending]);

  async function submitQuery(query: string) {
    const normalizedQuery = query.trim();
    if (!normalizedQuery || isSending) {
      return;
    }

    const nowIso = new Date().toISOString();
    const userMessage: ChatMessage = {
      id: `user-${nowIso}`,
      role: "user",
      text: normalizedQuery,
      timestamp: nowIso,
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    setError(null);
    setIsSending(true);

    try {
      const response = await sendChatQuery({
        device_id: DEVICE_ID,
        query: normalizedQuery,
        time_range: timeRange,
        visual_context: {
          selected_metric: "power",
          dashboard_time_range: timeRange,
          reading_snapshot: {
            power: currentReading.power,
            lux: currentReading.lux,
            temperature: currentReading.temperature,
            humidity: currentReading.humidity,
            fan_status: currentReading.fan_status,
          },
        },
      });

      const assistantMessage: ChatMessage = {
        id: `assistant-${new Date().toISOString()}`,
        role: "assistant",
        text: response.answer,
        timestamp: new Date().toISOString(),
        payload: response,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      setError(getFriendlyError(err));
    } finally {
      setIsSending(false);
    }
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    await submitQuery(input);
  }

  return (
    <div className="space-y-6 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-3">
        <div>
          <h1 className="text-xl md:text-2xl font-bold">AI Chat Assistant</h1>
          <p className="text-sm text-muted-foreground mt-0.5">
            Grounded responses from live telemetry, predictions, and anomaly signals.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Wrench className="w-4 h-4 text-muted-foreground" />
          <Select value={persona} onValueChange={(value) => setPersona(value as ChatPersona)}>
            <SelectTrigger className="w-[220px] h-9 text-xs">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="operator">Operator</SelectItem>
              <SelectItem value="energy_manager">Energy Manager</SelectItem>
              <SelectItem value="maintenance_technician">Maintenance Technician</SelectItem>
              <SelectItem value="academic_evaluator">Academic Evaluator</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      <div className="grid lg:grid-cols-[2fr_1fr] gap-4">
        <section className="glass-card rounded-xl p-4 md:p-5 animate-fade-in min-h-[560px] flex flex-col">
          <div className="flex items-center justify-between gap-2 mb-3">
            <h2 className="text-sm font-semibold">Conversation</h2>
            <div className="text-xs text-muted-foreground">
              Device {DEVICE_ID} · {timeRange}
            </div>
          </div>

          <Separator className="mb-4" />

          <div className="flex-1 space-y-4 overflow-auto pr-1">
            {messages.map((message) => (
              <article key={message.id} className={`flex gap-3 ${message.role === "user" ? "justify-end" : "justify-start"}`}>
                {message.role === "assistant" && (
                  <div className="w-8 h-8 rounded-full bg-primary/10 text-primary flex items-center justify-center shrink-0">
                    <Bot className="w-4 h-4" />
                  </div>
                )}

                <div className={`max-w-[90%] md:max-w-[80%] rounded-xl border px-3 py-2 ${message.role === "user" ? "bg-primary text-primary-foreground border-primary" : "bg-card border-border"}`}>
                  <p className="text-sm leading-6 whitespace-pre-wrap">{message.text}</p>
                  <p className={`text-[11px] mt-1 ${message.role === "user" ? "text-primary-foreground/80" : "text-muted-foreground"}`}>
                    {new Date(message.timestamp).toLocaleTimeString()}
                  </p>

                  {message.payload && (
                    <div className="mt-3 pt-3 border-t border-border/70 space-y-3">
                      <div className="flex flex-wrap items-center gap-2">
                        <Badge variant="secondary" className="text-[10px]">
                          Intent: {message.payload.intent}
                        </Badge>
                        <Badge variant="outline" className="text-[10px]">
                          Confidence: {toPercentage(message.payload.confidence)}
                        </Badge>
                      </div>

                      {message.payload.suggested_actions.length > 0 && (
                        <div>
                          <p className="text-xs font-medium mb-1">Suggested actions</p>
                          <ul className="text-xs text-muted-foreground space-y-1">
                            {message.payload.suggested_actions.map((action) => (
                              <li key={action}>• {action}</li>
                            ))}
                          </ul>
                        </div>
                      )}

                      {message.payload.evidence.source_endpoints.length > 0 && (
                        <div>
                          <p className="text-xs font-medium mb-1">Evidence endpoints</p>
                          <div className="flex flex-wrap gap-1.5">
                            {message.payload.evidence.source_endpoints.map((endpoint) => (
                              <Badge key={endpoint} variant="outline" className="text-[10px]">
                                {endpoint}
                              </Badge>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>

                {message.role === "user" && (
                  <div className="w-8 h-8 rounded-full bg-secondary text-secondary-foreground flex items-center justify-center shrink-0">
                    <UserRound className="w-4 h-4" />
                  </div>
                )}
              </article>
            ))}

            {isSending && (
              <div className="flex items-center gap-2 text-xs text-muted-foreground px-1">
                <Loader2 className="w-3.5 h-3.5 animate-spin" />
                Thinking with grounded telemetry...
              </div>
            )}
          </div>

          <form className="mt-4 pt-4 border-t border-border" onSubmit={handleSubmit}>
            <div className="flex gap-2">
              <Textarea
                value={input}
                onChange={(event) => setInput(event.target.value)}
                placeholder="Ask about trends, anomalies, causes, or optimization recommendations..."
                className="min-h-[76px] resize-none"
              />
              <Button type="submit" size="icon" className="h-auto w-11" disabled={!canSubmit}>
                {isSending ? <Loader2 className="w-4 h-4 animate-spin" /> : <SendHorizontal className="w-4 h-4" />}
              </Button>
            </div>
            {error && <p className="text-xs text-destructive mt-2">{error}</p>}
          </form>
        </section>

        <section className="glass-card rounded-xl p-4 md:p-5 animate-fade-in space-y-4">
          <div>
            <h2 className="text-sm font-semibold">Quick Prompts</h2>
            <p className="text-xs text-muted-foreground mt-1">
              Persona: {PERSONA_LABELS[persona]}
            </p>
          </div>

          <Separator />

          {isLoadingSuggestions ? (
            <div className="flex items-center gap-2 text-xs text-muted-foreground">
              <Loader2 className="w-3.5 h-3.5 animate-spin" />
              Loading suggestions...
            </div>
          ) : suggestions.length === 0 ? (
            <p className="text-xs text-muted-foreground">No suggestions available right now.</p>
          ) : (
            <div className="space-y-2">
              {suggestions.map((question) => (
                <Button
                  key={question}
                  type="button"
                  variant="outline"
                  className="w-full text-left justify-start h-auto whitespace-normal py-2"
                  onClick={() => submitQuery(question)}
                  disabled={isSending}
                >
                  {question}
                </Button>
              ))}
            </div>
          )}

          <Separator />

          <div className="space-y-2">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">Tips</h3>
            <p className="text-xs text-muted-foreground">
              Ask comparative questions with an explicit period (for example: "Compare output in the last 1h vs 6h").
            </p>
            <p className="text-xs text-muted-foreground">
              Responses include confidence and source endpoints so you can verify grounding.
            </p>
          </div>
        </section>
      </div>
    </div>
  );
}

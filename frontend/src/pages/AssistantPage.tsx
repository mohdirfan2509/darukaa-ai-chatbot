import { FormEvent, useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { EnvironmentalContext } from "../components/EnvironmentalContext";
import { EvidencePanel } from "../components/EvidencePanel";
import { ReasoningSummary } from "../components/ReasoningSummary";
import { RecommendationCards } from "../components/RecommendationCards";
import { DEMO_SCENARIOS } from "../data/scenarios";
import { api } from "../services/api";
import type { Message, StructuredAIResponse } from "../types";

interface Props {
  initialPrompt?: string;
}

export function AssistantPage({ initialPrompt }: Props) {
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<Message[]>([]);
  const [latest, setLatest] = useState<StructuredAIResponse | null>(null);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [known, setKnown] = useState<Record<string, unknown>>({});

  useEffect(() => {
    if (initialPrompt) {
      void startWithPrompt(initialPrompt);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [initialPrompt]);

  const context = useMemo(
    () => latest?.environmental_context || {},
    [latest]
  );

  async function ensureConversation(): Promise<string> {
    if (conversationId) return conversationId;
    const conv = await api.createConversation("New assessment");
    setConversationId(conv.id);
    return conv.id;
  }

  async function send(content: string) {
    if (!content.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const id = await ensureConversation();
      const optimistic: Message = {
        id: `tmp-${Date.now()}`,
        role: "user",
        content,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, optimistic]);
      setInput("");
      const result = await api.sendMessage(id, content);
      const assistant: Message = {
        id: (result.message as Message).id,
        role: "assistant",
        content: result.response.answer,
        structured_payload: result.response,
        created_at: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistant]);
      setLatest(result.response);
      setKnown(
        (result.response.environmental_context?._provenance as { user_provided?: string[] })
          ? Object.fromEntries(
              Object.entries(result.response.environmental_context).filter(
                ([k]) => k !== "_provenance"
              )
            )
          : {}
      );
      // Refresh known from conversation context
      const detail = (await api.getConversation(id)) as {
        context?: { known_variables?: Record<string, unknown> };
      };
      if (detail.context?.known_variables) {
        setKnown(detail.context.known_variables);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Request failed");
    } finally {
      setLoading(false);
    }
  }

  async function startWithPrompt(prompt: string) {
    setMessages([]);
    setLatest(null);
    setConversationId(null);
    setKnown({});
    await send(prompt);
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    void send(input);
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>AI Biodiversity Intelligence Assistant</h1>
        <p>
          Evidence-grounded environmental reasoning with RAG — not an LLM-only chatbot.
        </p>
      </div>

      <div className="panel">
        <p className="section-title">Demo scenarios (Synthetic Demo Data)</p>
        <div className="scenario-grid">
          {DEMO_SCENARIOS.map((s) => (
            <button
              key={s.id}
              className="scenario-card"
              type="button"
              onClick={() => void startWithPrompt(s.prompt)}
            >
              <span className="badge">{s.label}</span>
              <strong>{s.title}</strong>
              <p className="muted">{s.description}</p>
            </button>
          ))}
        </div>
      </div>

      <div className="chat-layout">
        <div className="panel">
          <div className="messages" data-testid="messages">
            {messages.length === 0 && (
              <p className="muted">
                Ask an environmental question or select a synthetic demo scenario.
              </p>
            )}
            {messages.map((m) => (
              <div key={m.id} className={`bubble ${m.role}`} data-testid={`msg-${m.role}`}>
                {m.content}
              </div>
            ))}
            {loading && <p className="loading">Analyzing environmental context…</p>}
            {error && <p className="error">{error}</p>}
          </div>
          <form className="composer" onSubmit={onSubmit}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Describe soil, climate, land use, biodiversity…"
              data-testid="chat-input"
            />
            <button className="btn" type="submit" disabled={loading || !input.trim()}>
              Send
            </button>
          </form>
          {latest?.needs_clarification && (
            <p className="muted" style={{ marginTop: "0.5rem" }}>
              Clarification needed. You can also open{" "}
              <Link to="/demo">Demo Mode</Link>.
            </p>
          )}
        </div>

        <div className="side-stack">
          <div className="panel">
            <EnvironmentalContext context={context} knownVariables={known} />
          </div>
          <div className="panel">
            <ReasoningSummary
              summary={latest?.reasoning_summary || []}
              variables={latest?.environmental_assessment?.variables_considered || []}
            />
          </div>
          <div className="panel">
            <p className="section-title">Recommendations</p>
            <RecommendationCards recommendations={latest?.recommendations || []} />
          </div>
          <div className="panel">
            <EvidencePanel
              recommendations={latest?.recommendations || []}
              sourcesUsed={latest?.retrieval?.sources_used}
              chunksUsed={latest?.retrieval?.chunks_used}
            />
          </div>
        </div>
      </div>
    </div>
  );
}

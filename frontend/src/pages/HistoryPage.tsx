import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../services/api";
import type { ConversationSummary } from "../types";

export function HistoryPage() {
  const [items, setItems] = useState<ConversationSummary[]>([]);
  const [error, setError] = useState<string | null>(null);
  const navigate = useNavigate();

  useEffect(() => {
    api
      .listConversations()
      .then(setItems)
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load"));
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <h1>Conversation History</h1>
        <p>Previous multi-turn environmental assessments.</p>
      </div>
      <div className="panel">
        {error && <p className="error">{error}</p>}
        {!error && items.length === 0 && <p className="muted">No conversations yet.</p>}
        <ul className="list">
          {items.map((c) => (
            <li key={c.id} onClick={() => navigate(`/?resume=${c.id}`)}>
              <strong>{c.title || "Untitled"}</strong>
              <div className="muted">{new Date(c.updated_at).toLocaleString()}</div>
            </li>
          ))}
        </ul>
      </div>
    </div>
  );
}

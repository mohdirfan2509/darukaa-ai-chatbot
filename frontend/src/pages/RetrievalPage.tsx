import { FormEvent, useState } from "react";
import { api } from "../services/api";
import type { RetrievedChunk } from "../types";

export function RetrievalPage() {
  const [query, setQuery] = useState(
    "relationship between soil organic carbon biodiversity low rainfall monoculture"
  );
  const [results, setResults] = useState<RetrievedChunk[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: FormEvent) {
    e.preventDefault();
    setLoading(true);
    setError(null);
    try {
      const res = await api.searchKnowledge(query, 5);
      setResults(res.results);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Knowledge Retrieval (Developer View)</h1>
        <p>Demonstrates genuine vector / lexical retrieval from the knowledge base.</p>
      </div>
      <div className="panel">
        <form className="composer" onSubmit={onSubmit}>
          <textarea value={query} onChange={(e) => setQuery(e.target.value)} />
          <button className="btn" type="submit" disabled={loading}>
            Search
          </button>
        </form>
        {loading && <p className="loading">Retrieving…</p>}
        {error && <p className="error">{error}</p>}
        {results.map((r) => (
          <div className="retrieval-result" key={r.chunk_id} data-testid="retrieval-result">
            <div className="meta-row">
              <span className="chip accent">similarity {r.similarity}</span>
              <span className="chip">{r.topic || "topic n/a"}</span>
            </div>
            <strong>{String(r.source.title || "Source")}</strong>
            <div className="muted">
              {String(r.source.organization || "")} · {String(r.source.publication_year || "")}
            </div>
            <p>{r.content}</p>
          </div>
        ))}
      </div>
    </div>
  );
}

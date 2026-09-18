import type { Recommendation } from "../types";

interface Props {
  recommendations: Recommendation[];
  sourcesUsed?: number;
  chunksUsed?: number;
}

export function EvidencePanel({ recommendations, sourcesUsed, chunksUsed }: Props) {
  const sources = new Map<string, { title: string; organization?: string | null; year?: number | null; url?: string | null; type?: string | null; snippet: string }>();

  for (const rec of recommendations) {
    for (const ev of rec.evidence) {
      const key = `${ev.source_title}|${ev.url || ""}`;
      if (!sources.has(key)) {
        sources.set(key, {
          title: ev.source_title,
          organization: ev.organization,
          year: ev.publication_year,
          url: ev.url,
          type: ev.source_type,
          snippet: ev.relevant_snippet,
        });
      }
    }
  }

  return (
    <div>
      <p className="section-title">Sources Used</p>
      <p className="muted">
        Retrieval: {sourcesUsed ?? sources.size} sources / {chunksUsed ?? "—"} chunks
      </p>
      {sources.size === 0 && <p className="muted">No sources attached yet.</p>}
      {[...sources.values()].map((s) => (
        <div className="retrieval-result" key={s.title + (s.url || "")}>
          <strong>{s.title}</strong>
          <div className="muted">
            {s.organization || "—"} · {s.year || "n/a"} · {s.type || "source"}
          </div>
          {s.url && (
            <a href={s.url} target="_blank" rel="noreferrer">
              Open source
            </a>
          )}
          <p className="muted">{s.snippet}</p>
        </div>
      ))}
    </div>
  );
}

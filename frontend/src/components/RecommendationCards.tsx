import type { Recommendation } from "../types";

interface Props {
  recommendations: Recommendation[];
}

export function RecommendationCards({ recommendations }: Props) {
  if (!recommendations?.length) {
    return <p className="muted">No recommendations yet.</p>;
  }

  return (
    <div>
      {recommendations.map((rec) => (
        <article className="rec-card" key={rec.title}>
          <h3>{rec.title}</h3>
          <p>
            <strong>What to do:</strong> {rec.action}
          </p>
          <p>
            <strong>Why it works:</strong> {rec.scientific_reasoning}
          </p>
          <div className="meta-row">
            <span className="chip accent">Impact: {rec.impacted_metrics.join(", ") || "n/a"}</span>
            <span className="chip">Direction: {rec.expected_direction}</span>
            <span className="chip">Horizon: {rec.time_horizon}</span>
            <span className="chip">Confidence: {(rec.confidence * 100).toFixed(0)}%</span>
          </div>
          <p className="muted">
            <strong>Estimated effect:</strong>{" "}
            {rec.estimated_effect ||
              "Quantitative improvement could not be reliably estimated from the retrieved evidence."}
          </p>
          <details className="evidence">
            <summary>Evidence ({rec.evidence.length})</summary>
            {rec.evidence.map((ev, idx) => (
              <div key={`${ev.source_title}-${idx}`} style={{ marginTop: "0.5rem" }}>
                <div>
                  <strong>{ev.source_title}</strong>
                  {ev.organization ? ` — ${ev.organization}` : ""}
                  {ev.publication_year ? ` (${ev.publication_year})` : ""}
                </div>
                {ev.url && (
                  <div>
                    <a href={ev.url} target="_blank" rel="noreferrer">
                      Source URL
                    </a>
                  </div>
                )}
                <p className="muted">{ev.relevant_snippet}</p>
              </div>
            ))}
          </details>
        </article>
      ))}
    </div>
  );
}

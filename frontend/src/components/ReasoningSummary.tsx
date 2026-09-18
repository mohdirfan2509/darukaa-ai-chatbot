interface Props {
  summary: string[];
  variables: string[];
}

export function ReasoningSummary({ summary, variables }: Props) {
  return (
    <div>
      <p className="section-title">Reasoning Summary</p>
      <p className="muted">
        Variables considered: {variables.length ? variables.join(", ") : "—"}
      </p>
      <p className="muted" style={{ marginTop: "0.35rem" }}>
        Evidence-supported relationships:
      </p>
      <ul>
        {(summary.length ? summary : ["No reasoning summary yet."]).map((line) => (
          <li key={line}>{line}</li>
        ))}
      </ul>
    </div>
  );
}

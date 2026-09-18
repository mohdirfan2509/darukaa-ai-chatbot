import { useEffect, useState } from "react";
import { EnvironmentalContext } from "../components/EnvironmentalContext";
import { api } from "../services/api";

export function ContextPage() {
  const [text, setText] = useState(
    "Soil organic carbon is 0.3%, rainfall is low, wheat monoculture, habitat diversity low"
  );
  const [result, setResult] = useState<{
    environmental_state: Record<string, unknown>;
    known_variables: Record<string, unknown>;
    missing_variables: string[];
    assessment_summary: string;
  } | null>(null);
  const [error, setError] = useState<string | null>(null);

  async function analyze() {
    setError(null);
    try {
      const res = (await api.analyzeEnvironment(text)) as typeof result;
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analyze failed");
    }
  }

  useEffect(() => {
    void analyze();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return (
    <div className="page">
      <div className="page-header">
        <h1>Environmental Context</h1>
        <p>Inspect parsed environmental variables without running a full chat turn.</p>
      </div>
      <div className="panel">
        <textarea value={text} onChange={(e) => setText(e.target.value)} rows={4} style={{ width: "100%" }} />
        <div style={{ marginTop: "0.75rem" }}>
          <button className="btn" type="button" onClick={() => void analyze()}>
            Analyze
          </button>
        </div>
        {error && <p className="error">{error}</p>}
        {result && (
          <>
            <p style={{ marginTop: "1rem" }}>{result.assessment_summary}</p>
            <EnvironmentalContext
              context={result.environmental_state}
              knownVariables={result.known_variables}
            />
            <p className="muted">
              Missing: {result.missing_variables.join(", ") || "none"}
            </p>
          </>
        )}
      </div>
    </div>
  );
}

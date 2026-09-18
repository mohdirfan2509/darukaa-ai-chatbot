import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { DEMO_SCENARIOS } from "../data/scenarios";
import { AssistantPage } from "./AssistantPage";

export function DemoPage() {
  const [prompt, setPrompt] = useState<string | undefined>();
  const navigate = useNavigate();

  if (prompt) {
    return <AssistantPage initialPrompt={prompt} />;
  }

  return (
    <div className="page">
      <div className="page-header">
        <h1>Evaluator Demo Mode</h1>
        <p>
          Select a synthetic scenario or enter a free-form environmental question. All
          demo measurements are labeled Synthetic Demo Data.
        </p>
      </div>
      <div className="panel">
        <div className="scenario-grid">
          {DEMO_SCENARIOS.map((s) => (
            <button
              key={s.id}
              type="button"
              className="scenario-card"
              onClick={() => setPrompt(s.prompt)}
            >
              <span className="badge">{s.label}</span>
              <strong>{s.title}</strong>
              <p className="muted">{s.description}</p>
              <p className="muted" style={{ marginTop: "0.5rem" }}>
                {s.prompt}
              </p>
            </button>
          ))}
        </div>
        <div style={{ marginTop: "1rem" }}>
          <button className="btn secondary" type="button" onClick={() => navigate("/")}>
            Open free-form assistant
          </button>
        </div>
      </div>
    </div>
  );
}

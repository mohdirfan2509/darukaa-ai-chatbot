interface Props {
  context: Record<string, unknown>;
  knownVariables?: Record<string, unknown>;
}

function renderSection(title: string, data: Record<string, unknown> | undefined) {
  if (!data || Object.keys(data).length === 0) return null;
  return (
    <div className="ctx-group" key={title}>
      <h4>{title}</h4>
      <ul>
        {Object.entries(data).map(([k, v]) => (
          <li key={k}>
            {k.replace(/_/g, " ")}: {String(v)}
          </li>
        ))}
      </ul>
    </div>
  );
}

export function EnvironmentalContext({ context, knownVariables }: Props) {
  const soil = context.soil as Record<string, unknown> | undefined;
  const climate = context.climate as Record<string, unknown> | undefined;
  const land = context.land_use as Record<string, unknown> | undefined;
  const bio = context.biodiversity as Record<string, unknown> | undefined;
  const human = context.human_impact as Record<string, unknown> | undefined;
  const geo = context.geography as Record<string, unknown> | undefined;
  const provenance = context._provenance as
    | { user_provided?: string[]; inferred?: string[]; evidence_supported?: string[] }
    | undefined;

  const hasAny = soil || climate || land || bio || human || geo;

  return (
    <div>
      <p className="section-title">Environmental Context</p>
      {!hasAny && <p className="muted">No environmental variables captured yet.</p>}
      {renderSection("Soil", soil)}
      {renderSection("Climate", climate)}
      {renderSection("Land", land)}
      {renderSection("Biodiversity", bio)}
      {renderSection("Human impact", human)}
      {renderSection("Geography", geo)}
      {provenance && (
        <div className="provenance">
          <div>USER-PROVIDED DATA: {(provenance.user_provided || []).join(", ") || "—"}</div>
          <div>INFERRED CONTEXT: {(provenance.inferred || []).join(", ") || "—"}</div>
          <div>
            EVIDENCE-SUPPORTED INFORMATION:{" "}
            {(provenance.evidence_supported || []).join(", ") || "—"}
          </div>
        </div>
      )}
      {knownVariables && Object.keys(knownVariables).length > 0 && (
        <p className="muted" style={{ marginTop: "0.5rem" }}>
          Tracked variables:{" "}
          {Object.entries(knownVariables)
            .map(([k, v]) => `${k}=${String(v)}`)
            .join("; ")}
        </p>
      )}
    </div>
  );
}

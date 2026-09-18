import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RecommendationCards } from "../components/RecommendationCards";
import { EnvironmentalContext } from "../components/EnvironmentalContext";
import { ReasoningSummary } from "../components/ReasoningSummary";

describe("RecommendationCards", () => {
  it("renders recommendation fields and evidence", () => {
    render(
      <RecommendationCards
        recommendations={[
          {
            title: "Diversify cropping systems",
            action: "Rotate crops",
            scientific_reasoning: "Reduces habitat simplification",
            impacted_metrics: ["habitat diversity"],
            expected_direction: "increase",
            estimated_effect:
              "Quantitative improvement could not be reliably estimated from the retrieved evidence.",
            time_horizon: "medium",
            confidence: 0.72,
            evidence: [
              {
                source_title: "FAO Agroecology",
                organization: "FAO",
                publication_year: 2018,
                url: "https://www.fao.org/agroecology/overview/overview10elements/en/",
                relevant_snippet: "Diversity is a foundational element.",
              },
            ],
          },
        ]}
      />
    );
    expect(screen.getByText("Diversify cropping systems")).toBeInTheDocument();
    expect(screen.getByText(/What to do/i)).toBeInTheDocument();
    expect(screen.getByText(/Why it works/i)).toBeInTheDocument();
    expect(screen.getByText(/Evidence/)).toBeInTheDocument();
  });
});

describe("EnvironmentalContext", () => {
  it("shows soil climate and land sections", () => {
    render(
      <EnvironmentalContext
        context={{
          soil: { organic_carbon: 0.3 },
          climate: { rainfall: "low" },
          land_use: { type: "continuous_monoculture" },
          _provenance: {
            user_provided: ["soil_organic_carbon", "rainfall", "land_use"],
            inferred: [],
            evidence_supported: [],
          },
        }}
      />
    );
    expect(screen.getByText(/Soil/)).toBeInTheDocument();
    expect(screen.getByText(/USER-PROVIDED DATA/)).toBeInTheDocument();
  });
});

describe("ReasoningSummary", () => {
  it("lists variables and relationships", () => {
    render(
      <ReasoningSummary
        variables={["soil organic carbon", "rainfall", "land use"]}
        summary={["Low rainfall with low SOC indicates water-stress context."]}
      />
    );
    expect(screen.getByText(/Variables considered/)).toBeInTheDocument();
    expect(screen.getByText(/water-stress/)).toBeInTheDocument();
  });
});

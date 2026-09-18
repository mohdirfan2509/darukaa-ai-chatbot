import type { DemoScenario } from "../types";

/** All scenarios are Synthetic Demo Data — not real field measurements. */
export const DEMO_SCENARIOS: DemoScenario[] = [
  {
    id: "scenario-1",
    title: "Semi-arid wheat monoculture",
    description:
      "Low soil organic carbon, low rainfall, continuous wheat, biodiversity decline.",
    label: "Synthetic Demo Data",
    prompt:
      "Soil organic carbon is 0.3%, rainfall is low, I grow wheat continuously in a semi-arid region and biodiversity is declining.",
    followUps: ["Why did you recommend that?", "What if rainfall increases?"],
  },
  {
    id: "scenario-2",
    title: "High-rainfall fragmented habitat",
    description:
      "Moderate soil carbon, high temperature, fragmented habitat, moderate species richness.",
    label: "Synthetic Demo Data",
    prompt:
      "I have moderate soil organic carbon, temperature is 34 C, high rainfall, habitat fragmentation is high, and species richness is 28. Biodiversity pressure is rising.",
    followUps: ["What interventions address fragmentation first?"],
  },
  {
    id: "scenario-3",
    title: "Pollution and degradation",
    description:
      "Pollution pressure, degraded land, reduced species richness, fragmentation.",
    label: "Synthetic Demo Data",
    prompt:
      "My land is degraded with elevated pollution, habitat fragmentation is high, and species richness is 9. Biodiversity is declining.",
    followUps: ["How should pollution and restoration be sequenced?"],
  },
  {
    id: "scenario-4",
    title: "Missing information",
    description: "Vague biodiversity concern — system should ask clarifying questions.",
    label: "Synthetic Demo Data",
    prompt: "Biodiversity is declining on my land.",
  },
  {
    id: "scenario-5",
    title: "Multi-turn conversation",
    description: "Start vague, then supply measurements in a follow-up turn.",
    label: "Synthetic Demo Data",
    prompt: "Biodiversity is declining on my land.",
    followUps: [
      "Organic carbon is 0.3%, rainfall is low, and I grow wheat continuously.",
      "What if I introduce agroforestry?",
    ],
  },
];

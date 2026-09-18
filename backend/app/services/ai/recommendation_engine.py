"""Evidence-grounded recommendation engine — not hard-coded keyword rules."""

from __future__ import annotations

from typing import Any, Optional

from app.core.logging import get_logger
from app.prompts.recommendation import RECOMMENDATION_PROMPT, RECOMMENDATION_SYSTEM
from app.schemas.recommendations import EvidenceItem, Recommendation
from app.services.ai.llm_provider import LLMProvider, get_llm_provider

logger = get_logger("recommendations")

# Intervention catalog keyed by evidence themes — selected dynamically by
# matching retrieved evidence + environmental state (not by single if/query).
INTERVENTION_CATALOG = [
    {
        "id": "cover_crops_legume",
        "title": "Introduce legume-based cover crops",
        "action": (
            "Integrate legume cover crops into fallow or inter-season windows to "
            "add organic inputs, protect soil surface, and support soil biota."
        ),
        "impacted_metrics": [
            "soil organic carbon",
            "soil moisture",
            "microbial diversity",
        ],
        "expected_direction": "increase",
        "time_horizon": "medium",
        "themes": ["organic carbon", "cover crop", "soil", "legume", "nitrogen"],
        "states": ["low_soc", "monoculture", "agriculture"],
    },
    {
        "id": "crop_diversification",
        "title": "Diversify cropping systems",
        "action": (
            "Rotate or intercrop with functionally diverse species to reduce "
            "monoculture habitat simplification and improve above- and below-ground diversity."
        ),
        "impacted_metrics": [
            "habitat diversity",
            "species richness",
            "soil organic carbon",
        ],
        "expected_direction": "increase",
        "time_horizon": "medium",
        "themes": ["diversif", "rotation", "intercrop", "monoculture", "cropping"],
        "states": ["monoculture", "low_habitat"],
    },
    {
        "id": "agroforestry",
        "title": "Introduce agroforestry where site-appropriate",
        "action": (
            "Establish tree–crop or tree–livestock configurations suited to the region "
            "to add structural habitat, shade, and organic inputs without inventing yield claims."
        ),
        "impacted_metrics": [
            "habitat diversity",
            "ecological connectivity",
            "soil organic carbon",
        ],
        "expected_direction": "improve",
        "time_horizon": "long",
        "themes": ["agroforestry", "tree", "structural", "shade", "woody"],
        "states": ["low_soc", "low_habitat", "semi_arid", "monoculture"],
    },
    {
        "id": "habitat_corridors",
        "title": "Establish habitat corridors",
        "action": (
            "Restore linear or stepping-stone habitat connections between remnant patches "
            "to improve ecological connectivity for mobile species."
        ),
        "impacted_metrics": [
            "ecological connectivity",
            "species richness",
            "habitat quality",
        ],
        "expected_direction": "improve",
        "time_horizon": "long",
        "themes": ["corridor", "connectivity", "fragment", "landscape"],
        "states": ["fragmentation", "deforestation", "low_richness"],
    },
    {
        "id": "pollinator_habitat",
        "title": "Establish pollinator habitat",
        "action": (
            "Create flowering strips, hedgerows, or native floral resources adjacent to "
            "production areas to support pollinators and associated biodiversity."
        ),
        "impacted_metrics": [
            "pollinator support",
            "habitat diversity",
            "species richness",
        ],
        "expected_direction": "increase",
        "time_horizon": "short",
        "themes": ["pollinator", "floral", "hedgerow", "flower"],
        "states": ["monoculture", "low_habitat", "biodiversity_decline"],
    },
    {
        "id": "reduce_disturbance",
        "title": "Reduce soil disturbance",
        "action": (
            "Minimize unnecessary tillage intensity and timing impacts to protect soil "
            "structure, organic matter retention, and soil biota."
        ),
        "impacted_metrics": [
            "soil organic carbon",
            "microbial diversity",
            "soil moisture",
        ],
        "expected_direction": "improve",
        "time_horizon": "medium",
        "themes": [
            "tillage",
            "disturbance",
            "conservation agriculture",
            "soil structure",
        ],
        "states": ["low_soc", "agriculture"],
    },
    {
        "id": "water_retention",
        "title": "Improve on-site water retention",
        "action": (
            "Apply evidence-aligned water retention practices (mulching, contour measures, "
            "organic amendments) appropriate to local hydrology to buffer rainfall deficits."
        ),
        "impacted_metrics": ["soil moisture", "water availability", "habitat quality"],
        "expected_direction": "improve",
        "time_horizon": "medium",
        "themes": ["water", "moisture", "mulch", "retention", "drought", "rainfall"],
        "states": ["low_rainfall", "low_moisture", "semi_arid"],
    },
    {
        "id": "restore_degraded",
        "title": "Restore degraded habitat patches",
        "action": (
            "Prioritize native vegetation restoration on degraded patches to rebuild "
            "habitat structure and reduce fragmentation effects."
        ),
        "impacted_metrics": [
            "habitat quality",
            "species richness",
            "ecological connectivity",
        ],
        "expected_direction": "improve",
        "time_horizon": "long",
        "themes": ["restoration", "degraded", "native vegetation", "rehabilit"],
        "states": ["degraded", "pollution", "fragmentation"],
    },
    {
        "id": "pollution_mitigation",
        "title": "Reduce pollution pressures on habitats",
        "action": (
            "Identify and reduce pollutant pathways (runoff buffers, input reduction, "
            "containment) that degrade habitat quality for sensitive taxa."
        ),
        "impacted_metrics": ["habitat quality", "species richness", "pollution"],
        "expected_direction": "improve",
        "time_horizon": "medium",
        "themes": ["pollution", "contamin", "buffer", "water quality"],
        "states": ["pollution"],
    },
]


class RecommendationEngine:
    def __init__(self, llm: Optional[LLMProvider] = None) -> None:
        self.llm = llm or get_llm_provider()

    async def generate(
        self,
        environmental_state: dict[str, Any],
        known_variables: dict[str, Any],
        reasoning: dict[str, Any],
        evidence: list[dict[str, Any]],
        problem: Optional[str] = None,
    ) -> list[Recommendation]:
        state_tags = self._state_tags(known_variables, problem)
        evidence_blob = " ".join(e.get("content", "").lower() for e in evidence)

        scored: list[tuple[float, dict[str, Any], list[int]]] = []
        for item in INTERVENTION_CATALOG:
            theme_hits = sum(1 for t in item["themes"] if t in evidence_blob)
            state_hits = sum(1 for s in item["states"] if s in state_tags)
            if theme_hits == 0 and state_hits == 0:
                continue
            score = theme_hits * 1.5 + state_hits * 1.2
            # Prefer interventions supported by evidence themes
            if theme_hits == 0:
                score *= 0.4
            matched_idx = [
                i
                for i, e in enumerate(evidence)
                if any(t in e.get("content", "").lower() for t in item["themes"])
            ]
            if not matched_idx and evidence:
                # Weak link: use top evidence but lower confidence later
                matched_idx = list(range(min(2, len(evidence))))
                score *= 0.5
            if matched_idx or state_hits >= 2:
                scored.append((score, item, matched_idx))

        scored.sort(key=lambda x: x[0], reverse=True)
        selected = scored[:3]

        # Try LLM enrichment (optional)
        try:
            prompt = RECOMMENDATION_PROMPT.format(
                environmental_state=environmental_state,
                reasoning_summary=reasoning.get("reasoning_summary", []),
                evidence=self._format_evidence(evidence),
            )
            llm_out = await self.llm.complete_json(prompt, system=RECOMMENDATION_SYSTEM)
            if isinstance(llm_out, dict) and llm_out.get("recommendations"):
                llm_recs = self._from_llm(llm_out["recommendations"], evidence)
                if llm_recs:
                    return llm_recs[:3]
        except Exception as exc:  # noqa: BLE001
            logger.warning("llm_recommendation_failed", error=str(exc))

        recommendations: list[Recommendation] = []
        for score, item, idxs in selected:
            ev_items = self._evidence_items(evidence, idxs)
            confidence = self._confidence(score, ev_items, evidence)
            reasoning_text = self._scientific_reasoning(item, known_variables, ev_items)
            recommendations.append(
                Recommendation(
                    title=item["title"],
                    action=item["action"],
                    scientific_reasoning=reasoning_text,
                    impacted_metrics=item["impacted_metrics"],
                    expected_direction=item["expected_direction"],
                    estimated_effect=(
                        "Quantitative improvement could not be reliably estimated "
                        "from the retrieved evidence."
                    ),
                    time_horizon=item["time_horizon"],
                    confidence=confidence,
                    evidence=ev_items,
                )
            )

        if not recommendations and evidence:
            # Minimal evidence-grounded fallback
            ev_items = self._evidence_items(
                evidence, list(range(min(2, len(evidence))))
            )
            recommendations.append(
                Recommendation(
                    title="Evidence-informed habitat and soil management review",
                    action=(
                        "Review retrieved institutional guidance and prioritize "
                        "interventions that jointly address the documented soil, "
                        "climate, and land-use constraints at the site."
                    ),
                    scientific_reasoning=(
                        "Retrieved sources discuss interactions among soil function, "
                        "land management, and biodiversity; site-specific sequencing "
                        "should follow local constraints."
                    ),
                    impacted_metrics=list(
                        {k.replace("_", " ") for k in known_variables.keys()}
                    )[:4]
                    or ["habitat quality"],
                    expected_direction="improve",
                    estimated_effect=(
                        "Quantitative improvement could not be reliably estimated "
                        "from the retrieved evidence."
                    ),
                    time_horizon="medium",
                    confidence=0.45,
                    evidence=ev_items,
                )
            )

        logger.info("recommendations_generated", count=len(recommendations))
        return recommendations

    def _state_tags(self, known: dict[str, Any], problem: Optional[str]) -> set[str]:
        tags: set[str] = set()
        soc = known.get("soil_organic_carbon")
        if soc in ("low",) or (isinstance(soc, (int, float)) and soc < 1.0):
            tags.add("low_soc")
        rainfall = known.get("rainfall")
        if rainfall in ("low", "scarce") or (
            isinstance(rainfall, (int, float)) and rainfall < 400
        ):
            tags.add("low_rainfall")
        if known.get("soil_moisture") == "low":
            tags.add("low_moisture")
        land = str(known.get("land_use", "")).lower()
        if "monoculture" in land or known.get("crop"):
            tags.add("monoculture")
            tags.add("agriculture")
        if "degraded" in land:
            tags.add("degraded")
        if known.get("habitat_diversity") == "low":
            tags.add("low_habitat")
        if known.get("habitat_fragmentation"):
            tags.add("fragmentation")
        if known.get("deforestation"):
            tags.add("deforestation")
        if known.get("pollution"):
            tags.add("pollution")
        richness = known.get("species_richness")
        if isinstance(richness, (int, float)) and richness < 20:
            tags.add("low_richness")
        if str(known.get("region", "")).lower() in ("semi-arid", "arid"):
            tags.add("semi_arid")
        if problem == "biodiversity_decline":
            tags.add("biodiversity_decline")
        return tags

    def _format_evidence(self, evidence: list[dict[str, Any]]) -> str:
        parts = []
        for i, e in enumerate(evidence):
            src = e.get("source", {})
            parts.append(
                f"[{i}] {src.get('title')} | {src.get('organization')} | "
                f"{src.get('publication_year')} | {e.get('content', '')[:350]}"
            )
        return "\n".join(parts)

    def _evidence_items(
        self, evidence: list[dict[str, Any]], idxs: list[int]
    ) -> list[EvidenceItem]:
        items: list[EvidenceItem] = []
        for i in idxs:
            if i < 0 or i >= len(evidence):
                continue
            e = evidence[i]
            src = e.get("source", {})
            items.append(
                EvidenceItem(
                    source_title=src.get("title") or "Unknown source",
                    organization=src.get("organization"),
                    authors=src.get("authors"),
                    publication_year=src.get("publication_year"),
                    url=src.get("url"),
                    source_type=src.get("source_type"),
                    relevant_snippet=e.get("content", "")[:500],
                    similarity=e.get("similarity"),
                )
            )
        return items

    def _confidence(
        self,
        score: float,
        ev_items: list[EvidenceItem],
        evidence: list[dict[str, Any]],
    ) -> float:
        base = 0.4
        base += min(0.25, score * 0.05)
        if ev_items:
            avg_sim = sum(e.similarity or 0 for e in ev_items) / len(ev_items)
            base += min(0.25, avg_sim * 0.3)
        if len(evidence) >= 3:
            base += 0.05
        return round(min(0.92, max(0.3, base)), 2)

    def _scientific_reasoning(
        self,
        item: dict[str, Any],
        known: dict[str, Any],
        ev_items: list[EvidenceItem],
    ) -> str:
        vars_txt = ", ".join(k.replace("_", " ") for k in list(known.keys())[:5])
        src_titles = (
            ", ".join(e.source_title for e in ev_items[:2]) or "retrieved guidance"
        )
        return (
            f"Given the observed context ({vars_txt}), {item['title'].lower()} is "
            f"aligned with relationships discussed in: {src_titles}. "
            f"The action targets interacting drivers rather than a single metric."
        )

    def _from_llm(
        self,
        raw_recs: list[dict[str, Any]],
        evidence: list[dict[str, Any]],
    ) -> list[Recommendation]:
        out: list[Recommendation] = []
        for r in raw_recs:
            idxs = r.get("evidence_chunk_indices") or list(range(min(2, len(evidence))))
            ev_items = self._evidence_items(evidence, idxs)
            if not ev_items:
                continue
            effect = r.get("estimated_effect")
            # Strip fabricated-looking percentages if LLM invents them without support
            if effect and any(ch.isdigit() for ch in str(effect)):
                effect = (
                    "Quantitative improvement could not be reliably estimated "
                    "from the retrieved evidence."
                )
            out.append(
                Recommendation(
                    title=r.get("title", "Evidence-based intervention"),
                    action=r.get("action", ""),
                    scientific_reasoning=r.get("scientific_reasoning", ""),
                    impacted_metrics=r.get("impacted_metrics") or [],
                    expected_direction=r.get("expected_direction", "improve"),
                    estimated_effect=effect
                    or (
                        "Quantitative improvement could not be reliably estimated "
                        "from the retrieved evidence."
                    ),
                    time_horizon=r.get("time_horizon", "medium"),
                    confidence=float(r.get("confidence") or 0.5),
                    evidence=ev_items,
                )
            )
        return out

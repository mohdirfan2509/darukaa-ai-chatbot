"""Multi-metric environmental reasoning engine."""

from __future__ import annotations

from typing import Any, Optional

from app.core.logging import get_logger
from app.prompts.reasoning import REASONING_PROMPT, REASONING_SYSTEM
from app.services.ai.context_builder import variables_considered
from app.services.ai.llm_provider import LLMProvider, get_llm_provider

logger = get_logger("reasoning")


class ReasoningEngine:
    def __init__(self, llm: Optional[LLMProvider] = None) -> None:
        self.llm = llm or get_llm_provider()

    async def reason(
        self,
        environmental_state: dict[str, Any],
        known_variables: dict[str, Any],
        evidence: list[dict[str, Any]],
    ) -> dict[str, Any]:
        evidence_text = self._format_evidence(evidence)
        relationships = self._rule_based_relationships(known_variables, evidence)

        try:
            prompt = REASONING_PROMPT.format(
                environmental_state=environmental_state,
                evidence=evidence_text,
                known_variables=known_variables,
            )
            llm_out = await self.llm.complete_json(prompt, system=REASONING_SYSTEM)
            if isinstance(llm_out, dict) and llm_out.get("relationships"):
                # Prefer LLM relationships only if they don't invent sources
                for rel in llm_out["relationships"]:
                    if rel and rel not in relationships:
                        relationships.append(rel)
                if llm_out.get("assumptions"):
                    assumptions = list(llm_out["assumptions"])
                else:
                    assumptions = self._default_assumptions(known_variables)
                combined = llm_out.get(
                    "combined_assessment"
                ) or self._combined_assessment(known_variables, relationships)
            else:
                assumptions = self._default_assumptions(known_variables)
                combined = self._combined_assessment(known_variables, relationships)
        except Exception as exc:  # noqa: BLE001
            logger.warning("llm_reasoning_failed", error=str(exc))
            assumptions = self._default_assumptions(known_variables)
            combined = self._combined_assessment(known_variables, relationships)

        vars_used = variables_considered(environmental_state)
        if len(vars_used) < 3 and len(known_variables) >= 3:
            vars_used = [k.replace("_", " ") for k in list(known_variables.keys())[:6]]

        result = {
            "relationships": relationships,
            "combined_assessment": combined,
            "variables_used": vars_used,
            "assumptions": assumptions,
            "uncertainty_notes": self._uncertainty_notes(evidence, known_variables),
            "reasoning_summary": relationships[:6] + ([combined] if combined else []),
        }
        logger.info(
            "reasoning_complete",
            variables=vars_used,
            relationship_count=len(relationships),
        )
        return result

    def _format_evidence(self, evidence: list[dict[str, Any]]) -> str:
        parts = []
        for i, e in enumerate(evidence):
            src = e.get("source", {})
            parts.append(
                f"[{i}] {src.get('title')} ({src.get('organization')}, "
                f"{src.get('publication_year')}): {e.get('content', '')[:400]}"
            )
        return "\n".join(parts) if parts else "No evidence retrieved."

    def _evidence_mentions(
        self, evidence: list[dict[str, Any]], *keywords: str
    ) -> bool:
        blob = " ".join(e.get("content", "").lower() for e in evidence)
        return any(k.lower() in blob for k in keywords)

    def _rule_based_relationships(
        self,
        known: dict[str, Any],
        evidence: list[dict[str, Any]],
    ) -> list[str]:
        rels: list[str] = []
        rainfall = known.get("rainfall")
        moisture = known.get("soil_moisture")
        soc = known.get("soil_organic_carbon")
        land = str(known.get("land_use", "")).lower()
        habitat = str(known.get("habitat_diversity", "")).lower()
        richness = known.get("species_richness")
        pollution = known.get("pollution")
        frag = known.get("habitat_fragmentation")
        deforestation = known.get("deforestation")
        temp = known.get("temperature")

        rainfall_low = rainfall in ("low", "scarce") or (
            isinstance(rainfall, (int, float)) and rainfall < 400
        )
        soc_low = soc in ("low",) or (isinstance(soc, (int, float)) and soc < 1.0)

        if rainfall_low and (moisture == "low" or moisture is None):
            if self._evidence_mentions(
                evidence, "water", "rainfall", "drought", "moisture"
            ):
                rels.append(
                    "Low rainfall combined with limited soil moisture indicates a "
                    "water-stress context that constrains ecological recovery "
                    "(supported by retrieved water/climate guidance)."
                )

        if "monoculture" in land or land == "intensive_agriculture":
            if habitat == "low" or habitat == "" or richness is not None:
                if self._evidence_mentions(
                    evidence, "monoculture", "habitat", "diversity", "cropping"
                ):
                    rels.append(
                        "Simplified/monoculture land use is associated with reduced "
                        "habitat diversity and biodiversity pressure in the retrieved "
                        "land-use literature."
                    )

        if soc_low:
            if self._evidence_mentions(
                evidence, "organic carbon", "soil carbon", "soil organic"
            ):
                rels.append(
                    "Low soil organic carbon is associated with reduced soil ecological "
                    "function and weaker support for below-ground biodiversity "
                    "(supported by retrieved soil health guidance)."
                )

        if rainfall_low and soc_low and ("monoculture" in land or known.get("crop")):
            rels.append(
                "Combined low soil organic carbon, water limitation, and simplified "
                "cropping create multi-factor pressure on habitat quality and "
                "biodiversity recovery potential."
            )

        if frag or deforestation:
            if self._evidence_mentions(
                evidence, "fragment", "connectivity", "corridor", "deforest"
            ):
                rels.append(
                    "Habitat fragmentation and/or deforestation reduce ecological "
                    "connectivity, limiting species movement and habitat quality "
                    "(supported by retrieved connectivity guidance)."
                )

        if pollution:
            if self._evidence_mentions(evidence, "pollution", "contamin", "quality"):
                rels.append(
                    "Pollution pressure is linked to reduced habitat quality and "
                    "species persistence in the retrieved evidence."
                )

        if isinstance(temp, (int, float)) and temp >= 30 and rainfall_low:
            if self._evidence_mentions(
                evidence, "temperature", "heat", "drought", "water"
            ):
                rels.append(
                    "Elevated temperature with low rainfall intensifies water-stress "
                    "conditions relevant to vegetation and soil biota recovery."
                )

        if habitat == "low" and richness is not None and float(richness) < 20:
            rels.append(
                "Low habitat diversity together with limited species richness "
                "indicates biodiversity pressure requiring habitat-complexity interventions."
            )

        if not rels and evidence:
            rels.append(
                "Retrieved evidence provides general environmental guidance relevant "
                "to the stated variables; relationships are interpreted cautiously."
            )
        return rels

    def _combined_assessment(
        self, known: dict[str, Any], relationships: list[str]
    ) -> str:
        vars_list = ", ".join(k.replace("_", " ") for k in known.keys())
        if len(relationships) >= 2:
            return (
                f"These combined conditions ({vars_list}) suggest interacting soil, "
                f"climate, and land-use pressures on biodiversity. Interventions should "
                f"address multiple drivers rather than a single variable."
            )
        return (
            f"Based on available variables ({vars_list}), environmental pressure is "
            f"indicated; additional evidence-backed multi-variable linkages may emerge "
            f"as more measurements are provided."
        )

    def _default_assumptions(self, known: dict[str, Any]) -> list[str]:
        assumptions = [
            "User-provided values are treated as approximate site observations.",
            "Recommendations are general guidance, not site-specific engineering designs.",
        ]
        if "rainfall" in known and isinstance(known["rainfall"], str):
            assumptions.append(
                "Qualitative rainfall labels (e.g. low/high) are interpreted categorically."
            )
        return assumptions

    def _uncertainty_notes(
        self, evidence: list[dict[str, Any]], known: dict[str, Any]
    ) -> list[str]:
        notes = []
        if len(evidence) < 2:
            notes.append(
                "Limited retrieved evidence reduces confidence in recommendations."
            )
        if len(known) < 3:
            notes.append(
                "Fewer than three environmental variables limit multi-metric reasoning depth."
            )
        return notes

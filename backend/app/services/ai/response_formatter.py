"""Format final structured AI response for API/frontend."""

from __future__ import annotations

from typing import Any

from app.schemas.recommendations import (
    EnvironmentalAssessment,
    RetrievalMeta,
    StructuredAIResponse,
)
from app.services.ai.context_builder import variables_considered


class ResponseFormatter:
    def format(
        self,
        *,
        answer: str,
        environmental_state: dict[str, Any],
        reasoning: dict[str, Any],
        recommendations: list[Any],
        missing_information: list[str],
        assumptions: list[str],
        evidence: list[dict[str, Any]],
        needs_clarification: bool = False,
        clarification_questions: list[str] | None = None,
    ) -> StructuredAIResponse:
        vars_considered = reasoning.get("variables_used") or variables_considered(
            environmental_state
        )
        source_ids = {
            (e.get("source") or {}).get("id")
            for e in evidence
            if (e.get("source") or {}).get("id")
        }

        raw_summary = (
            reasoning.get("reasoning_summary") or reasoning.get("relationships") or []
        )
        reasoning_summary = self._as_string_list(raw_summary)
        assumptions_clean = self._as_string_list(assumptions)
        missing_clean = self._as_string_list(missing_information)
        vars_clean = self._as_string_list(vars_considered)

        return StructuredAIResponse(
            answer=answer,
            environmental_assessment=EnvironmentalAssessment(
                summary=str(
                    reasoning.get("combined_assessment")
                    or "Environmental assessment based on available variables and retrieved evidence."
                ),
                variables_considered=vars_clean,
            ),
            reasoning_summary=reasoning_summary,
            recommendations=recommendations,
            missing_information=missing_clean,
            assumptions=assumptions_clean,
            retrieval=RetrievalMeta(
                sources_used=len(source_ids),
                chunks_used=len(evidence),
            ),
            environmental_context=environmental_state,
            needs_clarification=needs_clarification,
            clarification_questions=clarification_questions or [],
        )

    @staticmethod
    def _as_string_list(items: Any) -> list[str]:
        if not items:
            return []
        if isinstance(items, str):
            return [items]
        out: list[str] = []
        for item in items:
            if isinstance(item, str):
                text = item.strip()
                if text:
                    out.append(text)
            elif isinstance(item, dict):
                # LLMs sometimes return objects instead of plain strings
                for key in ("summary", "relationship", "text", "description"):
                    if isinstance(item.get(key), str) and item[key].strip():
                        out.append(item[key].strip())
                        break
                else:
                    # compact fallback without dumping huge payloads
                    parts = [
                        f"{k}={v}"
                        for k, v in item.items()
                        if isinstance(v, (str, int, float))
                    ]
                    if parts:
                        out.append("; ".join(parts[:6]))
            elif item is not None:
                out.append(str(item))
        return out

    def clarification_answer(
        self,
        missing: list[str],
        known: dict[str, Any],
        problem: str | None,
    ) -> tuple[str, list[str]]:
        label_map = {
            "soil_organic_carbon": "Soil organic carbon (e.g. %)",
            "rainfall": "Rainfall pattern (low / moderate / high, or mm)",
            "land_use": "Current land-use type",
            "habitat_diversity": "Habitat diversity (low / moderate / high)",
            "soil_ph": "Soil pH",
            "soil_moisture": "Soil moisture",
            "species_richness": "Species richness estimate",
            "temperature": "Typical temperature",
            "pollution": "Pollution pressures, if any",
            "deforestation": "Recent deforestation pressure",
            "habitat_fragmentation": "Habitat fragmentation level",
        }
        questions = [label_map.get(m, m.replace("_", " ")) for m in missing[:3]]
        known_txt = (
            ", ".join(f"{k.replace('_', ' ')}={v}" for k, v in known.items())
            if known
            else "none yet"
        )
        problem_txt = (problem or "environmental concern").replace("_", " ")
        answer = (
            f"I can help assess this {problem_txt}. "
            f"Currently known: {known_txt}. "
            f"To narrow down likely drivers, please provide:\n"
            + "\n".join(f"{i + 1}. {q}" for i, q in enumerate(questions))
        )
        return answer, questions

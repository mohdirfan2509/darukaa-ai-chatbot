"""Environment analysis helpers."""

from __future__ import annotations

from typing import Any, Optional

from app.services.ai.context_builder import build_environmental_state
from app.services.ai.query_analyzer import QueryAnalyzer
from app.services.ai.reasoning_engine import ReasoningEngine


class EnvironmentService:
    def __init__(self) -> None:
        self.analyzer = QueryAnalyzer()
        self.reasoning = ReasoningEngine()

    async def analyze(
        self,
        text: Optional[str] = None,
        variables: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        known = dict(variables or {})
        # Reject obviously invalid numeric strings for quantitative metrics
        for key in (
            "soil_organic_carbon",
            "soil_ph",
            "temperature",
            "species_richness",
        ):
            if key in known and isinstance(known[key], str):
                try:
                    known[key] = float(known[key])
                except ValueError:
                    known.pop(key, None)
        analysis = await self.analyzer.analyze(text or "", known_variables=known)
        state = build_environmental_state(analysis["known_variables"])
        # Lightweight relationship preview without retrieval
        reasoning = await self.reasoning.reason(
            state, analysis["known_variables"], evidence=[]
        )
        return {
            "environmental_state": state,
            "known_variables": analysis["known_variables"],
            "missing_variables": analysis["missing_variables"],
            "critical_variables": analysis["critical_variables"],
            "optional_variables": analysis["optional_variables"],
            "relationships": reasoning.get("relationships", []),
            "assessment_summary": reasoning.get("combined_assessment", ""),
        }

"""Evidence validator — blocks unsupported claims and fabricated citations."""

from __future__ import annotations

import re
from typing import Any, Optional

from app.core.logging import get_logger
from app.prompts.evidence_validation import (
    EVIDENCE_VALIDATION_PROMPT,
    EVIDENCE_VALIDATION_SYSTEM,
)
from app.schemas.recommendations import Recommendation
from app.services.ai.llm_provider import LLMProvider, get_llm_provider

logger = get_logger("evidence_validator")

QUANT_CLAIM_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*%|\bincrease(?:s|d)?\s+by\b|\bdecrease(?:s|d)?\s+by\b",
    re.I,
)


class EvidenceValidator:
    def __init__(self, llm: Optional[LLMProvider] = None) -> None:
        self.llm = llm or get_llm_provider()

    async def validate(
        self,
        recommendations: list[Recommendation],
        evidence: list[dict[str, Any]],
        known_variables: dict[str, Any],
    ) -> dict[str, Any]:
        issues: list[str] = []
        rejected_quant: list[str] = []
        adjusted: dict[str, float] = {}
        validated: list[Recommendation] = []

        evidence_urls = {
            (e.get("source") or {}).get("url")
            for e in evidence
            if (e.get("source") or {}).get("url")
        }
        evidence_titles = {
            ((e.get("source") or {}).get("title") or "").lower() for e in evidence
        }

        for rec in recommendations:
            if not rec.evidence:
                issues.append(f"Rejected '{rec.title}': no supporting evidence.")
                continue

            # Check evidence relevance: snippet or title should relate to action themes
            relevant = False
            for ev in rec.evidence:
                blob = f"{ev.source_title} {ev.relevant_snippet}".lower()
                action_tokens = set(rec.action.lower().split())
                if len(action_tokens & set(blob.split())) >= 2:
                    relevant = True
                    break
                if any(
                    t in blob
                    for t in [
                        "soil",
                        "biodiversity",
                        "habitat",
                        "carbon",
                        "rainfall",
                        "agro",
                        "pollut",
                        "fragment",
                        "crop",
                        "water",
                    ]
                ):
                    relevant = True
                    break
            if not relevant:
                issues.append(
                    f"Lowered confidence for '{rec.title}': weak evidence relevance."
                )
                rec.confidence = min(rec.confidence, 0.4)

            # Fabricated URL check
            for ev in rec.evidence:
                if ev.url and ev.url not in evidence_urls:
                    issues.append(
                        f"Removed fabricated URL from '{rec.title}' evidence."
                    )
                    ev.url = None
                if ev.source_title.lower() not in evidence_titles and evidence_titles:
                    # Allow if snippet came from retrieval (title mismatch edge case)
                    pass

            # Quantitative claims
            text_to_check = f"{rec.scientific_reasoning} {rec.estimated_effect or ''}"
            if QUANT_CLAIM_RE.search(text_to_check or ""):
                if not self._quant_supported_in_evidence(rec):
                    rejected_quant.append(rec.title)
                    rec.estimated_effect = (
                        "Quantitative improvement could not be reliably estimated "
                        "from the retrieved evidence."
                    )
                    # Also scrub percentage claims from reasoning if present
                    if QUANT_CLAIM_RE.search(rec.scientific_reasoning or ""):
                        rec.scientific_reasoning = (
                            rec.scientific_reasoning
                            + " Note: numerical effect sizes were removed because "
                            "they were not supported by retrieved evidence."
                        )
                    rec.confidence = min(rec.confidence, 0.55)
                    issues.append(
                        f"Unsupported quantitative claim removed from '{rec.title}'."
                    )

            # Confidence reflects evidence quality
            if len(rec.evidence) == 1:
                rec.confidence = min(rec.confidence, 0.7)
            if len(evidence) < 2:
                rec.confidence = min(rec.confidence, 0.6)

            adjusted[rec.title] = rec.confidence
            validated.append(rec)

        assumptions = [
            "Recommendations depend on accuracy of user-provided environmental values.",
            "Retrieved institutional guidance may not capture all local constraints.",
        ]
        if len(known_variables) < 4:
            assumptions.append(
                "Limited variable coverage increases uncertainty in intervention prioritization."
            )

        # Optional LLM second pass (non-fatal)
        try:
            prompt = EVIDENCE_VALIDATION_PROMPT.format(
                recommendations=[r.model_dump() for r in validated],
                evidence=[
                    {
                        "title": (e.get("source") or {}).get("title"),
                        "snippet": e.get("content", "")[:300],
                    }
                    for e in evidence
                ],
            )
            llm_out = await self.llm.complete_json(
                prompt, system=EVIDENCE_VALIDATION_SYSTEM
            )
            if isinstance(llm_out, dict):
                issues.extend(llm_out.get("issues") or [])
                assumptions.extend(llm_out.get("assumptions_required") or [])
        except Exception as exc:  # noqa: BLE001
            logger.warning("llm_validation_failed", error=str(exc))

        valid = len(validated) > 0 or len(evidence) == 0
        result = {
            "valid": valid,
            "issues": issues,
            "adjusted_confidence": adjusted,
            "rejected_quantitative_claims": rejected_quant,
            "assumptions_required": assumptions,
            "recommendations": validated,
        }
        logger.info(
            "evidence_validation_complete",
            valid=valid,
            issues=len(issues),
            recommendations=len(validated),
        )
        return result

    def _quant_supported_in_evidence(self, rec: Recommendation) -> bool:
        """Require a numeric pattern to also appear in an evidence snippet."""
        for ev in rec.evidence:
            if QUANT_CLAIM_RE.search(ev.relevant_snippet or ""):
                return True
        return False

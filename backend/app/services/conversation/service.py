"""End-to-end chat pipeline orchestration."""

from __future__ import annotations

import time
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.conversation import (
    Conversation,
    ConversationContext,
    ConversationMessage,
)
from app.services.ai.context_builder import build_environmental_state
from app.services.ai.evidence_validator import EvidenceValidator
from app.services.ai.query_analyzer import QueryAnalyzer
from app.services.ai.reasoning_engine import ReasoningEngine
from app.services.ai.recommendation_engine import RecommendationEngine
from app.services.ai.response_formatter import ResponseFormatter
from app.services.ai.retrieval import RetrievalService

logger = get_logger("chat_pipeline")


class ChatPipeline:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.analyzer = QueryAnalyzer()
        self.retrieval = RetrievalService(db)
        self.reasoning = ReasoningEngine()
        self.recommendations = RecommendationEngine()
        self.validator = EvidenceValidator()
        self.formatter = ResponseFormatter()

    async def handle_message(
        self,
        conversation: Conversation,
        content: str,
        structured_input: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        started = time.perf_counter()
        ctx = conversation.context
        if ctx is None:
            ctx = ConversationContext(
                conversation_id=conversation.id,
                known_variables={},
                missing_variables=[],
                environmental_state={},
                assumptions=[],
            )
            self.db.add(ctx)
            self.db.flush()

        known = dict(ctx.known_variables or {})
        if structured_input:
            for k, v in structured_input.items():
                if v is not None:
                    known[k] = v

        analysis = await self.analyzer.analyze(content, known_variables=known)
        known = analysis["known_variables"]
        missing = analysis["missing_variables"]
        needs_clarification = analysis["needs_clarification"]
        intent = self._detect_followup_intent(content)

        environmental_state = build_environmental_state(known)

        # Off-topic / non-environmental questions should not force soil clarification.
        if intent == "out_of_domain" and not self._has_env_signal(content, known):
            answer = (
                "I am an environmental biodiversity intelligence assistant. "
                "I can help with soil, climate, land use, habitat, and biodiversity "
                "questions, but not unrelated topics. Please describe your site "
                "conditions or environmental concern."
            )
            response = self.formatter.format(
                answer=answer,
                environmental_state=environmental_state,
                reasoning={
                    "combined_assessment": "Query is outside the environmental scope of this system.",
                    "reasoning_summary": [
                        "No environmental variables were provided for biodiversity assessment."
                    ],
                    "variables_used": list(known.keys()),
                    "assumptions": [],
                },
                recommendations=[],
                missing_information=[],
                assumptions=[
                    "Off-topic requests are declined rather than forced into environmental clarification."
                ],
                evidence=[],
                needs_clarification=False,
                clarification_questions=[],
            )
            self._persist_turn(
                conversation,
                ctx,
                content,
                known,
                missing,
                environmental_state,
                response.model_dump(),
            )
            return response.model_dump()

        # Clarification path
        if needs_clarification:
            answer, questions = self.formatter.clarification_answer(
                missing, known, analysis.get("problem")
            )
            response = self.formatter.format(
                answer=answer,
                environmental_state=environmental_state,
                reasoning={
                    "combined_assessment": (
                        "Insufficient multi-variable context for evidence-grounded "
                        "recommendations yet."
                    ),
                    "reasoning_summary": [
                        "Critical environmental variables are missing for reliable multi-metric reasoning."
                    ],
                    "variables_used": list(known.keys()),
                    "assumptions": [],
                },
                recommendations=[],
                missing_information=missing,
                assumptions=[
                    "Clarifying questions prioritize variables that materially improve the next reasoning step."
                ],
                evidence=[],
                needs_clarification=True,
                clarification_questions=questions,
            )
            self._persist_turn(
                conversation,
                ctx,
                content,
                known,
                missing,
                environmental_state,
                response.model_dump(),
            )
            latency_ms = int((time.perf_counter() - started) * 1000)
            logger.info(
                "chat_turn_clarification",
                conversation_id=str(conversation.id),
                missing=missing,
                latency_ms=latency_ms,
            )
            return response.model_dump()

        # Retrieval
        retrieval_query = self.retrieval.build_retrieval_query(analysis)
        evidence = await self.retrieval.search(retrieval_query, top_k=6)

        # Reasoning
        reasoning = await self.reasoning.reason(environmental_state, known, evidence)

        # Recommendations
        recs = await self.recommendations.generate(
            environmental_state,
            known,
            reasoning,
            evidence,
            problem=analysis.get("problem"),
        )

        # Evidence validation
        validation = await self.validator.validate(recs, evidence, known)
        validated_recs = validation["recommendations"]
        assumptions = list(
            dict.fromkeys(
                (reasoning.get("assumptions") or [])
                + (validation.get("assumptions_required") or [])
            )
        )

        if not validated_recs and evidence:
            answer = (
                "Retrieved knowledge was insufficient to validate specific interventions "
                "with acceptable confidence. Please refine site variables or consult "
                "the retrieved sources listed in the developer retrieval view."
            )
        elif not evidence:
            answer = (
                "No relevant knowledge chunks were retrieved from the knowledge base. "
                "I will not invent scientific claims. Please ensure knowledge has been "
                "ingested, or provide more environmental detail."
            )
        else:
            titles = "; ".join(r.title for r in validated_recs)
            if intent == "why" and validated_recs:
                answer = (
                    "Based on the current environmental context "
                    f"({', '.join(k.replace('_', ' ') for k in known.keys())}), "
                    "these recommendations help because they target interacting drivers "
                    "supported by retrieved evidence:\n"
                    + "\n".join(
                        f"- {r.title}: {r.scientific_reasoning}" for r in validated_recs
                    )
                )
            elif intent == "metrics" and validated_recs:
                metrics = sorted(
                    {m for r in validated_recs for m in (r.impacted_metrics or [])}
                )
                answer = (
                    "Given the site context, monitor these environmental metrics over time: "
                    + (
                        ", ".join(metrics)
                        if metrics
                        else "soil organic carbon, habitat diversity, species richness"
                    )
                    + ". Track them alongside the recommended interventions to evaluate ecological response; "
                    "quantitative effect sizes are not asserted beyond retrieved evidence."
                )
            elif intent == "counterfactual":
                answer = (
                    f"{reasoning.get('combined_assessment', '')} "
                    f"Updated context after your change: rainfall={known.get('rainfall')}. "
                    f"Recommended actions under the revised conditions: {titles}. "
                    "Each recommendation below remains grounded in retrieved institutional evidence."
                )
            else:
                answer = (
                    f"{reasoning.get('combined_assessment', '')} "
                    f"Recommended actions: {titles}. "
                    f"Each recommendation below is grounded in retrieved institutional evidence."
                )

        response = self.formatter.format(
            answer=answer.strip(),
            environmental_state=environmental_state,
            reasoning=reasoning,
            recommendations=validated_recs,
            missing_information=missing,
            assumptions=assumptions,
            evidence=evidence,
            needs_clarification=False,
            clarification_questions=[],
        )

        payload = response.model_dump()
        self._persist_turn(
            conversation, ctx, content, known, missing, environmental_state, payload
        )

        latency_ms = int((time.perf_counter() - started) * 1000)
        logger.info(
            "chat_turn_complete",
            conversation_id=str(conversation.id),
            query=content[:200],
            detected_variables=list(known.keys()),
            retrieval_count=len(evidence),
            source_ids=[(e.get("source") or {}).get("id") for e in evidence],
            latency_ms=latency_ms,
            validation_valid=validation.get("valid"),
        )
        return payload

    def _persist_turn(
        self,
        conversation: Conversation,
        ctx: ConversationContext,
        user_content: str,
        known: dict[str, Any],
        missing: list[str],
        environmental_state: dict[str, Any],
        assistant_payload: dict[str, Any],
    ) -> None:
        user_msg = ConversationMessage(
            conversation_id=conversation.id,
            role="user",
            content=user_content,
        )
        assistant_msg = ConversationMessage(
            conversation_id=conversation.id,
            role="assistant",
            content=assistant_payload.get("answer", ""),
            structured_payload=assistant_payload,
        )
        self.db.add(user_msg)
        self.db.add(assistant_msg)

        ctx.known_variables = known
        ctx.missing_variables = missing
        ctx.environmental_state = environmental_state
        ctx.assumptions = assistant_payload.get("assumptions") or []

        if not conversation.title:
            conversation.title = user_content[:80]

        self.db.commit()
        self.db.refresh(conversation)

    def _detect_followup_intent(self, content: str) -> str:
        m = content.lower().strip()
        if any(
            x in m
            for x in [
                "programming language",
                "javascript",
                "python vs",
                "write a poem",
                "who won the",
                "movie recommendation",
                "stock tip",
            ]
        ):
            return "out_of_domain"
        if any(
            x in m
            for x in [
                "why would",
                "why did",
                "why does",
                "why that help",
                "explain why",
            ]
        ):
            return "why"
        if any(
            x in m
            for x in [
                "which environmental metrics",
                "what metrics",
                "metrics should i monitor",
                "what should i monitor",
                "impacted metrics",
            ]
        ):
            return "metrics"
        if any(
            x in m
            for x in [
                "what if rainfall",
                "if rainfall increases",
                "if rainfall decreases",
                "suppose rainfall",
            ]
        ):
            return "counterfactual"
        return "general"

    def _has_env_signal(self, content: str, known: dict[str, Any]) -> bool:
        if known:
            return True
        m = content.lower()
        keywords = [
            "soil",
            "carbon",
            "rainfall",
            "biodivers",
            "habitat",
            "crop",
            "monoculture",
            "deforest",
            "pollution",
            "temperature",
            "species",
            "land use",
            "agro",
        ]
        return any(k in m for k in keywords)

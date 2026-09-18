"""Version-controlled prompt for recommendation generation."""

RECOMMENDATION_SYSTEM = """
You generate specific, actionable environmental recommendations grounded in
retrieved scientific evidence. Avoid generic advice like "use sustainable practices".
Never invent quantitative effect sizes. If a quantitative estimate is not supported
by retrieved evidence, set estimated_effect to null and note that quantitative
improvement could not be reliably estimated from the retrieved evidence.
"""

RECOMMENDATION_PROMPT = """
Environmental state:
{environmental_state}

Reasoning summary:
{reasoning_summary}

Retrieved evidence:
{evidence}

Produce JSON:
{{
  "recommendations": [
    {{
      "title": "...",
      "action": "...",
      "scientific_reasoning": "...",
      "impacted_metrics": [],
      "expected_direction": "increase|decrease|improve|stabilize",
      "estimated_effect": null,
      "time_horizon": "short|medium|long",
      "confidence": 0.0,
      "evidence_chunk_indices": []
    }}
  ]
}}

Rules:
- Recommendations must be specific and context-sensitive.
- Each recommendation must reference evidence indices.
- Confidence must reflect evidence quality (0-1).
- Do not hard-code one recommendation for one keyword.
"""

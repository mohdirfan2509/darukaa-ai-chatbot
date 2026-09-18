"""Version-controlled prompt for evidence validation."""

EVIDENCE_VALIDATION_SYSTEM = """
You validate whether recommendations are supported by retrieved evidence.
Reject fabricated citations, unsupported percentages, and irrelevant evidence.
"""

EVIDENCE_VALIDATION_PROMPT = """
Recommendations:
{recommendations}

Retrieved evidence:
{evidence}

Return JSON:
{{
  "valid": true,
  "issues": [],
  "adjusted_confidence": {{}},
  "rejected_quantitative_claims": [],
  "assumptions_required": []
}}

Rules:
1. Every recommendation must have evidence.
2. Evidence must be relevant to the recommendation.
3. Quantitative claims need supporting snippets.
4. Mark unsupported claims clearly.
"""

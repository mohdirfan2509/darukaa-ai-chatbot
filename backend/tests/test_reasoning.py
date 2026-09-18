import pytest

from app.services.ai.context_builder import (
    build_environmental_state,
    variables_considered,
)
from app.services.ai.reasoning_engine import ReasoningEngine


@pytest.mark.asyncio
async def test_multi_metric_reasoning_connects_variables():
    known = {
        "soil_organic_carbon": 0.3,
        "rainfall": "low",
        "land_use": "continuous_monoculture",
        "habitat_diversity": "low",
    }
    state = build_environmental_state(known)
    evidence = [
        {
            "content": (
                "Low soil organic carbon is associated with reduced soil ecological "
                "function. Low rainfall and moisture create water-stress. Monoculture "
                "reduces habitat diversity and biodiversity."
            ),
            "source": {
                "title": "FAO Soil Organic Carbon",
                "organization": "FAO",
                "publication_year": 2017,
            },
            "similarity": 0.8,
        }
    ]
    engine = ReasoningEngine()
    result = await engine.reason(state, known, evidence)
    assert len(result["variables_used"]) >= 3
    assert len(result["relationships"]) >= 2
    assert any(
        "organic carbon" in r.lower()
        or "monoculture" in r.lower()
        or "rainfall" in r.lower()
        or "combined" in r.lower()
        for r in result["relationships"]
    )


def test_environmental_state_structure():
    state = build_environmental_state(
        {
            "soil_organic_carbon": 0.3,
            "rainfall": "low",
            "land_use": "wheat_monoculture",
            "species_richness": 12,
        }
    )
    assert "soil" in state
    assert "climate" in state
    assert "land_use" in state
    assert "biodiversity" in state
    assert len(variables_considered(state)) >= 3

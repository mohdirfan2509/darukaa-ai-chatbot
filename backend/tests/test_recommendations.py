import pytest

from app.schemas.recommendations import EvidenceItem, Recommendation
from app.services.ai.evidence_validator import EvidenceValidator
from app.services.ai.recommendation_engine import RecommendationEngine


@pytest.mark.asyncio
async def test_recommendations_include_evidence_schema():
    engine = RecommendationEngine()
    known = {
        "soil_organic_carbon": 0.3,
        "rainfall": "low",
        "land_use": "continuous_monoculture",
        "habitat_diversity": "low",
    }
    evidence = [
        {
            "content": (
                "Cover crops including legumes add organic inputs and support soil biota. "
                "Diversifying cropping systems reduces monoculture habitat simplification. "
                "Water retention practices buffer rainfall deficits."
            ),
            "similarity": 0.75,
            "source": {
                "id": "s1",
                "title": "FAO Soil Organic Carbon",
                "organization": "FAO",
                "publication_year": 2017,
                "url": "https://www.fao.org/documents/card/en/c/I6937EN",
                "source_type": "institutional_report",
            },
        },
        {
            "content": (
                "Agroforestry and habitat corridors improve ecological connectivity. "
                "Pollinator habitat with flowering strips supports biodiversity."
            ),
            "similarity": 0.7,
            "source": {
                "id": "s2",
                "title": "FAO Agroecology",
                "organization": "FAO",
                "publication_year": 2018,
                "url": "https://www.fao.org/agroecology/overview/overview10elements/en/",
                "source_type": "institutional_report",
            },
        },
    ]
    recs = await engine.generate(
        {"soil": {"organic_carbon": 0.3}},
        known,
        {"reasoning_summary": ["multi-factor pressure"]},
        evidence,
        problem="biodiversity_decline",
    )
    assert len(recs) >= 1
    for rec in recs:
        assert rec.title
        assert rec.action
        assert rec.scientific_reasoning
        assert rec.impacted_metrics
        assert rec.time_horizon in {"short", "medium", "long"}
        assert 0 <= rec.confidence <= 1
        assert len(rec.evidence) >= 1


@pytest.mark.asyncio
async def test_unsupported_quantitative_claims_rejected():
    validator = EvidenceValidator()
    rec = Recommendation(
        title="Fake percent claim",
        action="Do something",
        scientific_reasoning="This will increase biodiversity by 45%.",
        impacted_metrics=["species richness"],
        expected_direction="increase",
        estimated_effect="45% increase",
        time_horizon="medium",
        confidence=0.9,
        evidence=[
            EvidenceItem(
                source_title="FAO Soil Organic Carbon",
                organization="FAO",
                publication_year=2017,
                url="https://www.fao.org/documents/card/en/c/I6937EN",
                relevant_snippet="Soil organic carbon supports soil ecological function.",
                similarity=0.6,
            )
        ],
    )
    evidence = [
        {
            "source": {
                "title": "FAO Soil Organic Carbon",
                "url": "https://www.fao.org/documents/card/en/c/I6937EN",
            },
            "content": "Soil organic carbon supports soil ecological function.",
        }
    ]
    result = await validator.validate([rec], evidence, {"soil_organic_carbon": 0.3})
    assert result["rejected_quantitative_claims"]
    validated = result["recommendations"][0]
    assert (
        "could not be reliably estimated" in (validated.estimated_effect or "").lower()
    )


@pytest.mark.asyncio
async def test_recommendation_without_evidence_rejected():
    validator = EvidenceValidator()
    rec = Recommendation(
        title="No evidence",
        action="Guess",
        scientific_reasoning="Because",
        impacted_metrics=["soil"],
        expected_direction="improve",
        estimated_effect=None,
        time_horizon="short",
        confidence=0.8,
        evidence=[],
    )
    result = await validator.validate([rec], [], {})
    assert result["recommendations"] == []
    assert result["issues"]

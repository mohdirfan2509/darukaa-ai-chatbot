import pytest

from app.services.ai.query_analyzer import QueryAnalyzer


@pytest.mark.asyncio
async def test_extract_multi_variable_query():
    analyzer = QueryAnalyzer()
    result = await analyzer.analyze(
        "My biodiversity is declining. I have 0.3% soil organic carbon, "
        "low rainfall and continuous wheat cultivation."
    )
    known = result["known_variables"]
    assert known["soil_organic_carbon"] == 0.3
    assert known["rainfall"] == "low"
    assert known["crop"] == "wheat"
    assert known["land_use"] == "continuous_monoculture"
    assert result["problem"] == "biodiversity_decline"


@pytest.mark.asyncio
async def test_missing_information_detection():
    analyzer = QueryAnalyzer()
    result = await analyzer.analyze("Biodiversity is declining on my land.")
    assert result["needs_clarification"] is True
    assert "soil_organic_carbon" in result["missing_variables"]
    assert "rainfall" in result["missing_variables"]
    assert "land_use" in result["missing_variables"]


@pytest.mark.asyncio
async def test_conversation_memory_merge():
    analyzer = QueryAnalyzer()
    prior = {"soil_organic_carbon": 0.3, "rainfall": "low"}
    result = await analyzer.analyze(
        "I grow wheat continuously.",
        known_variables=prior,
    )
    known = result["known_variables"]
    assert known["soil_organic_carbon"] == 0.3
    assert known["rainfall"] == "low"
    assert known["crop"] == "wheat"
    assert known["land_use"] == "continuous_monoculture"

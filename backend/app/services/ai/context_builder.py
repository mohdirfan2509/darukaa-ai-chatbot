"""Build structured environmental state from known variables."""

from __future__ import annotations

from typing import Any


def build_environmental_state(known: dict[str, Any]) -> dict[str, Any]:
    soil: dict[str, Any] = {}
    climate: dict[str, Any] = {}
    land_use: dict[str, Any] = {}
    biodiversity: dict[str, Any] = {}
    human_impact: dict[str, Any] = {}
    geography: dict[str, Any] = {}

    if "soil_organic_carbon" in known:
        soil["organic_carbon"] = known["soil_organic_carbon"]
    if "soil_ph" in known:
        soil["ph"] = known["soil_ph"]
    if "soil_moisture" in known:
        soil["moisture"] = known["soil_moisture"]

    if "rainfall" in known:
        climate["rainfall"] = known["rainfall"]
    if "temperature" in known:
        climate["temperature"] = known["temperature"]

    if "land_use" in known:
        land_use["type"] = known["land_use"]
    if "crop" in known:
        land_use["crop"] = known["crop"]

    if "species_richness" in known:
        biodiversity["species_richness"] = known["species_richness"]
    if "habitat_diversity" in known:
        biodiversity["habitat_diversity"] = known["habitat_diversity"]

    if "pollution" in known:
        human_impact["pollution"] = known["pollution"]
    if "deforestation" in known:
        human_impact["deforestation"] = known["deforestation"]
    if "habitat_fragmentation" in known:
        human_impact["habitat_fragmentation"] = known["habitat_fragmentation"]

    if "region" in known:
        geography["region"] = known["region"]
    if "latitude" in known:
        geography["latitude"] = known["latitude"]
    if "longitude" in known:
        geography["longitude"] = known["longitude"]

    state: dict[str, Any] = {}
    if soil:
        state["soil"] = soil
    if climate:
        state["climate"] = climate
    if land_use:
        state["land_use"] = land_use
    if biodiversity:
        state["biodiversity"] = biodiversity
    if human_impact:
        state["human_impact"] = human_impact
    if geography:
        state["geography"] = geography

    # Provenance markers for UI
    state["_provenance"] = {
        "user_provided": list(known.keys()),
        "inferred": [],
        "evidence_supported": [],
    }
    return state


def variables_considered(state: dict[str, Any]) -> list[str]:
    labels = []
    mapping = [
        (("soil", "organic_carbon"), "soil organic carbon"),
        (("soil", "ph"), "soil pH"),
        (("soil", "moisture"), "soil moisture"),
        (("climate", "rainfall"), "rainfall"),
        (("climate", "temperature"), "temperature"),
        (("land_use", "type"), "land use"),
        (("land_use", "crop"), "crop"),
        (("biodiversity", "species_richness"), "species richness"),
        (("biodiversity", "habitat_diversity"), "habitat diversity"),
        (("human_impact", "pollution"), "pollution"),
        (("human_impact", "deforestation"), "deforestation"),
        (("human_impact", "habitat_fragmentation"), "habitat fragmentation"),
        (("geography", "region"), "region"),
    ]
    for path, label in mapping:
        section = state.get(path[0], {})
        if isinstance(section, dict) and path[1] in section:
            labels.append(label)
    return labels

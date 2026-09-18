# Evaluator scenarios

All numeric values below are **Synthetic Demo Data** unless otherwise noted.

## 1. Low organic carbon + low rainfall + monoculture

- **Input:** Soil organic carbon is 0.3%, rainfall is low, I grow wheat continuously in a semi-arid region and biodiversity is declining.
- **Variables detected:** soil_organic_carbon, rainfall, crop, land_use, region, problem=biodiversity_decline
- **Missing:** may still list optional vars (pH, species richness)
- **Retrieval topics:** soil_health, land_use, climate, biodiversity
- **Expected reasoning:** multi-factor soil + water + monoculture pressure
- **Recommendations:** cover crops / diversification / water retention / agroforestry (evidence-linked)
- **Evidence:** FAO/IPCC/CBD-style retrieved sources required

## 2. Habitat fragmentation + low species richness

- **Input:** Habitat fragmentation is high and species richness is 12. Biodiversity is declining. Land use is degraded land.
- **Variables:** habitat_fragmentation, species_richness, land_use, problem
- **Retrieval:** biodiversity, human_impact
- **Recommendations:** corridors, restore degraded patches

## 3. High temperature + water stress + degraded soil

- **Input:** Temperature is 34 C, rainfall is low, soil organic carbon is 0.5%, soil moisture is low.
- **Reasoning:** heat + water stress + low SOC coupling
- **Recommendations:** water retention, reduce disturbance, organic inputs

## 4. Pollution + biodiversity decline

- **Input:** Elevated pollution on degraded land, species richness is 9, biodiversity declining.
- **Recommendations:** pollution mitigation + habitat restoration

## 5. Deforestation + habitat fragmentation

- **Input:** Recent deforestation and high habitat fragmentation with low habitat diversity.
- **Recommendations:** corridors, restore native vegetation

## 6. High rainfall + poor land management

- **Input:** High rainfall, continuous monoculture wheat, soil organic carbon is 0.8%, habitat diversity low.
- **Recommendations:** diversification, cover crops, pollinator habitat

## 7. Insufficient information

- **Input:** Biodiversity is declining on my land.
- **Expected:** needs_clarification=true, targeted questions for SOC, rainfall, land use

## 8. Multi-turn memory

- **Turn 1:** Biodiversity is declining on my land.
- **Turn 2:** Organic carbon is 0.3%, rainfall is low, and I grow wheat continuously.
- **Expected:** remembers turn-1 problem; merges variables; produces multi-metric recommendations with evidence

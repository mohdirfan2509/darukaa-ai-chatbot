"""Query analyzer: extract environmental variables from natural language."""

from __future__ import annotations

import re
from typing import Any, Optional

from app.core.logging import get_logger
from app.prompts.query_analysis import QUERY_ANALYSIS_PROMPT, QUERY_ANALYSIS_SYSTEM
from app.services.ai.llm_provider import LLMProvider, get_llm_provider

logger = get_logger("query_analyzer")

# Critical variables prioritized for clarifying questions
CRITICAL_BY_PROBLEM: dict[str, list[str]] = {
    "biodiversity_decline": [
        "soil_organic_carbon",
        "rainfall",
        "land_use",
        "habitat_diversity",
    ],
    "soil_degradation": ["soil_organic_carbon", "soil_ph", "land_use", "rainfall"],
    "water_stress": ["rainfall", "soil_moisture", "temperature", "land_use"],
    "pollution": ["pollution", "species_richness", "land_use"],
    "habitat_loss": [
        "habitat_fragmentation",
        "deforestation",
        "species_richness",
        "land_use",
    ],
    "default": ["soil_organic_carbon", "rainfall", "land_use"],
}

OPTIONAL_VARIABLES = [
    "soil_ph",
    "soil_moisture",
    "temperature",
    "species_richness",
    "latitude",
    "longitude",
    "region",
]


class QueryAnalyzer:
    def __init__(self, llm: Optional[LLMProvider] = None) -> None:
        self.llm = llm or get_llm_provider()

    async def analyze(
        self,
        message: str,
        known_variables: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        known = dict(known_variables or {})
        extracted = self._rule_based_extract(message)

        # Optionally enrich with LLM JSON (ignored if empty/mock)
        try:
            prompt = QUERY_ANALYSIS_PROMPT.format(
                message=message,
                known_variables=known,
            )
            llm_result = await self.llm.complete_json(
                prompt, system=QUERY_ANALYSIS_SYSTEM
            )
            if isinstance(llm_result, dict) and llm_result.get("variables"):
                for k, v in llm_result["variables"].items():
                    if v is not None and extracted["variables"].get(k) is None:
                        extracted["variables"][k] = v
                if llm_result.get("problem") and not extracted.get("problem"):
                    extracted["problem"] = llm_result["problem"]
                if llm_result.get("requested_outcomes"):
                    extracted["requested_outcomes"] = llm_result["requested_outcomes"]
        except Exception as exc:  # noqa: BLE001
            logger.warning("llm_query_analysis_failed", error=str(exc))

        # Merge with prior conversation memory (prior wins only if new is null)
        merged_vars = dict(known)
        for k, v in extracted["variables"].items():
            if v is not None:
                merged_vars[k] = v

        # Clean nulls from variables dict for known set
        known_clean = {k: v for k, v in merged_vars.items() if v is not None}

        problem = extracted.get("problem") or self._infer_problem(message, known_clean)
        critical = CRITICAL_BY_PROBLEM.get(
            problem or "default", CRITICAL_BY_PROBLEM["default"]
        )
        missing = [v for v in critical if v not in known_clean]
        optional_missing = [v for v in OPTIONAL_VARIABLES if v not in known_clean]

        result = {
            "variables": extracted["variables"],
            "known_variables": known_clean,
            "missing_variables": missing,
            "critical_variables": critical,
            "optional_variables": optional_missing,
            "problem": problem,
            "requested_outcomes": extracted.get("requested_outcomes", []),
            "units_detected": extracted.get("units_detected", {}),
            "raw_extractions": extracted.get("raw_extractions", []),
            "needs_clarification": len(missing) >= 2
            and not self._has_enough_for_reasoning(known_clean),
        }
        logger.info(
            "query_analyzed",
            problem=problem,
            known=list(known_clean.keys()),
            missing=missing,
        )
        return result

    def _has_enough_for_reasoning(self, known: dict[str, Any]) -> bool:
        """Need at least 3 environmental variables for multi-metric reasoning."""
        env_keys = [
            "soil_organic_carbon",
            "soil_ph",
            "soil_moisture",
            "rainfall",
            "temperature",
            "land_use",
            "crop",
            "species_richness",
            "habitat_diversity",
            "pollution",
            "deforestation",
            "habitat_fragmentation",
        ]
        return sum(1 for k in env_keys if k in known) >= 3

    def _infer_problem(self, message: str, known: dict[str, Any]) -> Optional[str]:
        m = message.lower()
        if any(w in m for w in ["biodivers", "species richness", "pollinator"]):
            return "biodiversity_decline"
        if any(w in m for w in ["pollution", "contaminat", "chemical"]):
            return "pollution"
        if any(w in m for w in ["deforest", "forest loss", "clearing"]):
            return "habitat_loss"
        if any(w in m for w in ["fragment", "corridor", "habitat loss"]):
            return "habitat_loss"
        if any(w in m for w in ["drought", "water stress", "dry"]):
            return "water_stress"
        if any(w in m for w in ["soil", "organic carbon", "erosion"]):
            return "soil_degradation"
        if known.get("problem"):
            return str(known["problem"])
        return (
            "biodiversity_decline"
            if "biodiversity" in str(known).lower()
            else "default"
        )

    def _rule_based_extract(self, message: str) -> dict[str, Any]:
        m = message.lower()
        variables: dict[str, Any] = {
            "soil_organic_carbon": None,
            "soil_ph": None,
            "soil_moisture": None,
            "rainfall": None,
            "temperature": None,
            "land_use": None,
            "crop": None,
            "species_richness": None,
            "habitat_diversity": None,
            "pollution": None,
            "deforestation": None,
            "habitat_fragmentation": None,
            "region": None,
            "latitude": None,
            "longitude": None,
        }
        units: dict[str, str] = {}
        raw: list[str] = []

        # Soil organic carbon
        soc = re.search(
            r"(?:soil\s+)?organic\s+carbon(?:\s+is|\s*[:=])?\s*([\d.]+)\s*%?",
            m,
        )
        if not soc:
            soc = re.search(r"([\d.]+)\s*%\s*(?:soil\s+)?organic\s+carbon", m)
        if soc:
            variables["soil_organic_carbon"] = float(soc.group(1))
            units["soil_organic_carbon"] = "%"
            raw.append(f"soil_organic_carbon={soc.group(1)}")

        # Soil pH
        ph = re.search(r"(?:soil\s+)?pH(?:\s+is|\s*[:=])?\s*([\d.]+)", m, re.I)
        if ph:
            variables["soil_ph"] = float(ph.group(1))
            raw.append(f"soil_ph={ph.group(1)}")

        # Temperature
        temp = re.search(
            r"(?:temperature|temp)(?:\s+is|\s*[:=])?\s*([\d.]+)\s*°?\s*c?", m
        )
        if temp:
            variables["temperature"] = float(temp.group(1))
            units["temperature"] = "C"
            raw.append(f"temperature={temp.group(1)}")

        # Species richness
        sr = re.search(r"species\s+richness(?:\s+is|\s*[:=])?\s*([\d.]+)", m)
        if sr:
            variables["species_richness"] = float(sr.group(1))
            raw.append(f"species_richness={sr.group(1)}")

        # Rainfall qualitative / quantitative
        if re.search(
            r"rainfall\s+(increases?|increased|higher|rises?)|"
            r"if\s+rainfall\s+increases?|"
            r"increased\s+rainfall|"
            r"more\s+rainfall",
            m,
        ):
            variables["rainfall"] = "high"
            raw.append("rainfall=high")
        elif re.search(
            r"rainfall\s+(decreases?|decreased|lower|falls?)|"
            r"if\s+rainfall\s+decreases?|"
            r"reduced\s+rainfall|"
            r"less\s+rainfall",
            m,
        ):
            variables["rainfall"] = "low"
            raw.append("rainfall=low")
        elif re.search(
            r"\b(low|scarce|limited)\s+rainfall\b|\brainfall\s+is\s+low\b", m
        ):
            variables["rainfall"] = "low"
            raw.append("rainfall=low")
        elif re.search(
            r"\b(high|abundant|heavy)\s+rainfall\b|\brainfall\s+is\s+high\b", m
        ):
            variables["rainfall"] = "high"
            raw.append("rainfall=high")
        elif re.search(r"\bmoderate\s+rainfall\b|\brainfall\s+is\s+moderate\b", m):
            variables["rainfall"] = "moderate"
            raw.append("rainfall=moderate")
        rain_mm = re.search(r"rainfall(?:\s+is|\s*[:=])?\s*([\d.]+)\s*mm", m)
        if rain_mm:
            variables["rainfall"] = float(rain_mm.group(1))
            units["rainfall"] = "mm"
            raw.append(f"rainfall={rain_mm.group(1)}mm")

        # Soil moisture
        if re.search(r"soil\s+moisture(?:\s+is)?\s+low|low\s+soil\s+moisture", m):
            variables["soil_moisture"] = "low"
        elif re.search(r"soil\s+moisture(?:\s+is)?\s+high|high\s+soil\s+moisture", m):
            variables["soil_moisture"] = "high"

        # Habitat diversity
        if re.search(
            r"low\s+habitat\s+diversity|habitat\s+diversity(?:\s+is)?\s+low", m
        ):
            variables["habitat_diversity"] = "low"
        elif re.search(
            r"high\s+habitat\s+diversity|habitat\s+diversity(?:\s+is)?\s+high", m
        ):
            variables["habitat_diversity"] = "high"
        elif re.search(r"moderate\s+habitat\s+diversity", m):
            variables["habitat_diversity"] = "moderate"

        # Land use / crops
        if re.search(r"wheat", m):
            variables["crop"] = "wheat"
            if re.search(r"continuous|monoculture|continuously", m):
                variables["land_use"] = "continuous_monoculture"
            else:
                variables["land_use"] = variables["land_use"] or "agriculture"
        if re.search(r"monoculture", m) and not variables["land_use"]:
            variables["land_use"] = "continuous_monoculture"
        if re.search(r"mixed\s+crop", m):
            variables["land_use"] = "mixed_cropping"
        if re.search(r"agroforestry", m):
            variables["land_use"] = "agroforestry"
        if re.search(r"\bgrassland\b", m):
            variables["land_use"] = "grassland"
        if re.search(r"\bwetland\b", m):
            variables["land_use"] = "wetland"
        if re.search(r"\bforest\b", m) and not re.search(r"deforest", m):
            variables["land_use"] = variables["land_use"] or "forest"
        if re.search(r"degraded\s+land", m):
            variables["land_use"] = "degraded_land"

        # Human impact
        if re.search(r"pollution|polluted", m):
            variables["pollution"] = "elevated"
        if re.search(r"deforest", m):
            variables["deforestation"] = "present"
        if re.search(r"fragment", m):
            variables["habitat_fragmentation"] = "high"
        if re.search(r"intensive\s+agricultur", m):
            variables["land_use"] = variables["land_use"] or "intensive_agriculture"

        # Region
        if re.search(r"semi[- ]arid", m):
            variables["region"] = "semi-arid"
        elif re.search(r"arid", m):
            variables["region"] = "arid"
        elif re.search(r"tropical", m):
            variables["region"] = "tropical"
        elif re.search(r"temperate", m):
            variables["region"] = "temperate"

        # Coordinates
        lat = re.search(r"lat(?:itude)?[:\s]+(-?[\d.]+)", m)
        lon = re.search(r"lon(?:gitude)?[:\s]+(-?[\d.]+)", m)
        if lat:
            variables["latitude"] = float(lat.group(1))
        if lon:
            variables["longitude"] = float(lon.group(1))

        problem = self._infer_problem(
            message, {k: v for k, v in variables.items() if v}
        )

        # Moderate soil carbon phrase
        if re.search(r"moderate\s+soil\s+carbon|moderate\s+organic\s+carbon", m):
            if variables["soil_organic_carbon"] is None:
                variables["soil_organic_carbon"] = "moderate"
                raw.append("soil_organic_carbon=moderate")

        return {
            "variables": variables,
            "problem": problem,
            "requested_outcomes": [],
            "units_detected": units,
            "raw_extractions": raw,
        }

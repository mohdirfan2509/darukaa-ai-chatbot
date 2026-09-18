"""LLM provider abstraction."""

from abc import ABC, abstractmethod
from typing import Any, Optional

import httpx

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("llm")


class LLMProvider(ABC):
    @abstractmethod
    async def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> str:
        raise NotImplementedError

    @abstractmethod
    async def complete_json(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        raise NotImplementedError


class MockLLMProvider(LLMProvider):
    """Deterministic mock for offline development and tests."""

    async def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> str:
        return (
            "Based on the retrieved evidence and environmental context provided, "
            "multi-metric relationships indicate combined soil, climate, and land-use "
            "pressures that warrant targeted ecological interventions grounded in the "
            "cited institutional guidance."
        )

    async def complete_json(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        # Mock returns empty dict — callers use rule-based fallbacks.
        return {}


class OpenAILLMProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model
        self.base_url = settings.llm_base_url or "https://api.openai.com/v1"

    async def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "model": self.model,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]

    async def complete_json(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        import json
        import re

        text = await self.complete(
            prompt,
            system=(system or "")
            + "\nRespond with valid JSON only. No markdown fences.",
            temperature=temperature,
        )
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        return json.loads(text)


class AnthropicLLMProvider(LLMProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.llm_api_key
        self.model = settings.llm_model or "claude-3-5-haiku-20241022"

    async def complete(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> str:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": self.model,
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "system": system
                    or "You are an environmental intelligence assistant.",
                    "messages": [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data["content"][0]["text"]

    async def complete_json(
        self,
        prompt: str,
        *,
        system: Optional[str] = None,
        temperature: float = 0.1,
    ) -> dict[str, Any]:
        import json
        import re

        text = await self.complete(
            prompt,
            system=(system or "")
            + "\nRespond with valid JSON only. No markdown fences.",
            temperature=temperature,
        )
        text = text.strip()
        if text.startswith("```"):
            text = re.sub(r"^```(?:json)?\s*", "", text)
            text = re.sub(r"\s*```$", "", text)
        return json.loads(text)


def get_llm_provider() -> LLMProvider:
    settings = get_settings()
    provider = settings.llm_provider.lower().strip()
    if provider == "openai":
        if not settings.llm_api_key:
            logger.warning("openai_key_missing_using_mock")
            return MockLLMProvider()
        return OpenAILLMProvider()
    if provider == "anthropic":
        if not settings.llm_api_key:
            logger.warning("anthropic_key_missing_using_mock")
            return MockLLMProvider()
        return AnthropicLLMProvider()
    return MockLLMProvider()

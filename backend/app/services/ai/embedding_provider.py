"""Embedding provider abstraction with deterministic mock for offline use."""

import hashlib
import math
from abc import ABC, abstractmethod
from typing import List

import httpx
import numpy as np

from app.core.config import get_settings
from app.core.logging import get_logger

logger = get_logger("embeddings")


class EmbeddingProvider(ABC):
    @abstractmethod
    async def embed(self, texts: List[str]) -> List[List[float]]:
        raise NotImplementedError

    async def embed_one(self, text: str) -> List[float]:
        results = await self.embed([text])
        return results[0]


class MockEmbeddingProvider(EmbeddingProvider):
    """
    Deterministic hash-based embeddings for offline development/tests.
    Similar texts with shared tokens tend to get closer cosine similarity
    via bag-of-tokens hashing into a fixed vector space.
    """

    def __init__(self, dimensions: int | None = None) -> None:
        settings = get_settings()
        self.dimensions = dimensions or settings.embedding_dimensions

    def _tokenize(self, text: str) -> list[str]:
        return [t for t in text.lower().replace("-", " ").split() if t]

    def _vector(self, text: str) -> list[float]:
        vec = np.zeros(self.dimensions, dtype=np.float64)
        tokens = self._tokenize(text)
        if not tokens:
            tokens = ["empty"]
        for token in tokens:
            digest = hashlib.sha256(token.encode("utf-8")).digest()
            # Map token into several dimensions for better distribution
            for i in range(4):
                idx = (
                    int.from_bytes(digest[i * 4 : (i + 1) * 4], "big") % self.dimensions
                )
                sign = 1.0 if digest[16 + i] % 2 == 0 else -1.0
                vec[idx] += sign
        # Add phrase-level component
        phrase = hashlib.sha256(text.lower().encode("utf-8")).digest()
        for i in range(8):
            idx = int.from_bytes(phrase[i * 2 : i * 2 + 2], "big") % self.dimensions
            vec[idx] += 0.25
        norm = np.linalg.norm(vec)
        if norm < 1e-12:
            vec[0] = 1.0
            norm = 1.0
        vec = vec / norm
        return vec.astype(float).tolist()

    async def embed(self, texts: List[str]) -> List[List[float]]:
        return [self._vector(t) for t in texts]


class OpenAIEmbeddingProvider(EmbeddingProvider):
    def __init__(self) -> None:
        settings = get_settings()
        self.api_key = settings.embedding_api_key or settings.llm_api_key
        self.model = settings.embedding_model
        self.dimensions = settings.embedding_dimensions

    async def embed(self, texts: List[str]) -> List[List[float]]:
        import asyncio

        payload: dict = {"model": self.model, "input": texts}
        if "text-embedding-3" in self.model:
            payload["dimensions"] = self.dimensions

        last_error: Exception | None = None
        for attempt in range(6):
            try:
                async with httpx.AsyncClient(timeout=60.0) as client:
                    resp = await client.post(
                        "https://api.openai.com/v1/embeddings",
                        headers={"Authorization": f"Bearer {self.api_key}"},
                        json=payload,
                    )
                    if resp.status_code == 429:
                        wait = min(2**attempt, 30)
                        logger.warning(
                            "embedding_rate_limited", attempt=attempt, wait=wait
                        )
                        await asyncio.sleep(wait)
                        continue
                    resp.raise_for_status()
                    data = resp.json()
                    sorted_data = sorted(data["data"], key=lambda x: x["index"])
                    return [item["embedding"] for item in sorted_data]
            except Exception as exc:  # noqa: BLE001
                last_error = exc
                await asyncio.sleep(min(2**attempt, 20))
        raise RuntimeError(f"OpenAI embeddings failed after retries: {last_error}")


def cosine_similarity(a: list[float], b: list[float]) -> float:
    va = np.array(a, dtype=np.float64)
    vb = np.array(b, dtype=np.float64)
    denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
    if denom < 1e-12:
        return 0.0
    return float(np.dot(va, vb) / denom)


def get_embedding_provider() -> EmbeddingProvider:
    settings = get_settings()
    provider = settings.embedding_provider.lower().strip()
    if provider == "openai":
        if not (settings.embedding_api_key or settings.llm_api_key):
            logger.warning("embedding_key_missing_using_mock")
            return MockEmbeddingProvider()
        return OpenAIEmbeddingProvider()
    return MockEmbeddingProvider()


# Silence unused import warning for math in some linters
_ = math

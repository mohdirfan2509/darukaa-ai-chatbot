"""Pytest configuration and shared fixtures."""

import os

import pytest

# Force mock providers for tests
os.environ.setdefault("LLM_PROVIDER", "mock")
os.environ.setdefault("EMBEDDING_PROVIDER", "mock")
os.environ.setdefault("EMBEDDING_DIMENSIONS", "384")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+psycopg://darukaa:darukaa@localhost:5433/darukaa_ai",
)


@pytest.fixture
def anyio_backend():
    return "asyncio"

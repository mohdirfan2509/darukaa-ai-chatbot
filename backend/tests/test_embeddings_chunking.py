import pytest

from app.services.ai.embedding_provider import MockEmbeddingProvider, cosine_similarity
from app.services.knowledge.ingestion import chunk_text, clean_text


def test_clean_and_chunk():
    text = "Paragraph one.\n\n\nParagraph two is longer and should stay.\n\nParagraph three."
    cleaned = clean_text(text)
    chunks = chunk_text(cleaned, chunk_size=80, overlap=10)
    assert cleaned
    assert len(chunks) >= 1


@pytest.mark.asyncio
async def test_mock_embeddings_are_deterministic():
    emb = MockEmbeddingProvider(dimensions=384)
    a1 = await emb.embed_one("soil organic carbon biodiversity")
    a2 = await emb.embed_one("soil organic carbon biodiversity")
    b = await emb.embed_one("completely unrelated quantum computing topic xyz")
    assert a1 == a2
    assert cosine_similarity(a1, a2) > 0.99
    assert cosine_similarity(a1, b) < cosine_similarity(a1, a2)

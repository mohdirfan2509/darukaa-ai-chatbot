"""Knowledge ingestion: clean → chunk → embed → store."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

import yaml
from sqlalchemy.orm import Session

from app.core.logging import get_logger
from app.models.knowledge import KnowledgeChunk, KnowledgeDocument, KnowledgeSource
from app.services.ai.embedding_provider import EmbeddingProvider, get_embedding_provider

logger = get_logger("ingestion")


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def chunk_text(
    text: str,
    *,
    chunk_size: int = 700,
    overlap: int = 100,
) -> list[str]:
    """Paragraph-aware chunking with character overlap."""
    text = clean_text(text)
    if not text:
        return []
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    current = ""
    for para in paragraphs:
        if len(current) + len(para) + 2 <= chunk_size:
            current = f"{current}\n\n{para}".strip() if current else para
        else:
            if current:
                chunks.append(current)
            if len(para) <= chunk_size:
                # overlap from previous
                if chunks and overlap > 0:
                    prev_tail = chunks[-1][-overlap:]
                    current = f"{prev_tail}\n\n{para}".strip()
                else:
                    current = para
            else:
                # hard split long paragraph
                start = 0
                while start < len(para):
                    end = start + chunk_size
                    piece = para[start:end]
                    chunks.append(piece)
                    start = end - overlap if overlap < chunk_size else end
                current = ""
    if current:
        chunks.append(current)
    return chunks


class KnowledgeIngestionService:
    def __init__(
        self,
        db: Session,
        embedder: Optional[EmbeddingProvider] = None,
    ) -> None:
        self.db = db
        self.embedder = embedder or get_embedding_provider()

    async def ingest_document(
        self,
        *,
        source_title: str,
        document_title: str,
        content: str,
        organization: Optional[str] = None,
        authors: Optional[str] = None,
        publication_year: Optional[int] = None,
        source_type: str = "institutional_report",
        url: Optional[str] = None,
        topic: Optional[str] = None,
        geographic_scope: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        source = KnowledgeSource(
            title=source_title,
            organization=organization,
            authors=authors,
            publication_year=publication_year,
            source_type=source_type,
            url=url,
            topic=topic,
            geographic_scope=geographic_scope,
        )
        self.db.add(source)
        self.db.flush()

        doc = KnowledgeDocument(
            source_id=source.id,
            title=document_title,
            content=clean_text(content),
            metadata_=metadata or {},
        )
        self.db.add(doc)
        self.db.flush()

        pieces = chunk_text(doc.content)
        embeddings = await self.embedder.embed(pieces) if pieces else []

        for idx, (piece, emb) in enumerate(zip(pieces, embeddings)):
            chunk = KnowledgeChunk(
                document_id=doc.id,
                chunk_index=idx,
                content=piece,
                metadata_={
                    "source_title": source_title,
                    "organization": organization,
                    "publication_year": publication_year,
                    "topic": topic,
                    "url": url,
                    "topics": topic,
                },
                embedding=emb,
            )
            self.db.add(chunk)

        self.db.commit()
        logger.info(
            "document_ingested",
            source_id=str(source.id),
            document_id=str(doc.id),
            chunks=len(pieces),
        )
        return {
            "source_id": source.id,
            "document_id": doc.id,
            "chunks_created": len(pieces),
        }

    async def ingest_from_manifest(self, knowledge_dir: Path) -> dict[str, Any]:
        """
        Ingest YAML manifests + markdown/text bodies from knowledge/sources/.

        Each source folder may contain:
          - manifest.yaml
          - content.md (or content.txt)
        """
        sources_root = knowledge_dir / "sources"
        if not sources_root.exists():
            raise FileNotFoundError(f"Knowledge sources not found: {sources_root}")

        total_docs = 0
        total_chunks = 0
        for folder in sorted(sources_root.iterdir()):
            if not folder.is_dir():
                continue
            manifest_path = folder / "manifest.yaml"
            if not manifest_path.exists():
                continue
            manifest = yaml.safe_load(manifest_path.read_text(encoding="utf-8"))
            content_path = folder / "content.md"
            if not content_path.exists():
                content_path = folder / "content.txt"
            if not content_path.exists():
                logger.warning("missing_content", folder=str(folder))
                continue
            body = content_path.read_text(encoding="utf-8")
            result = await self.ingest_document(
                source_title=manifest["title"],
                document_title=manifest.get("document_title", manifest["title"]),
                content=body,
                organization=manifest.get("organization"),
                authors=manifest.get("authors"),
                publication_year=manifest.get("publication_year"),
                source_type=manifest.get("source_type", "institutional_report"),
                url=manifest.get("url"),
                topic=manifest.get("topic"),
                geographic_scope=manifest.get("geographic_scope"),
                metadata=manifest.get("metadata") or {},
            )
            total_docs += 1
            total_chunks += result["chunks_created"]
            # Gentle pacing for provider rate limits during bulk ingest
            import asyncio

            await asyncio.sleep(1.0)

        return {"documents": total_docs, "chunks": total_chunks}

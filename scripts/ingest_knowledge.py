#!/usr/bin/env python3
"""Ingest local knowledge files into PostgreSQL + pgvector."""

from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

# Allow running from repo root or backend/
ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.core.database import SessionLocal  # noqa: E402
from app.services.knowledge.ingestion import KnowledgeIngestionService  # noqa: E402


async def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest Darukaa knowledge base")
    parser.add_argument(
        "--knowledge-dir",
        type=Path,
        default=ROOT / "knowledge",
        help="Path to knowledge directory",
    )
    args = parser.parse_args()

    db = SessionLocal()
    try:
        service = KnowledgeIngestionService(db)
        result = await service.ingest_from_manifest(args.knowledge_dir)
        print(f"Ingested documents={result['documents']} chunks={result['chunks']}")
    finally:
        db.close()


if __name__ == "__main__":
    asyncio.run(main())

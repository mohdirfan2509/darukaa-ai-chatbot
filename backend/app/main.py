"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import chat, environment, health, knowledge
from app.core.config import get_settings
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(_app: FastAPI):
    setup_logging()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="Darukaa.Earth AI Biodiversity Intelligence Chatbot",
        description=(
            "An AI environmental intelligence system with RAG, multi-metric reasoning, "
            "and evidence-validated recommendations — not an LLM-only chatbot."
        ),
        version="1.0.0",
        lifespan=lifespan,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    prefix = settings.api_prefix
    app.include_router(chat.router, prefix=prefix)
    app.include_router(knowledge.router, prefix=prefix)
    app.include_router(environment.router, prefix=prefix)
    return app


app = create_app()

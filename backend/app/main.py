"""FastAPI main application entrypoint for Contact Center Agent Helper Platform."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.container import get_container


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Application startup and shutdown lifespan events."""
    get_container()
    # Startup tasks
    yield
    # Shutdown tasks


def create_app() -> FastAPI:
    """Application factory for FastAPI server."""
    settings = get_settings()

    app = FastAPI(
        title=settings.APP_NAME,
        version="0.1.0",
        description="Real-time Contact Center Agent Assist Platform",
        lifespan=lifespan,
    )

    # CORS configuration for Vite frontend
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    async def health_check() -> dict[str, Any]:
        """Health check endpoint used by Docker, Kubernetes, and Cloud Run."""
        return {
            "status": "ok",
            "app": settings.APP_NAME,
            "profile": settings.APP_PROFILE,
        }

    # Mount WebSocket and session endpoints
    from app.ws.session import router as ws_router

    app.include_router(ws_router)

    return app


app = create_app()

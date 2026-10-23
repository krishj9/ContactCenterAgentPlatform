"""Database connection, engine configuration, and session factories."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""

    pass


_engine: AsyncEngine | None = None
_session_maker: async_sessionmaker[AsyncSession] | None = None


def get_async_engine(url: str | None = None, **kwargs: Any) -> AsyncEngine:
    """Get or create singleton async database engine."""
    global _engine
    if _engine is None:
        settings = get_settings()
        db_url = url or settings.POSTGRES_URL
        _engine = create_async_engine(
            db_url,
            echo=settings.DEBUG,
            future=True,
            pool_pre_ping=True,
            **kwargs,
        )
    return _engine


def get_session_factory(engine: AsyncEngine | None = None) -> async_sessionmaker[AsyncSession]:
    """Get or create sessionmaker."""
    global _session_maker
    if _session_maker is None or engine is not None:
        eng = engine or get_async_engine()
        _session_maker = async_sessionmaker(
            bind=eng,
            autocommit=False,
            autoflush=False,
            expire_on_commit=False,
        )
    return _session_maker


@asynccontextmanager
async def get_db_session(engine: AsyncEngine | None = None) -> AsyncIterator[AsyncSession]:
    """Async context manager yielding a database session."""
    factory = get_session_factory(engine)
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

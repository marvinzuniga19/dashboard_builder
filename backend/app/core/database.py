"""SQLAlchemy asíncrono y pragmas aplicados a cada conexión SQLite."""

from collections.abc import AsyncIterator
from typing import Any

from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


def configure_sqlite_connection(dbapi_connection: Any, _: Any) -> None:
    # SQLAlchemy adapta aquí el driver async al protocolo DBAPI de eventos.
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA busy_timeout=5000")
    finally:
        cursor.close()


def build_engine() -> AsyncEngine:
    url = get_settings().database_connection_url
    if url.drivername == "sqlite+aiosqlite" and url.database != ":memory:":
        from pathlib import Path

        Path(str(url.database)).parent.mkdir(parents=True, exist_ok=True)
    database_engine = create_async_engine(url, pool_pre_ping=True)
    if url.drivername == "sqlite+aiosqlite":
        event.listen(database_engine.sync_engine, "connect", configure_sqlite_connection)
    return database_engine


engine = build_engine()
session_factory = async_sessionmaker(engine, expire_on_commit=False)


async def get_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
        yield session

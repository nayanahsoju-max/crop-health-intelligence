"""SQLAlchemy engine and session setup; schema changes are managed by Alembic."""
from __future__ import annotations

import os
from collections.abc import Iterator

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker


def database_url_from_environment() -> str | None:
    """Return DATABASE_URL when configured; never invent credentials/default DBs."""
    return os.getenv("DATABASE_URL") or None


def create_database_engine(database_url: str) -> Engine:
    if not database_url:
        raise ValueError("DATABASE_URL must be set")
    if not (database_url.startswith("postgresql+") or database_url.startswith("sqlite:")):
        raise ValueError("DATABASE_URL must use PostgreSQL or SQLite")
    kwargs = {"pool_pre_ping": True}
    if database_url.startswith("sqlite:"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(database_url, **kwargs)


def create_session_factory(engine: Engine) -> sessionmaker[Session]:
    return sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def session_scope(factory: sessionmaker[Session]) -> Iterator[Session]:
    session = factory()
    try:
        yield session
    finally:
        session.close()

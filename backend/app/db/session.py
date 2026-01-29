import ssl
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# Query params that asyncpg does not understand (handled via connect_args instead)
_ASYNCPG_STRIP_PARAMS = {"sslmode", "channel_binding"}


def _is_remote_db(url: str) -> bool:
    """Detect if the database URL points to a remote/serverless provider."""
    remote_hosts = ["neon.tech", "supabase.co", "cockroachlabs.cloud"]
    return any(host in url for host in remote_hosts)


def _clean_url(url: str) -> str:
    """Strip query params that asyncpg doesn't support (sslmode, channel_binding)."""
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    cleaned = {k: v for k, v in params.items() if k not in _ASYNCPG_STRIP_PARAMS}
    new_query = urlencode(cleaned, doseq=True)
    return urlunparse(parsed._replace(query=new_query))


def _build_engine_kwargs() -> dict:
    """Build engine kwargs adapting to local or remote (Neon/serverless) database."""
    kwargs: dict = {
        "echo": settings.app_debug,
        "pool_pre_ping": True,
        "pool_recycle": 3600,
    }

    if _is_remote_db(settings.database_url):
        ssl_ctx = ssl.create_default_context()
        kwargs.update({
            "pool_size": 5,
            "max_overflow": 10,
            "connect_args": {"ssl": ssl_ctx},
        })
    else:
        kwargs.update({
            "pool_size": 10,
            "max_overflow": 20,
        })

    return kwargs


_db_url = _clean_url(settings.database_url)
engine = create_async_engine(_db_url, **_build_engine_kwargs())
async_session_factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI dependency for DB sessions."""
    async with async_session_factory() as session:
        yield session


@asynccontextmanager
async def get_standalone_session() -> AsyncGenerator[AsyncSession, None]:
    """Standalone session for use outside FastAPI (e.g., SMTP gateway)."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise

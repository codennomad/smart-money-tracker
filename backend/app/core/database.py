from functools import lru_cache
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


@lru_cache
def _get_engine():
    from .config import get_settings
    settings = get_settings()
    url = settings.DATABASE_URL
    is_sqlite = url.startswith("sqlite")
    kwargs = {"echo": settings.DEBUG}
    if not is_sqlite:
        kwargs.update({"pool_size": 10, "max_overflow": 20, "pool_pre_ping": True})
    return create_async_engine(url, **kwargs)


@lru_cache
def _get_session_factory():
    return async_sessionmaker(_get_engine(), expire_on_commit=False)


# Expose at module level for Alembic and app use
engine = _get_engine()
AsyncSessionLocal = _get_session_factory()


async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from typing import AsyncGenerator
from config import settings

async_engine = create_async_engine(
    settings.POSTGRES_DSN,
    pool_size=settings.POSTGRES_POOL_MIN_SIZE,
    max_overflow=settings.POSTGRES_POOL_MAX_SIZE - settings.POSTGRES_POOL_MIN_SIZE,
    pool_recycle=600,
    pool_pre_ping=True,
)

session_maker = async_sessionmaker(
    bind=async_engine, autoflush=False, autocommit=False, expire_on_commit=False
)


async def get_async_session() -> AsyncGenerator:
    async with session_maker() as session:
        yield session
        await session.close()

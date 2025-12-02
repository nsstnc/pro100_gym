from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

# Async engine & sessionmaker
engine: AsyncEngine = create_async_engine(settings.DB_URL, pool_pre_ping=True, future=True)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

Base = declarative_base()


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Зависимость на получение сессии. Использовать в роутерах
    """
    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """
    Инициализация БД
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
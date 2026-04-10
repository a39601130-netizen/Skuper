"""PostgreSQL async database engine and session."""

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

import config

engine = create_async_engine(config.DATABASE_URL, echo=False)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


async def get_db():
    async with async_session() as session:
        yield session


async def init_db():
    """Create all tables and run migrations."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Миграция: добавить body_weight в workouts (если ещё нет)
        await conn.execute(
            __import__('sqlalchemy').text(
                "ALTER TABLE workouts ADD COLUMN IF NOT EXISTS body_weight FLOAT"
            )
        )

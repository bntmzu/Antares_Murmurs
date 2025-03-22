from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from src.backend.config.settings import settings
from typing import AsyncGenerator

DATABASE_URL = settings.DATABASE_URL

# Create the async engine
engine = create_async_engine(DATABASE_URL, echo=True)

async_session_maker = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Dependency to get an async session
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_maker() as session:
        yield session




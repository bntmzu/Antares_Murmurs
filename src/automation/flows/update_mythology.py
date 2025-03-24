import asyncio
from datetime import datetime, timedelta, timezone
from prefect import task, flow
from sqlalchemy import select, update
from src.backend.models.star import Star
from src.backend.core.database import async_session_maker
from src.backend.services.redis_client import redis_client
from src.backend.services.ai_star_info import analyze_star_mythology
from src.automation.logging import get_prefect_logger

logger = get_prefect_logger()

MYTHOLOGY_CACHE_TTL = 31_536_000  # 1 year


@task
async def get_stars_for_mythology_update():
    """
    Retrieves stars that require mythology updates.
    Stars are selected if their last mythology update was more than a year ago or is missing.
    """
    async with async_session_maker() as session:
        one_year_ago = datetime.now(timezone.utc) - timedelta(days=365)

        result = await session.execute(
            select(Star.name).where(
                (Star.last_mythology_update.is_(None))
                | (Star.last_mythology_update < one_year_ago)
            )
        )
        stars_to_update = result.scalars().all()

    return stars_to_update


@task
async def update_star_mythology(star_name: str):
    """
    Updates the mythology description of a star in the database and caches it in Redis for one year.
    """
    async with async_session_maker() as session:
        star_record = await session.get(Star, star_name)

        if not star_record:
            logger.warning(
                f"Star {star_name} not found in the database, skipping update"
            )
            return

        # Generate new mythology
        mythology_data = await analyze_star_mythology(star_name, star_record.__dict__)

        if not mythology_data:
            logger.warning(f"Mythology data for {star_name} could not be retrieved")
            return

        # Update the database
        await session.execute(
            update(Star)
            .where(Star.name == star_name)
            .values(
                mythology=mythology_data,
                last_mythology_update=datetime.now(timezone.utc),
            )
        )
        await session.commit()

        # Cache mythology for 1 year
        await redis_client.setex(
            f"mythology:{star_name}", MYTHOLOGY_CACHE_TTL, mythology_data
        )

        logger.info(f"Mythology for {star_name} updated successfully")


@flow(name="Update Star Mythology Flow")
async def update_star_mythology_flow():
    """
    Updates star mythology using AI analysis and caches it in Redis for one year.
    """
    stars = await get_stars_for_mythology_update()

    if not stars:
        logger.info("No mythology updates needed; all data is already up-to-date.")
        return

    tasks = [update_star_mythology(star) for star in stars]
    await asyncio.gather(*tasks)

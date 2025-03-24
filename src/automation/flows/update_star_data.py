import asyncio
from prefect import task, flow
from src.backend.services.simbad_api import fetch_star_data
from src.backend.models.star import Star
from src.backend.core.database import async_session_maker
from src.backend.services.redis_client import redis_client
from src.automation.logging import get_prefect_logger

logger = get_prefect_logger()

DATA_CACHE_TTL = 7776000  # 3 months


@task
async def get_stars_from_db():
    """Retrieves the list of stars from the database."""
    async with async_session_maker() as session:
        result = await session.execute("SELECT name FROM stars")
        stars = result.scalars().all()
    return stars


@task
async def update_star_in_db(star_name: str):
    """Updates star data in the database and Redis cache."""
    star_data = await fetch_star_data(star_name)

    if not star_data:
        logger.warning(f"Data for {star_name} not found")
        return

    # Updating the database
    async with async_session_maker() as session:
        star_record = await session.get(Star, star_name)
        if star_record:
            star_record.update_from_dict(star_data)
        else:
            session.add(Star(**star_data))
        await session.commit()

    # Updating Redis cache
    await redis_client.setex(f"star:{star_name}", DATA_CACHE_TTL, star_data)
    logger.info(f"Data for {star_name} updated successfully")


@flow(name="Update Star Data Flow")
async def update_star_data():
    """Updates star characteristics from the SIMBAD API and caches them in Redis."""
    stars = await get_stars_from_db()

    if not stars:
        logger.info("No stars available for update")
        return

    tasks = [update_star_in_db(star) for star in stars]
    await asyncio.gather(*tasks)

import asyncio
from typing import Callable

from prefect.deployments import Deployment
from prefect.server.schemas.schedules import IntervalSchedule, PositiveDuration

from src.automation.flows.update_star_data import update_star_data, get_stars_from_db
from src.automation.logging import get_prefect_logger

logger = get_prefect_logger()


async def should_run_update(check_function: Callable[[], list]) -> bool:
    """
    Checks if there are stars requiring an update.

    Args:
        check_function (Callable): Function to retrieve outdated stars.

    Returns:
        bool: True if updates are needed, False otherwise.
    """
    outdated_stars = check_function()  # Убрали await, теперь работает корректно
    logger.info(f"Found {len(outdated_stars)} stars requiring updates.")
    return bool(outdated_stars)


async def apply_deployment():
    """
    Creates and applies a deployment only if an update is required.
    Runs every 3 months.
    """
    if await should_run_update(lambda: asyncio.run(get_stars_from_db())):
        deployment = Deployment.build_from_flow(
            flow=update_star_data,
            name="Update Star Data (every 3 months)",
            schedule=IntervalSchedule(
                interval=PositiveDuration(days=90)
            ),  # Исправили timedelta
            work_queue_name="default",
        )
        deployment.apply()
        logger.info("Deployment applied: SIMBAD data update scheduled.")
    else:
        logger.info("No updates required. Deployment skipped.")


if __name__ == "__main__":
    asyncio.run(apply_deployment())

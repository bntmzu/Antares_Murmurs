import asyncio
from typing import Callable

from prefect.deployments import Deployment
from prefect.server.schemas.schedules import CronSchedule

from src.automation.flows.update_mythology import (
    update_star_mythology_flow,
    get_stars_for_mythology_update,
)
from src.automation.logging import get_prefect_logger

logger = get_prefect_logger()


async def should_run_update(check_function: Callable[[], list]) -> bool:
    """
    Checks if there are stars requiring a mythology update.

    Args:
        check_function (Callable): Function to retrieve outdated mythology stars.

    Returns:
        bool: True if updates are needed, False otherwise.
    """
    outdated_stars = check_function()  # Убрали await, теперь работает корректно
    logger.info(f"Found {len(outdated_stars)} stars requiring mythology updates.")
    return bool(outdated_stars)


async def apply_deployment():
    """
    Creates and applies a deployment only if mythology updates are required.
    Runs every year on January 1st at 06:00 UTC.
    """
    if await should_run_update(lambda: asyncio.run(get_stars_for_mythology_update())):
        deployment = Deployment.build_from_flow(
            flow=update_star_mythology_flow,
            name="Update Star Mythology (every year)",
            schedule=CronSchedule(cron="0 6 1 1 *"),  # Runs every Jan 1st at 06:00 UTC
            work_queue_name="default",
        )
        deployment.apply()
        logger.info("Deployment applied: mythology update scheduled.")
    else:
        logger.info("No mythology updates required. Deployment skipped.")


if __name__ == "__main__":
    asyncio.run(apply_deployment())

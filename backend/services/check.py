import asyncio
from backend.services.simbad_api import fetch_star_data

async def test():
    result = await fetch_star_data("Antares")
    print(result)

asyncio.run(test())



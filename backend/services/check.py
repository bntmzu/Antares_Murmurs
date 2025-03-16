import asyncio
from backend.services.simbad_api import fetch_star_from_simbad

async def test():
    print(await fetch_star_from_simbad("Antares"))
    print(await fetch_star_from_simbad("Sirius"))
    print(await fetch_star_from_simbad("Betelgeuse"))
    print(await fetch_star_from_simbad("NonexistentStar"))

asyncio.run(test())


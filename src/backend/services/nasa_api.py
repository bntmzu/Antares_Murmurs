import httpx
from src.backend.config.settings import settings
from src.backend.services.star_constellation import get_star_constellation

NASA_API_KEY = settings.NASA_API_KEY
NASA_CATALOG_URL = (
    "https://exoplanetarchive.ipac.caltech.edu/cgi-bin/nstedAPI/nph-nstedAPI"
)


async def fetch_star_data(star_name: str):
    """
    Fetches star data from NASA's Exoplanet Archive and enriches it with constellation information.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(
            NASA_CATALOG_URL,
            params={"api_key": NASA_API_KEY, "table": "exoplanets", "format": "json"},
        )
        if response.status_code != 200:
            return None

        data = response.json()
        for star in data:
            if star_name.lower() in star["pl_hostname"].lower():
                constellation = await get_star_constellation(star_name)
                return {
                    "name": star["pl_hostname"],
                    "temperature": star.get("st_teff", None),
                    "distance_lightyears": star.get("st_dist", None),
                    "spectral_type": star.get("st_spectype", None),
                    "magnitude": star.get("st_optmag", None),
                    "constellation": constellation,
                }
        return None

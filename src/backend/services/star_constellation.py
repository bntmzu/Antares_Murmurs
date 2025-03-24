import openai
import httpx
from src.backend.config.settings import settings

openai.api_key = settings.OPENAI_API_KEY

SIMBAD_API_URL = "https://simbad.u-strasbg.fr/simbad/sim-id?output.format=json&Ident="


async def get_constellation_from_simbad(star_name: str):
    """
    Fetches the constellation of a star from the SIMBAD astronomical database.
    """
    async with httpx.AsyncClient() as client:
        response = await client.get(SIMBAD_API_URL + star_name)
        if response.status_code == 200:
            data = response.json()
            if "MAIN_ID" in data and "constellation" in data:
                return data["constellation"]
    return None


async def get_constellation_with_ai(star_name: str):
    """
    Uses GPT-4 to determine the constellation of a given star if it's not found in SIMBAD.
    """
    prompt = f"""
    You are an expert in astronomy. Determine the constellation where the star "{star_name}" is located. 
    Respond with only the name of the constellation.
    """

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=20,
        temperature=0.5,
    )

    return response["choices"][0]["message"]["content"].strip()


async def get_star_constellation(star_name: str):
    """
    Tries to get a star's constellation from SIMBAD first, then falls back to AI.
    """
    constellation = await get_constellation_from_simbad(star_name)

    if not constellation:
        constellation = await get_constellation_with_ai(star_name)

    return constellation if constellation else "Unknown"

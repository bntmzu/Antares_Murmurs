import aiohttp
import logging
import re
import json
from src.backend.core.database import get_session
from src.backend.models.star import Star
from src.backend.services.redis_client import redis_client
from sqlalchemy.future import select

# Enable logging
logging.basicConfig(level=logging.INFO)

# SIMBAD API URLs
SIMBAD_SCRIPT_URL = "https://simbad.u-strasbg.fr/simbad/sim-script"
SIMBAD_ID_URL = "https://simbad.u-strasbg.fr/simbad/sim-id"

# Spectral class temperature mapping
SPECTRAL_TEMPERATURES = {
    "O": (30000, 50000),
    "B": (10000, 30000),
    "A": (7500, 10000),
    "F": (6000, 7500),
    "G": (5200, 6000),
    "K": (3700, 5200),
    "M": (2500, 3700),
}

# Spectral class color mapping
SPECTRAL_COLORS = {
    "O": "Blue",
    "B": "Blue-white",
    "A": "White",
    "F": "Yellow-white",
    "G": "Yellow",
    "K": "Orange",
    "M": "Red",
}

# Luminosity class descriptions
LUMINOSITY_ESTIMATES = {
    "Ia": "Hypergiant",
    "Iab": "Bright supergiant",
    "Ib": "Supergiant",
    "II": "Bright giant",
    "III": "Giant",
    "IV": "Subgiant",
    "V": "Main sequence",
    "VI": "Subdwarf",
    "VII": "White dwarf",
}


async def query_simbad(star_name: str) -> dict | None:
    """
    Fetches star data from SIMBAD using sim-script and parses the response.
    """
    logging.info(f"Sending request to SIMBAD for {star_name}")
    script = f"""
    output console=off
    query id {star_name}
    """
    async with aiohttp.ClientSession() as session:
        async with session.post(SIMBAD_SCRIPT_URL, data={"script": script}) as response:
            logging.info(f"SIMBAD response status: {response.status}")
            text = await response.text()
            if response.status == 200:
                return parse_simbad_response(text)
            logging.warning(f"SIMBAD returned status {response.status} for {star_name}")
            return None


def parse_simbad_response(response_text: str) -> dict:
    """
    Parses SIMBAD text response and extracts relevant data.
    """
    return {
        "main_id": extract_value(
            r"typed ident:\s+(.+)", response_text, default="Unknown"
        ),
        "coordinates": extract_value(
            r"coord\s+:\s+([\d\s.-]+)\s+\([\w\s]+\)", response_text
        ),
        "spectral_type": extract_value(r"Spectral type:\s+([\w.-]+)", response_text),
        "visual_magnitude": extract_float(
            r"flux:\s+V \(Vega\)\s+([\d.-]+)", response_text
        ),
        "parallax": extract_float(r"parallax:\s+([\d.-]+)", response_text),
    }


def extract_value(pattern: str, text: str, default: str | None = None) -> str | None:
    match = re.search(pattern, text)
    return match.group(1).strip() if match else default


def extract_float(pattern: str, text: str) -> float | None:
    value = extract_value(pattern, text)
    return float(value) if value else None


def parse_spectral_type(spectral_type: str | None):
    """Extracts base class, subclass, and luminosity class from spectral type."""
    if not spectral_type:
        return None, None, None
    match = re.match(
        r"([OBAFGKM])([\d.]+)?(Iab|Ia|Ib|II|III|IV|V|VI|VII)?", spectral_type
    )
    if not match:
        return None, None, None
    base_class = match.group(1)
    subclass = float(match.group(2)) if match.group(2) else 5
    luminosity_class = match.group(3) if match.group(3) else "V"
    return base_class, subclass, luminosity_class


def estimate_temperature_from_spectral_type(spectral_type: str | None) -> int | None:
    base_class, subclass, _ = parse_spectral_type(spectral_type)
    if not base_class:
        return None
    temp_min, temp_max = SPECTRAL_TEMPERATURES.get(base_class, (None, None))
    if temp_min is None:
        return None
    return int(temp_min + (temp_max - temp_min) * (1 - subclass / 9))


def determine_star_color(spectral_type: str | None) -> str | None:
    base_class, _, _ = parse_spectral_type(spectral_type)
    return SPECTRAL_COLORS.get(base_class, "Unknown")


def estimate_luminosity_class(spectral_type: str | None) -> str | None:
    _, _, luminosity_class = parse_spectral_type(spectral_type)
    return LUMINOSITY_ESTIMATES.get(luminosity_class, "Unknown")


def calculate_distance(parallax: float | None) -> float | None:
    if parallax is None or parallax <= 0:
        return None
    return round((1000 / parallax) * 3.26156, 2)


def is_valid_star(star_data: dict) -> bool:
    spectral_type = star_data.get("spectral_type", "")
    magnitude = star_data.get("visual_magnitude")
    parallax = star_data.get("parallax")

    base_class, _, _ = parse_spectral_type(spectral_type)

    # Filters
    if base_class not in ["O", "B", "A", "F", "G", "K", "M"]:
        return False
    if magnitude is None or magnitude > 7:
        return False
    if parallax is None or parallax <= 0:
        return False

    return True


async def fetch_star_data(star_name: str) -> dict:
    """
    Fetches detailed star data from SIMBAD, caches it in Redis, and stores in PostgreSQL if valid.
    """
    # Check Redis cache first
    cached_data = await redis_client.get(f"star:{star_name}")
    if cached_data:
        logging.info(f"✅ Returning cached data for {star_name}")
        return json.loads(cached_data)

    logging.info(f"Fetching data for {star_name}")
    data = await query_simbad(star_name)
    if not data:
        return {"error": f"Star '{star_name}' not found in SIMBAD."}

    # Process data
    star_data = {
        "name": data["main_id"],
        "coordinates": data.get("coordinates"),
        "spectral_type": data.get("spectral_type"),
        "visual_magnitude": data.get("visual_magnitude"),
        "parallax": data.get("parallax"),
        "estimated_temperature": estimate_temperature_from_spectral_type(
            data.get("spectral_type")
        ),
        "color": determine_star_color(data.get("spectral_type")),
        "luminosity_class": estimate_luminosity_class(data.get("spectral_type")),
        "distance_light_years": calculate_distance(data.get("parallax")),
    }

    # Save to Redis cache
    await redis_client.set(
        f"star:{star_name}", json.dumps(star_data), ex=2592000
    )  # Cache for month

    # Store in PostgreSQL
    async with get_session() as session:
        existing_star = await session.execute(
            select(Star).where(Star.name == star_name)
        )
        existing_star = existing_star.scalars().first()

        if not existing_star:
            new_star = Star(**star_data)
            session.add(new_star)
            await session.commit()
            logging.info(f"✅ Star {star_name} added to database.")

    return star_data

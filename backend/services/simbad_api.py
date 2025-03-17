import aiohttp
import logging
import re

# Enable logging
logging.basicConfig(level=logging.INFO)

SIMBAD_SCRIPT_URL = "https://simbad.u-strasbg.fr/simbad/sim-script"
SIMBAD_ID_URL = "https://simbad.u-strasbg.fr/simbad/sim-id"

async def query_simbad(star_name: str) -> dict | None:
    """
    Fetches star data from SIMBAD using sim-script and parses the response.
    """
    logging.info(f" Sending request to SIMBAD for {star_name}")

    script = f"""
    output console=off
    query id {star_name}
    """

    async with aiohttp.ClientSession() as session:
        async with session.post(SIMBAD_SCRIPT_URL, data={"script": script}) as response:
            logging.info(f"📡 SIMBAD response status: {response.status}")
            text = await response.text()
            logging.debug(f"📜 Raw SIMBAD response:\n{text}")

            if response.status == 200:
                parsed_data = parse_simbad_response(text)
                logging.info(f"✅ Parsed SIMBAD data: {parsed_data}")
                return parsed_data
            logging.warning(f"⚠️ SIMBAD returned status {response.status} for {star_name}")
            return None

async def query_coordinates(star_name: str) -> str | None:
    """
    Fetches coordinates using SIMBAD's sim-id endpoint.
    """
    logging.info(f"🔎 Fetching coordinates for {star_name} using sim-id API")
    params = {"Ident": star_name, "output.format": "ASCII"}

    async with aiohttp.ClientSession() as session:
        async with session.get(SIMBAD_ID_URL, params=params) as response:
            if response.status == 200:
                return extract_coordinates(await response.text())
            logging.warning(f"Failed to fetch coordinates from sim-id for {star_name}")
            return None

def parse_simbad_response(response_text: str) -> dict:
    """
    Parses SIMBAD text response and extracts relevant data.
    """
    logging.info("🔍 Parsing SIMBAD response")

    parsed_data = {
        "main_id": extract_value(r"typed ident:\s+(.+)", response_text, default="Unknown"),
        "coordinates": extract_value(r"coord\s+:\s+([\d\s.-]+)\s+\([\w\s]+\)", response_text),
        "spectral_type": extract_value(r"Spectral type:\s+([\w.-]+)", response_text),
        "visual_magnitude": extract_float(r"flux:\s+V \(Vega\)\s+([\d.-]+)", response_text),
        "parallax": extract_float(r"parallax:\s+([\d.-]+)", response_text),
    }

    logging.info(f"✅ Parsed data: {parsed_data}")
    return parsed_data

def extract_value(pattern: str, text: str, default: str | None = None) -> str | None:
    """
    Extracts a value from text using a regex pattern.
    """
    match = re.search(pattern, text)
    return match.group(1).strip() if match else default

def extract_float(pattern: str, text: str) -> float | None:
    """
    Extracts a float value from text using a regex pattern.
    """
    value = extract_value(pattern, text)
    return float(value) if value else None

def extract_coordinates(response_text: str) -> str | None:
    """
    Extracts coordinates from SIMBAD's sim-id ASCII response.
    """
    return extract_value(r"(\d{2} \d{2} \d{2}\.\d+)\s+([\+\-]\d{2} \d{2} \d{2}\.\d+)", response_text)

async def resolve_star_name(star_name: str) -> str:
    """
    Resolves the official star name from SIMBAD.
    """
    logging.info(f"🔄 Resolving star name for {star_name}")

    data = await query_simbad(star_name)
    resolved_name = data["main_id"] if data and data["main_id"] != "Unknown" else star_name
    logging.info(f"Resolved {star_name} to {resolved_name}")
    return resolved_name

logging.info("🚀 Запуск get_star_info()")

async def fetch_star_data(star_name: str) -> dict:
    """
    Fetches detailed star data from SIMBAD.
    """
    logging.info(f"🌠 Fetching data for {star_name}")
    print(f"🔎 Fetching star data for {star_name}")

    resolved_name = await resolve_star_name(star_name)
    data = await query_simbad(resolved_name)

    if not data:
        logging.error(f"❌ No data found for {resolved_name}")
        return {"error": f"Star '{resolved_name}' not found in SIMBAD."}

    if not data.get("coordinates"):
        logging.warning(f"Coordinates missing for {resolved_name}, trying alternative query.")
        data["coordinates"] = await query_coordinates(resolved_name)

    data["estimated_temperature"] = estimate_temperature_from_spectral_type(data.get("spectral_type"))

    return {
        "name": resolved_name,
        "coordinates": data.get("coordinates"),
        "spectral_type": data.get("spectral_type"),
        "visual_magnitude": data.get("visual_magnitude"),
        "parallax": data.get("parallax"),
        "estimated_temperature": data["estimated_temperature"],
    }

# Global spectral temperature mapping
SPECTRAL_TEMPERATURES = {
    "O": (30000, 50000),
    "B": (10000, 30000),
    "A": (7500, 10000),
    "F": (6000, 7500),
    "G": (5200, 6000),
    "K": (3700, 5200),
    "M": (2500, 3700),
}

def estimate_temperature_from_spectral_type(spectral_type: str | None) -> int | None:
    """
    Estimates star temperature based on spectral classification.
    Supports ranges like "M1-M2Ia-Iab".
    """
    if not spectral_type:
        return None

    if "-" in spectral_type:
        base_classes = re.findall(r"[OBAFGKM]\d?", spectral_type)
        if len(base_classes) == 2:
            temp1 = estimate_temperature_from_spectral_type(base_classes[0])
            temp2 = estimate_temperature_from_spectral_type(base_classes[1])
            return (temp1 + temp2) // 2 if temp1 and temp2 else None

    base_class = spectral_type[0]
    subclass = spectral_type[1] if len(spectral_type) > 1 and spectral_type[1].isdigit() else "5"

    if base_class in SPECTRAL_TEMPERATURES:
        temp_min, temp_max = SPECTRAL_TEMPERATURES[base_class]
        subclass_fraction = int(subclass) / 9
        estimated_temp = int(temp_min + (temp_max - temp_min) * (1 - subclass_fraction))
        return estimated_temp

    return None



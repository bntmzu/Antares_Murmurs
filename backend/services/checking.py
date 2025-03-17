import aiohttp
import asyncio
import logging
import re

# Enable logging
logging.basicConfig(level=logging.INFO)

SIMBAD_SCRIPT_URL = "http://simbad.u-strasbg.fr/simbad/sim-script"
SIMBAD_ID_URL = "http://simbad.u-strasbg.fr/simbad/sim-id"

async def query_simbad(star_name: str):
    """
    Asynchronously fetches star data from SIMBAD using sim-script.
    Parses text response manually.
    """
    script = f"""
    output console=off
    query id {star_name}
    """

    async with aiohttp.ClientSession() as session:
        async with session.post(SIMBAD_SCRIPT_URL, data={"script": script}) as response:
            if response.status == 200:
                text = await response.text()
                return parse_simbad_response(text)
            else:
                logging.warning(f"⚠️ SIMBAD returned status {response.status} for {star_name}")
                return None

async def query_coordinates(star_name: str):
    """
    Fetches coordinates using SIMBAD's sim-id endpoint.
    """
    params = {
        "Ident": star_name,
        "output.format": "ASCII"
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(SIMBAD_ID_URL, params=params) as response:
            if response.status == 200:
                text = await response.text()
                return extract_coordinates(text)
            else:
                logging.warning(f"⚠️ Failed to fetch coordinates from sim-id for {star_name}")
                return None

def parse_simbad_response(response_text: str):
    """
    Parses the raw SIMBAD text response and extracts relevant data.
    """
    data = {}

    # Найти основное имя объекта (обычно в typed ident)
    main_id_match = re.search(r"typed ident:\s+(.+)", response_text)
    if main_id_match:
        data["main_id"] = main_id_match.group(1).strip()
    else:
        logging.warning("⚠️ Could not find main ID, using fallback.")
        data["main_id"] = "Unknown"

    # Найти координаты (форматы бывают разные)
    coord_match = re.search(r"coord\s+:\s+([\d\s\.\-]+)\s+\([\w\s]+\)", response_text)
    if coord_match:
        data["coordinates"] = coord_match.group(1).strip()
    else:
        data["coordinates"] = None  # Если координат нет, вернем None

    # Найти спектральный тип
    spectral_type_match = re.search(r"Spectral type:\s+([\w\.\-]+)", response_text)
    if spectral_type_match:
        data["spectral_type"] = spectral_type_match.group(1).strip()

    # Найти видимую звездную величину (V)
    magnitude_match = re.search(r"flux:\s+V \(Vega\)\s+([\d\.\-]+)", response_text)
    if magnitude_match:
        data["visual_magnitude"] = float(magnitude_match.group(1).strip())

    # Найти параллакс
    parallax_match = re.search(r"parallax:\s+([\d\.\-]+)", response_text)
    if parallax_match:
        data["parallax"] = float(parallax_match.group(1).strip())

    return data

def extract_coordinates(response_text: str):
    """
    Extracts coordinates from SIMBAD's sim-id ASCII response.
    """
    match = re.search(r"(\d{2} \d{2} \d{2}\.\d+)\s+([\+\-]\d{2} \d{2} \d{2}\.\d+)", response_text)
    if match:
        return f"{match.group(1)} {match.group(2)}"
    return None

async def resolve_star_name(star_name: str):
    """
    Tries to resolve the official star name from SIMBAD.
    """
    data = await query_simbad(star_name)

    if not data or "main_id" not in data or data["main_id"] == "Unknown":
        logging.error(f"❌ No data found for {star_name}")
        return star_name

    resolved_name = data["main_id"]
    logging.info(f"✅ Resolved {star_name} to {resolved_name}")
    return resolved_name

async def fetch_star_data(star_name: str):
    """
    Asynchronously fetches star data using SIMBAD.
    """
    resolved_name = await resolve_star_name(star_name)
    data = await query_simbad(resolved_name)

    if not data:
        return {"error": f"Star '{resolved_name}' not found in SIMBAD."}

    # Если координаты отсутствуют, попробуем второй метод
    if not data.get("coordinates"):
        logging.warning(f"⚠️ Coordinates missing for {resolved_name}, trying alternative query.")
        alternative_coords = await query_coordinates(resolved_name)
        data["coordinates"] = alternative_coords

    # Вычислить температуру
    spectral_type = data.get("spectral_type")
    estimated_temp = estimate_temperature_from_spectral_type(spectral_type) if spectral_type else None

    # Финальный объект star_info
    star_info = {
        "name": resolved_name,
        "coordinates": data.get("coordinates"),
        "spectral_type": spectral_type,
        "visual_magnitude": data.get("visual_magnitude"),
        "parallax": data.get("parallax"),
        "estimated_temperature": estimated_temp,
    }

    return star_info

def estimate_temperature_from_spectral_type(spectral_type: str):
    """
    More accurate temperature estimation based on spectral classification.
    Supports ranges like "M1-M2Ia-Iab".
    """
    spectral_temperatures = {
        "O": (30000, 50000),
        "B": (10000, 30000),
        "A": (7500, 10000),
        "F": (6000, 7500),
        "G": (5200, 6000),
        "K": (3700, 5200),
        "M": (2500, 3700),
    }

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

    if base_class in spectral_temperatures:
        temp_min, temp_max = spectral_temperatures[base_class]
        subclass_fraction = int(subclass) / 9
        estimated_temp = int(temp_min + (temp_max - temp_min) * (1 - subclass_fraction))
        return estimated_temp

    return None

async def main():
    # Пример параллельных запросов
    star_names = ["Antares", "Betelgeuse", "Sirius"]
    tasks = [fetch_star_data(name) for name in star_names]

    results = await asyncio.gather(*tasks)

    for star, result in zip(star_names, results):
        print(f"\n⭐ {star}:\n{result}")

if __name__ == "__main__":
    asyncio.run(main())

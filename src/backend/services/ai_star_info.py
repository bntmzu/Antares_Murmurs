import openai
import logging
import json
from src.backend.config.settings import settings
from src.backend.services.redis_client import redis_client

openai.api_key = settings.OPENAI_API_KEY
logger = logging.getLogger(__name__)

async def analyze_star_mythology(star_name: str, star_data: dict):
    """
    Uses GPT-4 to analyze the mythology of a star.
    """

    if not star_data:
        return {"error": "Star data not found in SIMBAD API."}

    cache_key = f"mythology:{star_name}"
    cached_data = await redis_client.get(cache_key)

    if cached_data:
        logger.info(f"Cache hit for mythology of {star_name}")
        return json.loads(cached_data)

    prompt = f"""
    You are an expert in astronomy, mythology, and poetic writing. Your task is to create a concise yet poetic 
    and emotionally profound description of the star "{star_name}," 
    analyzing its historical and mythological significance.

         **Structure of the response:**
        - **Mythological meaning**: Use only real historical and mythological sources.
          If the star has no known mythology, explicitly state: 
          "There are no direct mythological references to {star_name}."
        - **Emotional and symbolic representation**: What human emotions, strengths,
         or challenges does this star symbolize?
        - **If the star were a person**: What kind of personality or presence would it have?
        - **A message for the user:** If this star could speak, what would it say to someone 
        who feels emotionally connected to it? The message should be poetic, 
        inspiring, and relevant to the star’s nature.
        
         **Output Format:**
        - **Mythological Meaning**: (Only real myths; if none exist, say so)
        - **Emotional and Symbolic Representation**: (Based only on historical symbolism)
        - **If the Star Were a Person**: (Characterization based on its traits)
        - **Message for the User**: (A poetic but meaningful reflection)

         **Style Guidelines:**
        - Balance logic and artistic expression (max 3 sentences per section).
        - Avoid overly poetic phrasing, but make it engaging.
        - Keep the text concise and meaningful.
        - Do NOT create fake scientific facts—use only the provided data.

    """

    client = openai.AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=300,
        temperature=0.6,
        top_p=0.9,
        frequency_penalty=0.2,
        presence_penalty=0.3
    )

    mythology_description = response.choices[0].message.content.strip()
    mythology_description = mythology_description.replace("\n-", "").strip()


    def format_mythology_response(mythology_text: str):
        sections = mythology_text.split("**")
        mythology = {}

        for i in range(1, len(sections), 2):
            key = sections[i].strip().lower().replace(" ", "_").replace(":", "")
            value = sections[i + 1].strip() if i + 1 < len(sections) else ""

            if value.startswith(": "):
                value = value[2:].strip()

            mythology[key] = value

        return mythology

    formatted_mythology = format_mythology_response(mythology_description)

    # Cache the response for 1 year (365 days)
    await redis_client.set(cache_key, json.dumps({**star_data, "mythology": formatted_mythology}), expire=31536000)

    logger.info(f" Mythology for {star_name} cached for 1 year")

    return {**star_data, "mythology": formatted_mythology}

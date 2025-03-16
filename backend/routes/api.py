from fastapi import APIRouter, HTTPException
from backend.services.simbad_api import fetch_star_from_simbad
from backend.services.ai_star_info import analyze_star_mythology

router = APIRouter()

@router.get("/star_info/")
async def get_star_info(star_name: str):
    """
    API endpoint to fetch real astronomical data and AI-generated mythology for a given star.
    """
    try:
        # 1️⃣ Fetch real star data from NASA API
        star_data = await fetch_star_from_simbad(star_name)

        if not star_data:
            raise HTTPException(status_code=404, detail="Star data not found.")

        # 2️⃣ Use GPT-4 to analyze mythology
        mythology_description = await analyze_star_mythology(star_name)

        # 3️⃣ Merge real data with AI-generated mythology
        enriched_star_info = {**star_data, "mythology": mythology_description}

        return enriched_star_info

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

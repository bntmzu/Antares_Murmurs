from fastapi import APIRouter, HTTPException
from src.backend.services.simbad_api import fetch_star_data
from src.backend.services.ai_star_info import analyze_star_mythology
import logging


router = APIRouter()

@router.get("/star_info/")
async def get_star_info(star_name: str):
    """
    API endpoint to fetch real astronomical data and AI-generated mythology for a given star.
    """
    logging.info(f"🟡 API called with star_name: {star_name}")

    try:
        # 1️⃣ Fetch real star data from SIMBAD
        star_data = await fetch_star_data(star_name)

        if not star_data:
            raise HTTPException(status_code=404, detail="Star data not found.")

        enriched_star_info = await analyze_star_mythology(star_name, star_data)

        return enriched_star_info

    except Exception as e:
        logging.error(f"❌ API Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

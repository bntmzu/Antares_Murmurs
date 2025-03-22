from fastapi import FastAPI
from contextlib import asynccontextmanager
from src.backend.routes import api
from src.backend.services.redis_client import redis_client
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")
logging.info("Logging enabled")

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler for FastAPI (replaces @app.on_event)"""
    try:
        await redis_client.connect()
        logging.info("✅ Redis connection established.")
    except Exception as e:
        logging.error(f"❌ Redis startup error: {e}")

    yield  # This is where the app runs

    try:
        await redis_client.close()
        logging.info("✅ Redis connection closed.")
    except Exception as e:
        logging.error(f"❌ Redis shutdown error: {e}")

app = FastAPI(title="Antares Murmurs", lifespan=lifespan)
app.include_router(api.router)

# Log available routes
for route in app.routes:
    logging.info(f" Available route: {getattr(route, 'path', 'Unknown')}")

@app.get("/")
async def root():
    return {"message": "Welcome to Antares Murmurs!"}

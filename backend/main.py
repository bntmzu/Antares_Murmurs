from fastapi import FastAPI
from backend.routes import api

app = FastAPI(title="Antares Murmurs")

app.include_router(api.router)

@app.get("/")
async def root():
    return {"message": "Welcome to Antares Murmurs!"}

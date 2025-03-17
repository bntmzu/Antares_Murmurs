from fastapi import FastAPI
from backend.routes import api
import logging

logging.basicConfig(level=logging.DEBUG)  # Настроить уровень логов
logging.info("ℹ️ Логирование включено")

app = FastAPI(title="Antares Murmurs")

print("✅ Подключаем роуты API...")
app.include_router(api.router)

for route in app.routes:
    print(f"🌍 Доступный маршрут: {route.path}")

@app.get("/")
async def root():
    return {"message": "Welcome to Antares Murmurs!"}
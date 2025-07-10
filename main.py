import os
import time
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from routers import auth, users, products

# --- Настройка лимитера для защиты от brute-force ---
limiter = Limiter(key_func=get_remote_address, default_limits=["100 per minute"])

# --- Инициализация приложения FastAPI ---
app = FastAPI(title="TechMart API")

# --- Подключение обработчика исключений для лимитера ---
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# --- Middleware для логирования запросов (опционально) ---
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response

# --- Подключение роутеров ---
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(products.router)

@app.on_event("startup")
async def startup_event():
    """Проверяем наличие файлов БД при старте и создаем их, если их нет."""
    if not os.path.exists("database/users.json"):
        with open("database/users.json", "w") as f:
            f.write("[]")
    if not os.path.exists("database/products.json"):
        with open("database/products.json", "w") as f:
            f.write("[]")
    if not os.path.exists("database/categories.json"):
        with open("database/categories.json", "w") as f:
            f.write("[]")

@app.get("/", tags=["Root"])
async def read_root():
    return {"message": "Welcome to the TechMart API!"}

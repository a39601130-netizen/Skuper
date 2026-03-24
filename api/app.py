"""FastAPI application with SPA fallback."""

import os
import time
from pathlib import Path
from collections import defaultdict
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse, Response

from api.routers import health, transactions, accounts, categories, stats, workouts, exercises, advisor, recurring, sync

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
IS_PRODUCTION = os.getenv("ENVIRONMENT", "production") == "production"

# Simple in-memory rate limiter
_rate_limit_store: dict[str, list[float]] = defaultdict(list)
RATE_LIMIT = 100  # requests
RATE_WINDOW = 60  # seconds


def create_app() -> FastAPI:
    app = FastAPI(
        title="Budget Bot Mini App",
        docs_url=None if IS_PRODUCTION else "/api/docs",
        openapi_url=None if IS_PRODUCTION else "/api/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "https://budget-bot.duckdns.org",
            "http://localhost:5173",
            "http://localhost:8000",
        ],
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Content-Type", "X-Telegram-Init-Data"],
    )

    # Rate limiting middleware
    @app.middleware("http")
    async def rate_limit_middleware(request: Request, call_next):
        if request.url.path.startswith("/api/"):
            client_ip = request.client.host if request.client else "unknown"
            now = time.time()
            # Clean old entries
            _rate_limit_store[client_ip] = [
                t for t in _rate_limit_store[client_ip] if now - t < RATE_WINDOW
            ]
            if len(_rate_limit_store[client_ip]) >= RATE_LIMIT:
                return JSONResponse(
                    {"detail": "Too many requests"},
                    status_code=429,
                    headers={"Retry-After": str(RATE_WINDOW)},
                )
            _rate_limit_store[client_ip].append(now)
        return await call_next(request)

    # API роутеры
    app.include_router(health.router)
    app.include_router(transactions.router)
    app.include_router(accounts.router)
    app.include_router(categories.router)
    app.include_router(stats.router)
    app.include_router(workouts.router)
    app.include_router(exercises.router)
    app.include_router(advisor.router)
    app.include_router(recurring.router)
    app.include_router(sync.router)

    # SPA fallback — раздаём собранный React
    if os.path.isdir(FRONTEND_DIR):
        assets_dir = os.path.join(FRONTEND_DIR, "assets")
        if os.path.isdir(assets_dir):
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            file_path = os.path.join(FRONTEND_DIR, full_path)
            # Защита от path traversal
            if not Path(file_path).resolve().is_relative_to(Path(FRONTEND_DIR).resolve()):
                return JSONResponse({"detail": "Forbidden"}, status_code=403)
            if os.path.isfile(file_path):
                return FileResponse(file_path)
            index = os.path.join(FRONTEND_DIR, "index.html")
            if os.path.isfile(index):
                return FileResponse(
                    index,
                    headers={
                        "Cache-Control": "no-cache, no-store, must-revalidate",
                        "Pragma": "no-cache",
                        "Expires": "0",
                    },
                )
            return JSONResponse({"detail": "Frontend not built"}, status_code=404)

    return app

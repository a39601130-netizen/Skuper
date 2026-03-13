"""FastAPI application with SPA fallback."""

import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse

from api.routers import health, transactions, accounts, categories, stats, workouts, exercises, advisor

FRONTEND_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")


def create_app() -> FastAPI:
    app = FastAPI(
        title="Budget Bot Mini App",
        docs_url="/api/docs",
        openapi_url="/api/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # API роутеры
    app.include_router(health.router)
    app.include_router(transactions.router)
    app.include_router(accounts.router)
    app.include_router(categories.router)
    app.include_router(stats.router)
    app.include_router(workouts.router)
    app.include_router(exercises.router)
    app.include_router(advisor.router)

    # SPA fallback — раздаём собранный React
    if os.path.isdir(FRONTEND_DIR):
        assets_dir = os.path.join(FRONTEND_DIR, "assets")
        if os.path.isdir(assets_dir):
            app.mount("/assets", StaticFiles(directory=assets_dir), name="assets")

        @app.get("/{full_path:path}")
        async def serve_spa(full_path: str):
            file_path = os.path.join(FRONTEND_DIR, full_path)
            if os.path.isfile(file_path):
                return FileResponse(file_path)
            index = os.path.join(FRONTEND_DIR, "index.html")
            if os.path.isfile(index):
                return FileResponse(index)
            return JSONResponse({"detail": "Frontend not built"}, status_code=404)

    return app

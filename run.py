"""Entry point: runs FastAPI (Mini App) + Telegram bot concurrently."""

import asyncio
import logging
import uvicorn

import config
from api.app import create_app

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = create_app()


async def main():
    # Валидация обязательных переменных окружения
    missing = []
    if not config.TELEGRAM_BOT_TOKEN:
        missing.append("TELEGRAM_BOT_TOKEN")
    if not config.TELEGRAM_USER_ID:
        missing.append("TELEGRAM_USER_ID")
    if missing:
        logger.error("Отсутствуют переменные окружения: %s", ", ".join(missing))
        return

    # Инициализируем PostgreSQL
    from db.database import init_db
    from db.seed import seed_db
    await init_db()
    await seed_db()
    logger.info("PostgreSQL инициализирован")

    # Инициализируем Google Sheets (опционально)
    sheets_ok = False
    try:
        from services.sheets import get_sheets_service
        sheets = get_sheets_service()
        sheets.ensure_exchange_type_exists()
        sheets_ok = True
    except Exception as e:
        logger.warning(f"Google Sheets init: {e}")

    # Создаём Telegram bot application
    from main import create_application
    from telegram import Update

    bot_app = create_application()

    # Запускаем FastAPI
    uvicorn_config = uvicorn.Config(
        app, host="0.0.0.0", port=8000, log_level="info"
    )
    server = uvicorn.Server(uvicorn_config)

    # Запускаем бот polling
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling(
        allowed_updates=Update.ALL_TYPES,
        drop_pending_updates=True,
    )

    logger.info("🤖 Bot polling started")
    logger.info("🌐 FastAPI server starting on :8000")

    # Запускаем периодическую синхронизацию Sheets ↔ PG
    sync_task = None
    if sheets_ok:
        try:
            from services.sync import periodic_sync_task
            sync_task = asyncio.create_task(periodic_sync_task(interval_minutes=5))
            logger.info("🔄 Sheets sync task started (every 5 min)")
        except Exception as e:
            logger.warning(f"Sheets sync task failed to start: {e}")

    try:
        await server.serve()
    finally:
        logger.info("Shutting down...")
        if sync_task:
            sync_task.cancel()
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

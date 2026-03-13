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
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не задан!")
        return

    # Инициализируем PostgreSQL
    from db.database import init_db
    from db.seed import seed_db
    await init_db()
    await seed_db()
    logger.info("PostgreSQL инициализирован")

    # Инициализируем Google Sheets (опционально)
    try:
        from services.sheets import get_sheets_service
        sheets = get_sheets_service()
        sheets.ensure_exchange_type_exists()
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

    try:
        await server.serve()
    finally:
        logger.info("Shutting down...")
        await bot_app.updater.stop()
        await bot_app.stop()
        await bot_app.shutdown()


if __name__ == "__main__":
    asyncio.run(main())

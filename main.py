"""
Life Manager Bot - Главный файл
Telegram бот: /start, /help, /backup
Всё остальное — через Mini App.

Запуск: python main.py
"""
import logging
import os
import sys
import atexit
from pathlib import Path
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
)
from telegram.error import NetworkError, TimedOut

import config

# Handlers
from bot.handlers.start import start_command, help_command
from bot.handlers.backup import (
    backup_command, backup_menu_callback,
    backup_type_callback, backup_month_callback
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def error_handler(update: object, context):
    """Глобальный обработчик ошибок"""
    error = context.error

    if isinstance(error, (NetworkError, TimedOut)):
        logger.warning(f"Сетевая ошибка: {error}")
        return

    logger.error(f"Ошибка: {error}", exc_info=True)

    if update and hasattr(update, 'effective_message'):
        try:
            await update.effective_message.reply_text(
                "❌ Произошла ошибка. Попробуй /start для перезапуска."
            )
        except Exception:
            pass


# ============================================
# БЛОКИРОВКА МНОЖЕСТВЕННОГО ЗАПУСКА
# ============================================

LOCK_FILE = Path(__file__).parent / "bot.lock"

def acquire_lock():
    """Создает файл блокировки для предотвращения множественного запуска"""
    if LOCK_FILE.exists():
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())

            if sys.platform == 'win32':
                import subprocess
                result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'],
                                      capture_output=True, text=True)
                if str(pid) in result.stdout:
                    logger.error(f"❌ Бот уже запущен (PID: {pid})")
                    logger.error("Завершите предыдущий экземпляр или удалите bot.lock")
                    sys.exit(1)
            else:
                try:
                    os.kill(pid, 0)
                    logger.error(f"❌ Бот уже запущен (PID: {pid})")
                    logger.error("Завершите предыдущий экземпляр или удалите bot.lock")
                    sys.exit(1)
                except OSError:
                    pass

            LOCK_FILE.unlink()
        except (ValueError, FileNotFoundError):
            LOCK_FILE.unlink()

    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))

    logger.info(f"🔒 Блокировка создана (PID: {os.getpid()})")

def release_lock():
    """Удаляет файл блокировки при завершении"""
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
            logger.info("🔓 Блокировка снята")
    except Exception as e:
        logger.warning(f"Не удалось удалить файл блокировки: {e}")


# ============================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================

async def post_init(application):
    """Регистрация команд в меню Telegram после старта"""
    from telegram import BotCommand
    await application.bot.set_my_commands([
        BotCommand("start", "Открыть Mini App"),
        BotCommand("backup", "Бэкап в Google Sheets"),
        BotCommand("help", "Справка"),
    ])


def main():
    """Запуск бота"""
    acquire_lock()
    atexit.register(release_lock)

    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не задан в .env файле!")
        return

    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    _register_handlers(application)

    logger.info("🤖 Life Manager Bot запущен!")
    logger.info("📱 Режим: Mini App + /backup")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


def create_application():
    """Создаёт и возвращает Application (без запуска polling).
    Используется из run.py для параллельного запуска с FastAPI."""
    acquire_lock()
    atexit.register(release_lock)

    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).post_init(post_init).build()
    _register_handlers(application)
    return application


def _register_handlers(application):
    """Регистрирует все handlers на application."""
    # Команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("backup", backup_command))

    # Backup inline callbacks
    application.add_handler(CallbackQueryHandler(backup_menu_callback, pattern="^backup_menu$"))
    application.add_handler(CallbackQueryHandler(backup_type_callback, pattern="^backup_type_"))
    application.add_handler(CallbackQueryHandler(backup_month_callback, pattern="^backup_month_"))

    # Глобальный обработчик ошибок
    application.add_error_handler(error_handler)


if __name__ == "__main__":
    main()

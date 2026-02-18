"""
Обработчики отчетов
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.sheets import get_sheets_service
from utils.formatters import format_weekly_report
from utils.telegram_helpers import safe_edit_message
from bot.keyboards.menus import get_main_menu

logger = logging.getLogger(__name__)


async def _get_weekly_report_text() -> str:
    sheets = get_sheets_service()
    data = sheets.get_weekly_summary(days_back=7)
    return format_weekly_report(data)


async def weekly_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /weekly - еженедельный отчет"""
    try:
        report = await _get_weekly_report_text()
        await update.message.reply_text(report, parse_mode="Markdown", reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Ошибка при формировании отчета: {e}")
        await update.message.reply_text("❌ Ошибка при формировании отчета.", reply_markup=get_main_menu())


async def weekly_report_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback для кнопки недельного отчета"""
    query = update.callback_query
    await query.answer()
    try:
        report = await _get_weekly_report_text()
        await safe_edit_message(query, report, parse_mode="Markdown", reply_markup=get_main_menu())
    except Exception as e:
        logger.error(f"Ошибка при формировании отчета: {e}")
        await query.edit_message_text("❌ Ошибка при формировании отчета.", reply_markup=get_main_menu())


async def send_weekly_report(context: ContextTypes.DEFAULT_TYPE):
    """
    Автоматическая отправка еженедельного отчета
    Вызывается планировщиком по воскресеньям
    """
    try:
        chat_id = context.job.chat_id
        report = "🔔 **АВТОМАТИЧЕСКИЙ ЕЖЕНЕДЕЛЬНЫЙ ОТЧЕТ**\n\n" + await _get_weekly_report_text()
        await context.bot.send_message(
            chat_id=chat_id,
            text=report,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        logger.info(f"Отправлен еженедельный отчет пользователю {chat_id}")
    except Exception as e:
        logger.error(f"Ошибка отправки автоматического отчета: {e}")

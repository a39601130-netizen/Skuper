"""
Обработчики отчетов
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from services.sheets import get_sheets_service
from utils.formatters import format_weekly_report
from bot.keyboards.menus import get_main_menu

logger = logging.getLogger(__name__)


async def weekly_report_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /weekly - еженедельный отчет"""
    try:
        sheets = get_sheets_service()
        data = sheets.get_weekly_summary(days_back=7)

        report = format_weekly_report(data)

        await update.message.reply_text(
            report,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )

    except Exception as e:
        logger.error(f"Ошибка при формировании отчета: {e}")
        await update.message.reply_text(
            "❌ Ошибка при формировании отчета.",
            reply_markup=get_main_menu()
        )


async def weekly_report_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback для кнопки недельного отчета"""
    query = update.callback_query
    await query.answer()

    try:
        sheets = get_sheets_service()
        data = sheets.get_weekly_summary(days_back=7)

        report = format_weekly_report(data)

        await query.edit_message_text(
            report,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )

    except Exception as e:
        logger.error(f"Ошибка при формировании отчета: {e}")
        await query.edit_message_text(
            "❌ Ошибка при формировании отчета.",
            reply_markup=get_main_menu()
        )


async def send_weekly_report(context: ContextTypes.DEFAULT_TYPE):
    """
    Автоматическая отправка еженедельного отчета
    Вызывается планировщиком по воскресеньям
    """
    try:
        # Получаем chat_id из job.data
        chat_id = context.job.chat_id

        sheets = get_sheets_service()
        data = sheets.get_weekly_summary(days_back=7)

        report = "🔔 **АВТОМАТИЧЕСКИЙ ЕЖЕНЕДЕЛЬНЫЙ ОТЧЕТ**\n\n" + format_weekly_report(data)

        await context.bot.send_message(
            chat_id=chat_id,
            text=report,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )

        logger.info(f"Отправлен еженедельный отчет пользователю {chat_id}")

    except Exception as e:
        logger.error(f"Ошибка отправки автоматического отчета: {e}")

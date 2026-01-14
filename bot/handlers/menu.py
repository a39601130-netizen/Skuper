"""
Обработчики главного меню и навигации между модулями
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest

from bot.keyboards.main_menu import (
    get_main_menu,
    get_finance_menu,
    get_workout_menu,
    get_advisor_menu
)

logger = logging.getLogger(__name__)


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик callbacks главного меню"""
    query = update.callback_query
    
    try:
        await query.answer()
    except BadRequest as e:
        if "query is too old" in str(e).lower():
            logger.warning(f"Устаревший callback: {e}")
            return
        raise
    
    data = query.data
    
    try:
        if data == "menu_main":
            await query.edit_message_text(
                "🏠 **Главное меню**\n\nВыбери модуль:",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
        
        elif data == "module_finance":
            await query.edit_message_text(
                "💰 **ФИНАНСЫ**\n\nВыбери действие:",
                parse_mode="Markdown",
                reply_markup=get_finance_menu()
            )
        
        elif data == "module_workout":
            from bot.handlers.workout.session import workout_menu_callback
            await workout_menu_callback(update, context)
        
        elif data == "module_advisor":
            await query.edit_message_text(
                "🤖 **AI СОВЕТНИК**\n\n"
                "Выбери что проанализировать:",
                parse_mode="Markdown",
                reply_markup=get_advisor_menu()
            )
        
        elif data == "module_settings":
            await query.edit_message_text(
                "⚙️ **НАСТРОЙКИ**\n\n"
                "В разработке...\n\n"
                "Настройки можно изменить в Google Sheets.",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
    
    except BadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise

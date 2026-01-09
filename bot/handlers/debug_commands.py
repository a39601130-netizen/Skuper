"""
Команды для отладки и просмотра багов
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes
from utils.debug_logger import bug_tracker
from bot.keyboards.menus import get_main_menu

logger = logging.getLogger(__name__)


async def bugs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /bugs - показать последние нерешенные баги"""

    unresolved = bug_tracker.get_unresolved_bugs()

    if not unresolved:
        await update.message.reply_text(
            "✅ Нерешенных багов нет!",
            reply_markup=get_main_menu()
        )
        return

    response = f"🐛 **Нерешенные баги: {len(unresolved)}**\n\n"

    # Показываем последние 5 багов
    for i, bug in enumerate(unresolved[-5:], 1):
        response += f"**{i}. {bug['error_type']}**\n"
        response += f"📅 {bug['timestamp'][:19]}\n"
        response += f"🔧 Обработчик: `{bug.get('handler', 'N/A')}`\n"
        response += f"👤 User ID: {bug.get('user_id', 'N/A')}\n"
        response += f"💬 {bug['error_message'][:100]}\n\n"

    response += f"\n📂 Полные логи в: `logs/bugs.json`"

    await update.message.reply_text(
        response,
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )


async def clear_bugs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /clear_bugs - очистить решенные баги"""

    bug_tracker.clear_resolved()
    unresolved_count = len(bug_tracker.get_unresolved_bugs())

    await update.message.reply_text(
        f"🧹 Решенные баги удалены.\n\n"
        f"Осталось нерешенных: {unresolved_count}",
        reply_markup=get_main_menu()
    )

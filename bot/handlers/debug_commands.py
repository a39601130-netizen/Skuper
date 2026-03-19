"""
Команды для отладки и служебные команды
"""
import logging
import asyncio
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

    response = f"🐛 Нерешенные баги: {len(unresolved)}\n\n"

    # Показываем последние 5 багов
    for i, bug in enumerate(unresolved[-5:], 1):
        handler = str(bug.get('handler', 'N/A'))
        error_msg = str(bug.get('error_message', 'N/A'))[:100]

        response += f"{i}. {bug['error_type']}\n"
        response += f"📅 {bug['timestamp'][:19]}\n"
        response += f"🔧 Обработчик: {handler}\n"
        response += f"👤 User ID: {bug.get('user_id', 'N/A')}\n"
        response += f"💬 {error_msg}\n\n"

    response += f"\n📂 Полные логи в: logs/bugs.json"

    await update.message.reply_text(
        response,
        parse_mode=None,
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


async def sync_balances_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /sync_balances - обновить балансы счетов из Google Sheets"""

    msg = await update.message.reply_text("🔄 Загружаю балансы из Google Sheets...")

    try:
        # Читаем из Sheets в отдельном потоке (gspread синхронный)
        from services.sheets import get_sheets_service
        sheets = get_sheets_service()
        accounts_data = await asyncio.to_thread(sheets.get_accounts_balance)

        if not accounts_data:
            await msg.edit_text("❌ Не удалось получить данные из Google Sheets")
            return

        # Обновляем балансы в PostgreSQL
        from sqlalchemy import select
        from db.database import async_session
        from db.models import Account

        updated = []
        not_found = []

        async with async_session() as db:
            for acc_data in accounts_data:
                name = acc_data.get("name", "")
                if not name:
                    continue

                result = await db.execute(select(Account).where(Account.name == name))
                account = result.scalar_one_or_none()

                if account:
                    old_balance = account.balance
                    new_balance = acc_data.get("current", 0)
                    if old_balance != new_balance:
                        account.balance = new_balance
                        updated.append(f"  {name}: {old_balance:.2f} → {new_balance:.2f}")
                    else:
                        updated.append(f"  {name}: {new_balance:.2f} (без изменений)")
                else:
                    not_found.append(name)

            await db.commit()

        # Формируем отчёт
        text = "✅ Балансы обновлены из Google Sheets\n\n"
        text += "📊 Счета:\n"
        text += "\n".join(updated)

        if not_found:
            text += f"\n\n⚠️ Не найдены в БД: {', '.join(not_found)}"

        await msg.edit_text(text, reply_markup=get_main_menu())

    except Exception as e:
        logger.error(f"Sync balances error: {e}", exc_info=True)
        await msg.edit_text(
            f"❌ Ошибка синхронизации:\n{str(e)[:200]}",
            reply_markup=get_main_menu()
        )

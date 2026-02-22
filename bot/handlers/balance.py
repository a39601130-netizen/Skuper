"""
Обработчики балансов и статистики
"""
from telegram import Update
from telegram.ext import ContextTypes
from bot.keyboards.menus import get_main_menu, get_history_keyboard
from services.sheets import get_sheets_service
from utils.formatters import format_balance_message, format_stats_message, format_history, format_income_by_days
from utils.telegram_helpers import safe_edit_message


async def _get_balance_message() -> str:
    sheets = get_sheets_service()
    accounts = sheets.get_accounts_balance()
    for acc in accounts:
        if "сбер" in acc["name"].lower():
            acc["sber_expenses"] = sheets.get_account_expenses(acc["name"], exclude_categories=["Долги"])
            break
    return format_balance_message(accounts)


async def _get_stats_message() -> str:
    sheets = get_sheets_service()
    data = sheets.get_monthly_summary()
    return format_stats_message(data)


async def _get_history_data():
    sheets = get_sheets_service()
    transactions = sheets.get_recent_transactions(10)
    return format_history(transactions), transactions


async def _get_income_stats_message() -> str:
    sheets = get_sheets_service()
    data = sheets.get_income_by_days()
    return format_income_by_days(data)


async def _handle_command(update, get_data, error_prefix=""):
    """Общий паттерн для команд: получить данные и отправить"""
    try:
        message = await get_data()
        await update.message.reply_text(message, parse_mode="Markdown", reply_markup=get_main_menu())
    except Exception as e:
        await update.message.reply_text(
            f"❌ {error_prefix}{str(e)}" if error_prefix else f"❌ Ошибка: {str(e)}",
            reply_markup=get_main_menu()
        )


async def _handle_callback(update, get_data, reply_markup=None):
    """Общий паттерн для callback: ответить и отредактировать сообщение"""
    query = update.callback_query
    await query.answer()
    try:
        message = await get_data()
        await safe_edit_message(query, message, parse_mode="Markdown", reply_markup=reply_markup or get_main_menu())
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}", reply_markup=get_main_menu())


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /balance - показать балансы счетов"""
    await _handle_command(update, _get_balance_message, "Ошибка загрузки балансов: ")


async def balance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback для кнопки балансов"""
    await _handle_callback(update, _get_balance_message)


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats - статистика за месяц"""
    await _handle_command(update, _get_stats_message, "Ошибка загрузки статистики: ")


async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback для кнопки статистики"""
    await _handle_callback(update, _get_stats_message)


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /history - последние транзакции"""
    try:
        message, _ = await _get_history_data()
        await update.message.reply_text(message, parse_mode="Markdown", reply_markup=get_main_menu())
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}", reply_markup=get_main_menu())


async def history_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback для кнопки истории"""
    query = update.callback_query
    await query.answer()
    try:
        message, transactions = await _get_history_data()
        await safe_edit_message(query, message, parse_mode="Markdown", reply_markup=get_history_keyboard(transactions))
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}", reply_markup=get_main_menu())


async def income_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /income - статистика доходов по дням"""
    await _handle_command(update, _get_income_stats_message, "Ошибка загрузки доходов: ")


async def income_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback для кнопки статистики доходов"""
    await _handle_callback(update, _get_income_stats_message)


async def delete_transaction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback для удаления последней транзакции"""
    query = update.callback_query
    await query.answer()

    try:
        row_index = int(query.data.replace("delete_", ""))
        sheets = get_sheets_service()
        success = sheets.delete_transaction(row_index)

        if success:
            transactions = sheets.get_recent_transactions(10)
            message = format_history(transactions)
            await query.edit_message_text(
                f"✅ Последняя транзакция удалена\n\n{message}",
                parse_mode="Markdown",
                reply_markup=get_history_keyboard(transactions)
            )
        else:
            await query.answer("❌ Ошибка удаления", show_alert=True)

    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}", reply_markup=get_main_menu())

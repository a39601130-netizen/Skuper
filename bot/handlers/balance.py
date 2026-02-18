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


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /balance - показать балансы счетов"""
    try:
        message = await _get_balance_message()
        await update.message.reply_text(message, parse_mode="Markdown", reply_markup=get_main_menu())
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка загрузки балансов: {str(e)}\n\nПроверь подключение к Google Sheets.",
            reply_markup=get_main_menu()
        )


async def balance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback для кнопки балансов"""
    query = update.callback_query
    await query.answer()
    try:
        message = await _get_balance_message()
        await safe_edit_message(query, message, parse_mode="Markdown", reply_markup=get_main_menu())
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}", reply_markup=get_main_menu())


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats - статистика за месяц"""
    try:
        message = await _get_stats_message()
        await update.message.reply_text(message, parse_mode="Markdown", reply_markup=get_main_menu())
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка загрузки статистики: {str(e)}", reply_markup=get_main_menu())


async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback для кнопки статистики"""
    query = update.callback_query
    await query.answer()
    try:
        message = await _get_stats_message()
        await safe_edit_message(query, message, parse_mode="Markdown", reply_markup=get_main_menu())
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}", reply_markup=get_main_menu())


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
    try:
        message = await _get_income_stats_message()
        await update.message.reply_text(message, parse_mode="Markdown", reply_markup=get_main_menu())
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка загрузки доходов: {str(e)}", reply_markup=get_main_menu())


async def income_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback для кнопки статистики доходов"""
    query = update.callback_query
    await query.answer()
    try:
        message = await _get_income_stats_message()
        await safe_edit_message(query, message, parse_mode="Markdown", reply_markup=get_main_menu())
    except Exception as e:
        await query.edit_message_text(f"❌ Ошибка: {str(e)}", reply_markup=get_main_menu())


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

"""
Обработчики балансов и статистики
"""
from telegram import Update
from telegram.ext import ContextTypes
from telegram.error import BadRequest
from bot.keyboards.menus import get_main_menu, get_history_keyboard
from services.sheets import get_sheets_service
from utils.formatters import format_balance_message, format_stats_message, format_history, format_income_by_days


async def balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /balance - показать балансы счетов"""
    
    try:
        sheets = get_sheets_service()
        accounts = sheets.get_accounts_balance()
        
        message = format_balance_message(accounts)
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка загрузки балансов: {str(e)}\n\n"
            "Проверь подключение к Google Sheets.",
            reply_markup=get_main_menu()
        )


async def balance_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback для кнопки балансов"""
    query = update.callback_query
    await query.answer()

    try:
        sheets = get_sheets_service()
        accounts = sheets.get_accounts_balance()

        message = format_balance_message(accounts)

        try:
            await query.edit_message_text(
                message,
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
        except BadRequest as e:
            if "message is not modified" not in str(e).lower():
                raise

    except Exception as e:
        await query.edit_message_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_main_menu()
        )


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /stats - статистика за месяц"""
    
    try:
        sheets = get_sheets_service()
        data = sheets.get_monthly_summary()
        
        message = format_stats_message(data)
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка загрузки статистики: {str(e)}",
            reply_markup=get_main_menu()
        )


async def stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback для кнопки статистики"""
    query = update.callback_query
    await query.answer()

    try:
        sheets = get_sheets_service()
        data = sheets.get_monthly_summary()

        message = format_stats_message(data)

        try:
            await query.edit_message_text(
                message,
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
        except BadRequest as e:
            if "message is not modified" not in str(e).lower():
                raise

    except Exception as e:
        await query.edit_message_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_main_menu()
        )


async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /history - последние транзакции"""
    
    try:
        sheets = get_sheets_service()
        transactions = sheets.get_recent_transactions(10)
        
        message = format_history(transactions)
        
        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )
        
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_main_menu()
        )


async def history_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback для кнопки истории"""
    query = update.callback_query
    await query.answer()

    try:
        sheets = get_sheets_service()
        transactions = sheets.get_recent_transactions(10)

        message = format_history(transactions)

        try:
            await query.edit_message_text(
                message,
                parse_mode="Markdown",
                reply_markup=get_history_keyboard(transactions)
            )
        except BadRequest as e:
            if "message is not modified" not in str(e).lower():
                raise

    except Exception as e:
        await query.edit_message_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_main_menu()
        )


async def income_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /income - статистика доходов по дням"""

    try:
        sheets = get_sheets_service()
        data = sheets.get_income_by_days()

        message = format_income_by_days(data)

        await update.message.reply_text(
            message,
            parse_mode="Markdown",
            reply_markup=get_main_menu()
        )

    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка загрузки доходов: {str(e)}",
            reply_markup=get_main_menu()
        )


async def income_stats_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback для кнопки статистики доходов"""
    query = update.callback_query
    await query.answer()

    try:
        sheets = get_sheets_service()
        data = sheets.get_income_by_days()

        message = format_income_by_days(data)

        try:
            await query.edit_message_text(
                message,
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
        except BadRequest as e:
            if "message is not modified" not in str(e).lower():
                raise

    except Exception as e:
        await query.edit_message_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_main_menu()
        )


async def delete_transaction_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback для удаления последней транзакции"""
    query = update.callback_query
    await query.answer()

    try:
        # Извлекаем row_index из callback_data (формат: delete_<row_index>)
        row_index = int(query.data.replace("delete_", ""))

        sheets = get_sheets_service()
        success = sheets.delete_transaction(row_index)

        if success:
            # После удаления показываем обновлённую историю
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
        await query.edit_message_text(
            f"❌ Ошибка: {str(e)}",
            reply_markup=get_main_menu()
        )

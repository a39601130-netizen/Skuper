"""
Budget Bot - Главный файл
Telegram бот для управления личными финансами

Запуск: python main.py
"""
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters
)
from telegram.error import BadRequest

import config
from bot.handlers.start import start_command, help_command
from bot.handlers.transactions import (
    add_command,
    handle_quick_input,
    select_type_callback,
    select_date_callback,
    enter_custom_date,
    select_account_callback,
    select_to_account_callback,
    select_category_callback,
    enter_amount,
    enter_comment,
    enter_hours,
    confirm_callback,
    cancel
)
from bot.handlers.balance import (
    balance_command,
    balance_callback,
    stats_command,
    stats_callback,
    history_command,
    history_callback,
    income_stats_command,
    income_stats_callback
)
from bot.handlers.advisor import (
    advisor_command,
    advisor_callback,
    ask_advisor_command,
    advisor_question,
    advisor_ask_callback,
    advisor_refresh_callback,
    handle_advisor_text
)
from bot.states import TransactionStates, AdvisorStates
from bot.keyboards.menus import get_main_menu

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


async def menu_callback(update: Update, context):
    """Обработчик главного меню"""
    query = update.callback_query
    await query.answer()

    data = query.data

    try:
        if data == "menu_main":
            await query.edit_message_text(
                "🏠 **Главное меню**\n\nВыбери действие:",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
        elif data == "menu_add":
            from bot.keyboards.menus import get_add_menu
            await query.edit_message_text(
                "➕ **Добавить транзакцию**\n\nВыбери тип:",
                parse_mode="Markdown",
                reply_markup=get_add_menu()
            )
        elif data == "menu_balance":
            await balance_callback(update, context)
        elif data == "menu_stats":
            await stats_callback(update, context)
        elif data == "menu_income":
            await income_stats_callback(update, context)
        elif data == "menu_advisor":
            await advisor_callback(update, context)
        elif data == "menu_history":
            await history_callback(update, context)
        elif data == "menu_settings":
            await query.edit_message_text(
                "⚙️ **Настройки**\n\n"
                "В разработке...\n\n"
                "Пока что настройки можно изменить в Google Sheets.",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )
    except BadRequest as e:
        # Игнорируем ошибку "message is not modified"
        if "message is not modified" not in str(e).lower():
            raise  # Если это другая ошибка, пробрасываем дальше


async def handle_text(update: Update, context):
    """Обработчик текстовых сообщений (быстрый ввод)"""
    text = update.message.text.lower()
    
    # Проверяем, есть ли активный диалог (ConversationHandler)
    # Если да - не обрабатываем кнопки клавиатуры
    user_data = context.user_data
    if user_data.get('in_conversation'):
        return  # Пропускаем, ConversationHandler обработает
    
    # Проверяем на reply клавиатуру
    if text in ["➕ расход", "расход"]:
        from bot.keyboards.menus import get_quick_expense_keyboard
        await update.message.reply_text(
            "💸 **Расход**\n\nВыбери категорию:",
            parse_mode="Markdown",
            reply_markup=get_quick_expense_keyboard()
        )
        return
        
    elif text in ["💰 доход", "доход"]:
        await update.message.reply_text(
            "💰 **Доход**\n\n"
            "Введи в формате: `сумма чаевые комментарий 10ч`\n\n"
            "Например: `135 чаевые смена 10ч`",
            parse_mode="Markdown"
        )
        return
        
    elif text in ["💳 баланс", "баланс"]:
        await balance_command(update, context)
        return
        
    elif text in ["📊 статистика", "статистика"]:
        await stats_command(update, context)
        return
        
    elif text in ["🤖 советник", "советник"]:
        await advisor_command(update, context)
        return
    
    # Иначе пробуем парсить как быстрый ввод
    await handle_quick_input(update, context)


def main():
    """Запуск бота"""
    
    # Проверяем наличие токена
    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не задан в .env файле!")
        return
    
    # Создаем приложение
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    
    # === HANDLERS ===
    
    # Команды
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("income", income_stats_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("advisor", advisor_command))
    
    # ConversationHandler для добавления транзакции
    add_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("add", add_command),
            CallbackQueryHandler(select_type_callback, pattern="^add_")
        ],
        states={
            TransactionStates.SELECT_TYPE: [
                CallbackQueryHandler(select_type_callback, pattern="^add_")
            ],
            TransactionStates.SELECT_DATE: [
                CallbackQueryHandler(select_date_callback, pattern="^date_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_custom_date)
            ],
            TransactionStates.SELECT_ACCOUNT: [
                CallbackQueryHandler(select_account_callback, pattern="^(from_|income_)")
            ],
            TransactionStates.SELECT_TO_ACCOUNT: [
                CallbackQueryHandler(select_to_account_callback, pattern="^to_")
            ],
            TransactionStates.SELECT_CATEGORY: [
                CallbackQueryHandler(select_category_callback, pattern="^(quick_|cat_|show_all)")
            ],
            TransactionStates.ENTER_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_amount)
            ],
            TransactionStates.ENTER_COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_comment),
                CommandHandler("skip", enter_comment)
            ],
            TransactionStates.ENTER_HOURS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_hours),
                CommandHandler("skip", enter_hours)
            ],
            TransactionStates.CONFIRM: [
                CallbackQueryHandler(confirm_callback, pattern="^confirm_")
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(menu_callback, pattern="^menu_")
        ],
        per_message=False,
        per_user=True,
        per_chat=True
    )
    # Группа 0 - высший приоритет
    application.add_handler(add_conv_handler, group=0)
    
    # ConversationHandler для AI советника
    advisor_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("ask", ask_advisor_command),
            CallbackQueryHandler(advisor_ask_callback, pattern="^advisor_ask$")
        ],
        states={
            AdvisorStates.WAITING_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, advisor_question)
            ]
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        per_user=True,
        per_chat=True
    )
    application.add_handler(advisor_conv_handler, group=0)
    
    # Callback для кнопок AI советника
    application.add_handler(CallbackQueryHandler(advisor_refresh_callback, pattern="^advisor_refresh$"))
    
    # Callback для меню
    application.add_handler(CallbackQueryHandler(menu_callback, pattern="^menu_"))
    
    # Обработчик текстовых сообщений (быстрый ввод) - группа 1 (ниже приоритет)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
        group=1
    )

    # Запуск бота
    logger.info("🤖 Budget Bot запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()

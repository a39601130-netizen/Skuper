"""
Обработчик AI советника
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from bot.keyboards.menus import get_main_menu
from bot.states import AdvisorStates
from services.sheets import get_sheets_service
from services.ai_advisor import get_advisor


def get_advisor_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после ответа AI"""
    keyboard = [
        [InlineKeyboardButton("💬 Задать вопрос", callback_data="advisor_ask")],
        [InlineKeyboardButton("🔄 Новый анализ", callback_data="advisor_refresh")],
        [InlineKeyboardButton("◀️ Главное меню", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


async def _run_advisor_analysis(context: ContextTypes.DEFAULT_TYPE) -> str:
    sheets = get_sheets_service()
    budget_data = sheets.get_monthly_summary()
    context.user_data['budget_data'] = budget_data
    advisor = get_advisor()
    return await advisor.get_advice(budget_data)


async def advisor_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /advisor - запуск AI советника"""
    await update.message.reply_text(
        "🤖 **AI Советник**\n\nАнализирую твой бюджет...",
        parse_mode="Markdown"
    )
    try:
        advice = await _run_advisor_analysis(context)
        await update.message.reply_text(
            f"🤖 AI Советник:\n\n{advice}",
            parse_mode="Markdown",
            reply_markup=get_advisor_keyboard()
        )
    except Exception as e:
        await update.message.reply_text(
            f"❌ Ошибка: {str(e)}\n\nПопробуй позже или проверь настройки API.",
            reply_markup=get_main_menu()
        )


async def advisor_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback для кнопки AI советника"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "🤖 **AI Советник**\n\nАнализирую твой бюджет...",
        parse_mode="Markdown"
    )
    try:
        advice = await _run_advisor_analysis(context)
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"🤖 AI Советник:\n\n{advice}",
            parse_mode="Markdown",
            reply_markup=get_advisor_keyboard()
        )
    except Exception as e:
        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"❌ Ошибка: {str(e)}",
            reply_markup=get_main_menu()
        )


async def advisor_ask_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback для кнопки 'Задать вопрос'"""
    query = update.callback_query
    await query.answer()

    context.user_data['waiting_advisor_question'] = True

    await query.edit_message_text(
        "🤖 **AI Советник**\n\n"
        "💬 Задай свой вопрос о финансах:\n\n"
        "_Например:_\n"
        "• Как оптимизировать расходы?\n"
        "• Стоит ли делать крупную покупку?\n"
        "• Что делать с долгом?\n\n"
        "Напиши вопрос или /cancel для отмены",
        parse_mode="Markdown"
    )
    return AdvisorStates.WAITING_QUESTION


async def advisor_refresh_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback для кнопки 'Новый анализ'"""
    query = update.callback_query
    await query.answer("Обновляю данные...")
    await advisor_callback(update, context)


async def advisor_question(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка вопроса к AI советнику"""
    question = update.message.text
    context.user_data['waiting_advisor_question'] = False

    await update.message.reply_text("🤖 Думаю над ответом...", parse_mode="Markdown")

    try:
        budget_data = context.user_data.get('budget_data')
        if not budget_data:
            sheets = get_sheets_service()
            budget_data = sheets.get_monthly_summary()
            context.user_data['budget_data'] = budget_data

        advisor = get_advisor()
        advice = await advisor.get_advice(budget_data, user_question=question)

        await update.message.reply_text(
            f"🤖 Ответ:\n\n{advice}",
            parse_mode="Markdown",
            reply_markup=get_advisor_keyboard()
        )
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка: {str(e)}", reply_markup=get_main_menu())

    return ConversationHandler.END


async def ask_advisor_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало диалога с AI советником"""
    context.user_data['waiting_advisor_question'] = True

    await update.message.reply_text(
        "🤖 **AI Советник**\n\n"
        "Задай любой вопрос о своих финансах!\n\n"
        "Например:\n"
        "• _Как мне оптимизировать расходы?_\n"
        "• _Стоит ли мне делать крупную покупку?_\n"
        "• _Что посоветуешь с учётом моего Human Design?_\n\n"
        "Напиши свой вопрос или /cancel для отмены:",
        parse_mode="Markdown"
    )
    return AdvisorStates.WAITING_QUESTION

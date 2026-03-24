"""
Обработчики команд /start и /help
"""
from telegram import Update, WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import config


def get_mini_app_button() -> InlineKeyboardMarkup:
    """Кнопка открытия Mini App"""
    keyboard = [
        [InlineKeyboardButton(
            "📱 Открыть Mini App",
            web_app=WebAppInfo(url=config.MINI_APP_URL)
        )]
    ]
    return InlineKeyboardMarkup(keyboard)


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""

    welcome_text = f"""
🏠 Привет, {config.USER_NAME}!

Я твой **Life Manager Bot**

📱 Все функции доступны в **Mini App**:
• 💰 Финансы — учёт доходов и расходов
• 🏋️ Тренировки — трекер тренировок
• 🤖 AI Советник — умные рекомендации

Нажми кнопку ниже 👇
"""

    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_mini_app_button()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""

    help_text = """📚 **СПРАВКА ПО БОТУ**

📱 Все функции доступны через **Mini App** — нажми /start

⌨️ Команды бота:
• /start — Открыть Mini App
• /backup — Бэкап данных в Google Sheets
• /help — Эта справка
"""

    await update.message.reply_text(
        help_text,
        parse_mode="Markdown",
        reply_markup=get_mini_app_button()
    )

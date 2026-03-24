"""
Клавиатуры бота (минимальные — основной UI в Mini App)
"""
from telegram import WebAppInfo, InlineKeyboardButton, InlineKeyboardMarkup
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

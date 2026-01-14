"""
Главное меню бота
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup


def get_main_menu() -> InlineKeyboardMarkup:
    """Главное меню с модулями"""
    keyboard = [
        [
            InlineKeyboardButton("💰 Финансы", callback_data="module_finance"),
            InlineKeyboardButton("🏋️ Тренировки", callback_data="module_workout")
        ],
        [
            InlineKeyboardButton("🤖 AI Советник", callback_data="module_advisor")
        ],
        [
            InlineKeyboardButton("⚙️ Настройки", callback_data="module_settings")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_finance_menu() -> InlineKeyboardMarkup:
    """Меню финансов"""
    keyboard = [
        [
            InlineKeyboardButton("➕ Добавить", callback_data="finance_add"),
        ],
        [
            InlineKeyboardButton("💳 Балансы", callback_data="finance_balance"),
            InlineKeyboardButton("📊 Статистика", callback_data="finance_stats")
        ],
        [
            InlineKeyboardButton("📜 История", callback_data="finance_history")
        ],
        [
            InlineKeyboardButton("🔙 Главное меню", callback_data="menu_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_workout_menu() -> InlineKeyboardMarkup:
    """Меню тренировок"""
    keyboard = [
        [
            InlineKeyboardButton("▶️ Начать тренировку", callback_data="workout_start"),
        ],
        [
            InlineKeyboardButton("📊 Прогресс", callback_data="workout_progress"),
            InlineKeyboardButton("🏋️ Веса", callback_data="workout_weights")
        ],
        [
            InlineKeyboardButton("📜 История", callback_data="workout_history"),
            InlineKeyboardButton("📅 Следующая", callback_data="workout_next")
        ],
        [
            InlineKeyboardButton("🔙 Главное меню", callback_data="menu_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_advisor_menu() -> InlineKeyboardMarkup:
    """Меню AI советника"""
    keyboard = [
        [
            InlineKeyboardButton("💰 Анализ финансов", callback_data="advisor_finance"),
            InlineKeyboardButton("🏋️ Анализ тренировок", callback_data="advisor_workout")
        ],
        [
            InlineKeyboardButton("❓ Задать вопрос", callback_data="advisor_ask")
        ],
        [
            InlineKeyboardButton("🔙 Главное меню", callback_data="menu_main")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_to_main() -> InlineKeyboardMarkup:
    """Кнопка возврата в главное меню"""
    keyboard = [[InlineKeyboardButton("🔙 Главное меню", callback_data="menu_main")]]
    return InlineKeyboardMarkup(keyboard)

"""
Клавиатуры для модуля тренировок
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from typing import List, Dict


def get_workout_start_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура начала тренировки"""
    keyboard = [
        [
            InlineKeyboardButton("▶️ Начать", callback_data="workout_begin"),
            InlineKeyboardButton("❌ Отмена", callback_data="workout_cancel")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_energy_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора уровня энергии (1-10)"""
    keyboard = [
        [
            InlineKeyboardButton("1", callback_data="energy_1"),
            InlineKeyboardButton("2", callback_data="energy_2"),
            InlineKeyboardButton("3", callback_data="energy_3"),
            InlineKeyboardButton("4", callback_data="energy_4"),
            InlineKeyboardButton("5", callback_data="energy_5"),
        ],
        [
            InlineKeyboardButton("6", callback_data="energy_6"),
            InlineKeyboardButton("7", callback_data="energy_7"),
            InlineKeyboardButton("8", callback_data="energy_8"),
            InlineKeyboardButton("9", callback_data="energy_9"),
            InlineKeyboardButton("10", callback_data="energy_10"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_rpe_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора RPE (5-10)"""
    keyboard = [
        [
            InlineKeyboardButton("5 😊", callback_data="rpe_5"),
            InlineKeyboardButton("6", callback_data="rpe_6"),
            InlineKeyboardButton("7", callback_data="rpe_7"),
        ],
        [
            InlineKeyboardButton("8", callback_data="rpe_8"),
            InlineKeyboardButton("9 😰", callback_data="rpe_9"),
            InlineKeyboardButton("10 🔥", callback_data="rpe_10"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_emotional_wave_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура эмоциональной волны"""
    keyboard = [
        [
            InlineKeyboardButton("↑ Подъём", callback_data="wave_up"),
            InlineKeyboardButton("→ Нейтраль", callback_data="wave_neutral"),
            InlineKeyboardButton("↓ Спад", callback_data="wave_down"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_warmup_phase_keyboard(phase: int) -> InlineKeyboardMarkup:
    """Клавиатура для фазы разминки"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Выполнено", callback_data=f"warmup_done_{phase}"),
        ],
        [
            InlineKeyboardButton("⏭️ Пропустить", callback_data=f"warmup_skip_{phase}"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_warmup_complete_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура завершения разминки"""
    keyboard = [
        [
            InlineKeyboardButton("▶️ К упражнениям!", callback_data="warmup_complete"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_set_input_keyboard(has_alternative=True, is_alternative=False) -> InlineKeyboardMarkup:
    """Клавиатура во время ввода подхода"""
    keyboard = []
    # Кнопки замены и переноса
    row1 = []
    if has_alternative:
        label = "🔄 Оригинал" if is_alternative else "🔄 Замена"
        row1.append(InlineKeyboardButton(label, callback_data="exercise_alt"))
    row1.append(InlineKeyboardButton("⏬ Позже", callback_data="exercise_later"))
    keyboard.append(row1)
    keyboard.append([
        InlineKeyboardButton("⏭️ Пропустить", callback_data="exercise_skip"),
        InlineKeyboardButton("🏁 Завершить", callback_data="workout_end_early"),
    ])
    return InlineKeyboardMarkup(keyboard)


def get_rest_timer_keyboard(seconds: int) -> InlineKeyboardMarkup:
    """Клавиатура таймера отдыха"""
    keyboard = [
        [
            InlineKeyboardButton(f"⏱️ {seconds // 60}:{seconds % 60:02d}", callback_data="timer_display"),
        ],
        [
            InlineKeyboardButton("⏩ Готов раньше", callback_data="timer_skip"),
            InlineKeyboardButton("➕ +30 сек", callback_data="timer_add_30"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_exercise_complete_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после завершения упражнения"""
    keyboard = [
        [
            InlineKeyboardButton("▶️ Следующее упражнение", callback_data="exercise_next"),
        ],
        [
            InlineKeyboardButton("🏁 Завершить тренировку", callback_data="workout_end_early"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_workout_complete_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура после завершения тренировки"""
    keyboard = [
        [
            InlineKeyboardButton("📊 Показать прогресс", callback_data="workout_show_progress"),
        ],
        [
            InlineKeyboardButton("🤖 AI Анализ", callback_data="workout_ai_analysis"),
        ],
        [
            InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_yes_no_keyboard(prefix: str) -> InlineKeyboardMarkup:
    """Универсальная клавиатура Да/Нет"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Да", callback_data=f"{prefix}_yes"),
            InlineKeyboardButton("❌ Нет", callback_data=f"{prefix}_no"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)


def get_back_keyboard(callback: str = "workout_menu") -> InlineKeyboardMarkup:
    """Кнопка назад"""
    keyboard = [[InlineKeyboardButton("🔙 Назад", callback_data=callback)]]
    return InlineKeyboardMarkup(keyboard)


def get_day_select_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора дня тренировки"""
    keyboard = [
        [
            InlineKeyboardButton("🔵 День A (Горизонтальный)", callback_data="select_day_A"),
            InlineKeyboardButton("🟢 День B (Вертикальный)", callback_data="select_day_B"),
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

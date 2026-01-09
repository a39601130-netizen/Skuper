"""
Обработчик управления уведомлениями
"""
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
import json
import os

# Простое хранилище пользователей (в будущем - БД)
USERS_FILE = "users_data.json"


def load_users():
    """Загрузка данных пользователей"""
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}


def save_users(users):
    """Сохранение данных пользователей"""
    with open(USERS_FILE, 'w', encoding='utf-8') as f:
        json.dump(users, f, ensure_ascii=False, indent=2)


def get_user_settings(chat_id):
    """Получить настройки пользователя"""
    users = load_users()
    user_id = str(chat_id)

    if user_id not in users:
        users[user_id] = {
            "chat_id": chat_id,
            "notifications": {
                "daily_reminder": True,
                "tips_reminder": True,
                "budget_alert": True,
                "weekly_summary": True,
                "month_end": True
            },
            "reminder_time": "21:00"
        }
        save_users(users)

    return users[user_id]


def update_user_setting(chat_id, setting_key, value):
    """Обновить настройку пользователя"""
    users = load_users()
    user_id = str(chat_id)

    if user_id in users:
        if "." in setting_key:  # notifications.daily_reminder
            keys = setting_key.split(".")
            users[user_id][keys[0]][keys[1]] = value
        else:
            users[user_id][setting_key] = value

        save_users(users)


async def notifications_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /notifications - настройки уведомлений"""
    chat_id = update.effective_chat.id
    settings = get_user_settings(chat_id)

    # Формируем сообщение
    notif = settings["notifications"]

    text = f"""🔔 **Настройки уведомлений**

⏰ Время напоминаний: **{settings['reminder_time']}**

**Активные уведомления:**
{'✅' if notif['daily_reminder'] else '❌'} Ежедневное напоминание
{'✅' if notif['tips_reminder'] else '❌'} Напоминание о чаевых
{'✅' if notif['budget_alert'] else '❌'} Предупреждения о бюджете
{'✅' if notif['weekly_summary'] else '❌'} Еженедельная статистика
{'✅' if notif['month_end'] else '❌'} Напоминание о конце месяца

Нажми кнопку, чтобы изменить настройки:
"""

    keyboard = [
        [
            InlineKeyboardButton(
                f"{'✅' if notif['daily_reminder'] else '❌'} Ежедневное",
                callback_data="notif_toggle_daily_reminder"
            ),
            InlineKeyboardButton(
                f"{'✅' if notif['tips_reminder'] else '❌'} Чаевые",
                callback_data="notif_toggle_tips_reminder"
            )
        ],
        [
            InlineKeyboardButton(
                f"{'✅' if notif['budget_alert'] else '❌'} Бюджет",
                callback_data="notif_toggle_budget_alert"
            ),
            InlineKeyboardButton(
                f"{'✅' if notif['weekly_summary'] else '❌'} Еженедельное",
                callback_data="notif_toggle_weekly_summary"
            )
        ],
        [
            InlineKeyboardButton(
                f"{'✅' if notif['month_end'] else '❌'} Конец месяца",
                callback_data="notif_toggle_month_end"
            )
        ],
        [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")]
    ]

    await update.message.reply_text(
        text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def notifications_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback для переключения уведомлений"""
    query = update.callback_query
    await query.answer()

    chat_id = update.effective_chat.id
    data = query.data

    if data.startswith("notif_toggle_"):
        notif_type = data.replace("notif_toggle_", "")
        settings = get_user_settings(chat_id)

        # Переключаем значение
        current = settings["notifications"][notif_type]
        update_user_setting(chat_id, f"notifications.{notif_type}", not current)

        # Обновляем сообщение
        settings = get_user_settings(chat_id)  # Перезагружаем
        notif = settings["notifications"]

        text = f"""🔔 **Настройки уведомлений**

⏰ Время напоминаний: **{settings['reminder_time']}**

**Активные уведомления:**
{'✅' if notif['daily_reminder'] else '❌'} Ежедневное напоминание
{'✅' if notif['tips_reminder'] else '❌'} Напоминание о чаевых
{'✅' if notif['budget_alert'] else '❌'} Предупреждения о бюджете
{'✅' if notif['weekly_summary'] else '❌'} Еженедельная статистика
{'✅' if notif['month_end'] else '❌'} Напоминание о конце месяца

Нажми кнопку, чтобы изменить настройки:
"""

        keyboard = [
            [
                InlineKeyboardButton(
                    f"{'✅' if notif['daily_reminder'] else '❌'} Ежедневное",
                    callback_data="notif_toggle_daily_reminder"
                ),
                InlineKeyboardButton(
                    f"{'✅' if notif['tips_reminder'] else '❌'} Чаевые",
                    callback_data="notif_toggle_tips_reminder"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{'✅' if notif['budget_alert'] else '❌'} Бюджет",
                    callback_data="notif_toggle_budget_alert"
                ),
                InlineKeyboardButton(
                    f"{'✅' if notif['weekly_summary'] else '❌'} Еженедельное",
                    callback_data="notif_toggle_weekly_summary"
                )
            ],
            [
                InlineKeyboardButton(
                    f"{'✅' if notif['month_end'] else '❌'} Конец месяца",
                    callback_data="notif_toggle_month_end"
                )
            ],
            [InlineKeyboardButton("🏠 Главное меню", callback_data="menu_main")]
        ]

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

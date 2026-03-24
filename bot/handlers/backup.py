"""
Handler для бэкапа данных в Google Sheets
Flow: Настройки → 💾 Бэкап → Тип (Финансы/Тренировки/Всё) → Месяц → Экспорт
"""
import logging
from utils.timezone import now_minsk

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes


logger = logging.getLogger(__name__)

MONTH_NAMES = [
    "", "Январь", "Февраль", "Март", "Апрель", "Май", "Июнь",
    "Июль", "Август", "Сентябрь", "Октябрь", "Ноябрь", "Декабрь"
]


def get_backup_menu() -> InlineKeyboardMarkup:
    """Меню выбора типа бэкапа"""
    keyboard = [
        [InlineKeyboardButton("💰 Финансы", callback_data="backup_type_finance")],
        [InlineKeyboardButton("🏋️ Тренировки", callback_data="backup_type_workout")],
        [InlineKeyboardButton("📦 Всё сразу", callback_data="backup_type_all")],
    ]
    return InlineKeyboardMarkup(keyboard)


def get_backup_month_keyboard(backup_type: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора месяца (текущий + 2 предыдущих)"""
    now = now_minsk()
    buttons = []

    for i in range(3):
        month = now.month - i
        year = now.year
        if month <= 0:
            month += 12
            year -= 1
        label = f"{MONTH_NAMES[month]} {year}"
        if i == 0:
            label += " (текущий)"
        buttons.append([
            InlineKeyboardButton(label, callback_data=f"backup_month_{backup_type}_{year}_{month}")
        ])

    buttons.append([InlineKeyboardButton("🔙 Назад", callback_data="backup_menu")])
    return InlineKeyboardMarkup(buttons)


async def backup_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /backup — показать меню бэкапа"""
    await update.message.reply_text(
        "💾 **Бэкап в Google Sheets**\n\n"
        "Что экспортировать?",
        parse_mode="Markdown",
        reply_markup=get_backup_menu()
    )


async def backup_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback: показать меню бэкапа (из Настроек)"""
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "💾 **Бэкап в Google Sheets**\n\n"
        "Что экспортировать?",
        parse_mode="Markdown",
        reply_markup=get_backup_menu()
    )


async def backup_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback: выбор типа бэкапа → показать месяцы"""
    query = update.callback_query
    await query.answer()

    # backup_type_finance / backup_type_workout / backup_type_all
    backup_type = query.data.replace("backup_type_", "")

    type_labels = {
        "finance": "💰 Финансы",
        "workout": "🏋️ Тренировки",
        "all": "📦 Всё сразу"
    }

    await query.edit_message_text(
        f"💾 **Бэкап: {type_labels.get(backup_type, backup_type)}**\n\n"
        f"Выбери месяц:",
        parse_mode="Markdown",
        reply_markup=get_backup_month_keyboard(backup_type)
    )


async def backup_month_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Callback: выбран месяц → запускаем бэкап"""
    query = update.callback_query
    await query.answer()

    # backup_month_finance_2026_3
    parts = query.data.replace("backup_month_", "").rsplit("_", 2)
    backup_type = parts[0]
    year = int(parts[1])
    month = int(parts[2])

    type_labels = {
        "finance": "💰 Финансы",
        "workout": "🏋️ Тренировки",
        "all": "📦 Всё"
    }

    await query.edit_message_text(
        f"🔄 Бэкап: {type_labels.get(backup_type)} за {MONTH_NAMES[month]} {year}...\n\n"
        f"⏳ Экспорт в Google Sheets..."
    )

    try:
        from services.backup import BackupService
        backup = BackupService()

        if backup_type == "finance":
            finance = await backup.backup_finances(year, month)
            text = _format_finance_result(finance, month, year)
        elif backup_type == "workout":
            workouts = await backup.backup_workouts(year, month)
            weights = await backup.backup_current_weights()
            text = _format_workout_result(workouts, weights, month, year)
        else:  # all
            results = await backup.full_backup(year, month)
            text = _format_full_result(results, month, year)

        # Кнопки после бэкапа
        keyboard = [
            [InlineKeyboardButton("🔄 Ещё бэкап", callback_data="backup_menu")],
        ]

        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    except Exception as e:
        logger.error(f"Backup error: {e}", exc_info=True)
        await query.edit_message_text(
            f"❌ Ошибка бэкапа:\n`{str(e)[:300]}`",
            parse_mode="Markdown",
            reply_markup=get_backup_menu()
        )


def _format_finance_result(finance: dict, month: int, year: int) -> str:
    status = "✅" if not finance["errors"] else "⚠️"
    text = f"{status} **Бэкап финансов — {MONTH_NAMES[month]} {year}**\n\n"
    text += f"💰 Транзакции: {finance['count']}\n"

    if finance["errors"]:
        text += "\n❌ Ошибки:\n"
        for err in finance["errors"]:
            text += f"  • {err}\n"
    elif finance["count"] > 0:
        text += "\n✅ Экспорт завершён. Можно скачивать!"
    else:
        text += "\nℹ️ Нет данных за этот месяц."
    return text


def _format_workout_result(workouts: dict, weights: dict, month: int, year: int) -> str:
    errors = workouts["errors"] + weights["errors"]
    status = "✅" if not errors else "⚠️"
    text = f"{status} **Бэкап тренировок — {MONTH_NAMES[month]} {year}**\n\n"
    text += f"🏋️ Тренировки: {workouts['workouts_count']}\n"
    text += f"📝 Подходы: {workouts['sets_count']}\n"
    text += f"⚖️ Текущие веса: {weights['count']}\n"

    if errors:
        text += "\n❌ Ошибки:\n"
        for err in errors:
            text += f"  • {err}\n"
    elif workouts["workouts_count"] > 0 or weights["count"] > 0:
        text += "\n✅ Экспорт завершён. Можно скачивать!"
    else:
        text += "\nℹ️ Нет данных за этот месяц."
    return text


def _format_full_result(results: dict, month: int, year: int) -> str:
    status = "✅" if results["status"] == "success" else "⚠️"
    finance = results["finance"]
    workouts = results["workouts"]
    weights = results["weights"]

    text = f"{status} **Полный бэкап — {MONTH_NAMES[month]} {year}**\n\n"
    text += f"💰 Транзакции: {finance['count']}\n"
    text += f"🏋️ Тренировки: {workouts['workouts_count']}\n"
    text += f"📝 Подходы: {workouts['sets_count']}\n"
    text += f"⚖️ Текущие веса: {weights['count']}\n"
    text += f"\n📊 Всего записей: {results['total_records']}"

    all_errors = finance["errors"] + workouts["errors"] + weights["errors"]
    if all_errors:
        text += "\n\n❌ Ошибки:\n"
        for err in all_errors:
            text += f"  • {err}\n"
    elif results["total_records"] > 0:
        text += "\n\n✅ Экспорт завершён. Можно скачивать!"
    else:
        text += "\n\nℹ️ Нет данных за этот месяц."
    return text

"""
Клавиатуры и меню для Telegram бота
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

# === ВЫБОР ДАТЫ ===
def get_date_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора даты"""
    from datetime import datetime, timedelta
    
    today = datetime.now()
    yesterday = today - timedelta(days=1)
    day_before = today - timedelta(days=2)
    
    keyboard = [
        [InlineKeyboardButton(f"📅 Сегодня ({today.day}.{today.month:02d})", callback_data=f"date_{today.day}")],
        [InlineKeyboardButton(f"📅 Вчера ({yesterday.day}.{yesterday.month:02d})", callback_data=f"date_{yesterday.day}")],
        [InlineKeyboardButton(f"📅 Позавчера ({day_before.day}.{day_before.month:02d})", callback_data=f"date_{day_before.day}")],
        [InlineKeyboardButton("📆 Другой день (ввести)", callback_data="date_custom")],
        [InlineKeyboardButton("◀️ Назад", callback_data="menu_add")]
    ]
    return InlineKeyboardMarkup(keyboard)


# === ГЛАВНОЕ МЕНЮ (импортируется из main_menu.py) ===
from bot.keyboards.main_menu import get_main_menu


# === МЕНЮ ДОБАВЛЕНИЯ ТРАНЗАКЦИИ ===
def get_add_menu() -> InlineKeyboardMarkup:
    """Меню выбора типа транзакции"""
    keyboard = [
        [InlineKeyboardButton("💸 Расход", callback_data="add_expense")],
        [InlineKeyboardButton("💰 Доход", callback_data="add_income")],
        [InlineKeyboardButton("🔄 Перевод", callback_data="add_transfer")],
        [InlineKeyboardButton("💱 Обмен валюты", callback_data="add_exchange")],
        [InlineKeyboardButton("◀️ Назад", callback_data="menu_main")]
    ]
    return InlineKeyboardMarkup(keyboard)


# === ВЫБОР ВАЛЮТЫ ===
def get_currency_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора валюты"""
    keyboard = [
        [
            InlineKeyboardButton("🇧🇾 BYN", callback_data="currency_BYN"),
            InlineKeyboardButton("🇺🇸 USD", callback_data="currency_USD")
        ],
        [
            InlineKeyboardButton("🇪🇺 EUR", callback_data="currency_EUR"),
            InlineKeyboardButton("🇷🇺 RUB", callback_data="currency_RUB")
        ],
        [InlineKeyboardButton("◀️ Назад", callback_data="menu_add")]
    ]
    return InlineKeyboardMarkup(keyboard)


# === ВЫБОР СЧЕТА ===
def get_accounts_keyboard(accounts: list, prefix: str = "acc") -> InlineKeyboardMarkup:
    """Клавиатура выбора счета"""
    keyboard = []

    # По 2 счета в ряд
    row = []
    for acc in accounts:
        row.append(InlineKeyboardButton(
            f"💳 {acc}",
            callback_data=f"{prefix}_{acc}"
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:  # Остаток
        keyboard.append(row)

    # Кнопка "Назад" для возврата к меню добавления транзакции
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="menu_add")])
    return InlineKeyboardMarkup(keyboard)


# === ВЫБОР КАТЕГОРИИ ===
def get_categories_keyboard(categories: list, trans_type: str) -> InlineKeyboardMarkup:
    """Клавиатура выбора категории"""
    keyboard = []

    # Маппинг эмодзи для категорий
    category_emoji = {
        # Доходы
        "Зарплата/Чаевые": "💵",
        "Подработка": "💼",
        "Другое": "💰",

        # Расходы
        "Продукты": "🛒",
        "Кафе": "☕",
        "Транспорт": "🚌",
        "Такси": "🚕",
        "Досуг": "🎮",
        "Покупки": "🛍️",
        "Здоровье и красота": "💅",
        "Аптека": "💊",
        "Ништяки": "🍫",
        "Аренда": "🏠",
        "Коммуналка": "🔌",
        "Интернет и связь": "📱",
        "Кошки": "🐱",
        "Долги": "💳",
        "Одежда": "👕",
        "Подарки": "🎁"
    }

    row = []
    for cat in categories:
        emoji = category_emoji.get(cat, "📁")
        row.append(InlineKeyboardButton(
            f"{emoji} {cat}",
            callback_data=f"cat_{cat}"
        ))
        if len(row) == 2:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    # Кнопка "Назад" для возврата к быстрым категориям
    keyboard.append([InlineKeyboardButton("◀️ Назад", callback_data="menu_add")])
    return InlineKeyboardMarkup(keyboard)


# === БЫСТРЫЕ КАТЕГОРИИ РАСХОДОВ ===
def get_quick_expense_keyboard() -> InlineKeyboardMarkup:
    """Быстрые кнопки для частых расходов"""
    keyboard = [
        [
            InlineKeyboardButton("🛒 Продукты", callback_data="quick_Продукты"),
            InlineKeyboardButton("☕ Кафе", callback_data="quick_Кафе")
        ],
        [
            InlineKeyboardButton("🚌 Транспорт", callback_data="quick_Транспорт"),
            InlineKeyboardButton("🚕 Такси", callback_data="quick_Такси")
        ],
        [
            InlineKeyboardButton("🎮 Досуг", callback_data="quick_Досуг"),
            InlineKeyboardButton("🛍️ Покупки", callback_data="quick_Покупки")
        ],
        [InlineKeyboardButton("📋 Все категории", callback_data="show_all_categories")],
        [InlineKeyboardButton("◀️ Назад", callback_data="menu_add")]
    ]
    return InlineKeyboardMarkup(keyboard)


# === ПОДТВЕРЖДЕНИЕ ===
def get_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения"""
    keyboard = [
        [
            InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_yes"),
            InlineKeyboardButton("❌ Отмена", callback_data="confirm_no")
        ],
        [InlineKeyboardButton("✏️ Изменить", callback_data="confirm_edit")]
    ]
    return InlineKeyboardMarkup(keyboard)


# === REPLY КЛАВИАТУРА ДЛЯ БЫСТРОГО ВВОДА ===
def get_reply_keyboard() -> ReplyKeyboardMarkup:
    """Постоянная клавиатура внизу экрана"""
    keyboard = [
        ["➕ Расход", "💰 Доход"],
        ["💳 Баланс", "📊 Статистика"],
        ["🤖 Советник"]
    ]
    return ReplyKeyboardMarkup(
        keyboard, 
        resize_keyboard=True,
        input_field_placeholder="Введи: сумма категория комментарий"
    )


# === ИСТОРИЯ С КНОПКАМИ УДАЛЕНИЯ ===
def get_history_keyboard(transactions: list) -> InlineKeyboardMarkup:
    """Клавиатура для истории транзакций с кнопкой удаления последней операции"""
    keyboard = []

    # Добавляем кнопку удаления только для первой (последней по времени) транзакции
    if transactions and transactions[0].get("row_index"):
        row_index = transactions[0].get("row_index")
        keyboard.append([
            InlineKeyboardButton("🗑️ Удалить последнюю", callback_data=f"delete_{row_index}")
        ])

    # Кнопка "Назад в главное меню"
    keyboard.append([InlineKeyboardButton("◀️ Главное меню", callback_data="menu_main")])

    return InlineKeyboardMarkup(keyboard)


# === CALLBACK DATA PATTERNS ===
# Для использования в хендлерах
CALLBACK_PATTERNS = {
    "main_menu": r"^menu_",
    "add_transaction": r"^add_",
    "select_account": r"^acc_",
    "select_category": r"^cat_",
    "quick_category": r"^quick_",
    "confirm": r"^confirm_",
    "delete": r"^delete_"
}

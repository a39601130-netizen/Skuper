"""
Утилиты для форматирования сообщений
"""
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import re

logger = logging.getLogger(__name__)

def format_money(amount: float, currency: str = "BYN") -> str:
    """Форматировать денежную сумму"""
    if amount >= 0:
        return f"{amount:,.2f} {currency}".replace(",", " ")
    else:
        return f"-{abs(amount):,.2f} {currency}".replace(",", " ")


def format_balance_message(accounts: List[Dict[str, Any]]) -> str:
    """Форматировать сообщение с балансами"""
    lines = ["💳 **БАЛАНСЫ СЧЕТОВ**\n"]

    total_byn = 0

    for acc in accounts:
        current = acc["current"]
        currency = acc["currency"]

        # Emoji для статуса
        if current > 0:
            emoji = "✅"
        elif current < 0:
            emoji = "🔴"
        else:
            emoji = "⚪"

        # Для Сбера показываем в одну строку: баланс / расходы
        if "sber_expenses" in acc:
            expenses = acc["sber_expenses"]
            lines.append(f"{emoji} {acc['name']}: {format_money(current, currency)} / {format_money(expenses, currency)}")
        else:
            lines.append(f"{emoji} {acc['name']}: **{format_money(current, currency)}**")

        if currency == "BYN":
            total_byn += current

    lines.append(f"\n📊 **Всего (BYN):** {format_money(total_byn)}")

    return "\n".join(lines)


def format_stats_message(data: Dict[str, Any]) -> str:
    """Форматировать статистику за месяц"""
    lines = [
        "📊 **СТАТИСТИКА ЗА МЕСЯЦ**\n",
        f"💰 Доходы: **{format_money(data['total_income'])}**",
        f"💸 Расходы: **{format_money(data['total_expense'])}**",
        f"📈 Баланс: **{format_money(data['balance'])}**"
    ]

    # Заработок в час (если есть данные о часах)
    total_hours = data.get('total_hours', 0)
    if total_hours and total_hours > 0:
        total_tips = data.get('total_tips', 0) or data.get('total_income', 0)
        hourly_rate = total_tips / total_hours
        lines.append(f"⏰ Отработано: **{total_hours:.1f} ч** → **{format_money(hourly_rate)}/ч**")

    # Группируем по типу
    income_cats = [c for c in data.get("categories", []) if c["type"] == "Доход"]
    expense_cats = [c for c in data.get("categories", []) if c["type"] == "Расход"]

    # Доходы
    if income_cats:
        lines.append("\n💰 **Доходы:**")
        for cat in income_cats:
            if cat["spent"] > 0:
                lines.append(f"  • {cat['name']}: {format_money(cat['spent'])}")

    # Расходы
    if expense_cats:
        lines.append("\n💸 **Расходы:**")

        # Сортируем: "Аренда" первой, остальные по порядку
        def sort_key(cat):
            if cat['name'] == "Аренда":
                return (0, cat['name'])
            else:
                return (1, cat['name'])

        expense_cats = sorted(expense_cats, key=sort_key)

        # Маппинг эмодзи для категорий
        category_emoji = {
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

        for cat in expense_cats:
            spent = cat["spent"]
            budget = cat["budget"]

            # Показываем категории с расходами ИЛИ с бюджетом
            if spent > 0 or budget > 0:
                emoji = category_emoji.get(cat['name'], "📁")

                if budget > 0:
                    # Есть бюджет - показываем прогресс
                    progress = int((spent / budget) * 100) if budget > 0 else 0

                    # Создаем шкалу прогресса
                    filled = int(progress / 10)
                    if filled > 10:
                        filled = 10
                    empty = 10 - filled
                    bar = "█" * filled + "░" * empty

                    if progress >= 100:
                        status = "🔴"
                    elif progress >= 80:
                        status = "🟡"
                    else:
                        status = "🟢"

                    lines.append(
                        f"{emoji} {cat['name']}: {format_money(spent)}/{format_money(budget)}"
                    )
                    lines.append(f"   {status} [{bar}] {progress}%")
                else:
                    # Нет бюджета - просто показываем сумму расходов
                    lines.append(f"{emoji} {cat['name']}: {format_money(spent)}")

    return "\n".join(lines)


def format_transaction_success(
    trans_type: str,
    amount: float,
    category: Optional[str],
    comment: Optional[str],
    hours: Optional[float] = None,
    account: Optional[str] = None,
    show_balance: bool = True,
    currency: str = "BYN",
    exchange_rate: Optional[float] = None,
    amount_to: Optional[float] = None,
    to_account: Optional[str] = None
) -> str:
    """Форматировать сообщение об успешной транзакции"""

    emoji = {"Доход": "💰", "Расход": "💸", "Перевод": "🔄", "Обмен валюты": "💱"}.get(trans_type, "✅")

    lines = [
        "✅ **Записано!**\n",
        f"{emoji} {trans_type}: **{format_money(amount, currency)}**"
    ]

    # Для обмена валюты показываем детали
    if trans_type == "Обмен валюты" and amount_to and exchange_rate:
        # Определяем валюту зачисления через API
        to_currency = "BYN"
        if to_account:
            try:
                from services.sheets import get_sheets_service
                sheets = get_sheets_service()
                to_currency = sheets.get_account_currency(to_account)
            except Exception:
                pass
        lines.append(f"💵 Получено: **{format_money(amount_to, to_currency)}**")
        lines.append(f"📊 Курс: {exchange_rate:.4f}")

    # Для расхода в иностранной валюте показываем эквивалент
    if trans_type == "Расход" and currency != "BYN" and exchange_rate and amount_to:
        lines.append(f"📊 Курс: {exchange_rate:.4f}")
        lines.append(f"💰 Эквивалент: **{format_money(amount_to, 'BYN')}**")

    if category:
        lines.append(f"📁 Категория: {category}")

    if comment:
        lines.append(f"💬 {comment}")

    if hours:
        hourly_rate = 6.5  # Ставка в час
        earned = hours * hourly_rate
        lines.append(f"⏰ Часы: {hours} (= {format_money(earned)} по ставке)")

    lines.append(f"📅 {datetime.now().strftime('%d.%m.%Y')}")

    # Показываем баланс и остаток по категории
    if show_balance:
        try:
            from services.sheets import get_sheets_service
            sheets = get_sheets_service()

            # Получаем баланс счёта
            if account:
                accounts = sheets.get_accounts_balance()
                acc_data = next((a for a in accounts if a["name"] == account), None)
                if acc_data:
                    balance = acc_data["current"]
                    currency = acc_data.get("currency", "BYN")
                    lines.append(f"\n💳 **{account}:** {format_money(balance, currency)}")

            # Получаем остаток по категории (только для расходов)
            # Используем get_monthly_summary() вместо get_categories_budget(),
            # т.к. формулы на листе "Категории" могут не работать
            if category and trans_type == "Расход":
                summary = sheets.get_monthly_summary()
                cat_data = next((c for c in summary["categories"] if c["name"] == category and c["type"] == "Расход"), None)
                if cat_data and cat_data["budget"] > 0:
                    remaining = cat_data["remaining"]
                    budget = cat_data["budget"]
                    spent = cat_data["spent"]
                    progress = int((spent / budget) * 100) if budget > 0 else 0

                    # Выбираем эмодзи в зависимости от прогресса
                    if progress >= 100:
                        status_emoji = "🔴"
                    elif progress >= 80:
                        status_emoji = "🟡"
                    else:
                        status_emoji = "🟢"

                    lines.append(f"{status_emoji} **{category}:** осталось {format_money(remaining)} из {format_money(budget)} ({progress}%)")
        except Exception as e:
            # Если произошла ошибка при получении данных, просто не показываем баланс
            pass

    return "\n".join(lines)


def parse_quick_input(text: str) -> Optional[Dict[str, Any]]:
    """
    Парсинг быстрого ввода транзакции

    Форматы:
    - "50 продукты магазин" -> Расход 50, Продукты, комментарий "магазин"
    - "135 чаевые смена 10ч" -> Доход 135, Чаевые, 10 часов
    - "перевод 100 карта" -> Перевод 100 на Карту

    Returns:
        Dict с полями: type, amount, category, comment, hours, to_account
        или None если не удалось распарсить
    """
    import logging
    logger = logging.getLogger(__name__)

    text = text.strip().lower()
    logger.info(f"[PARSE] Original text: {text}")

    # Паттерн для часов: "10ч", "10 ч", "10 час", "10 часа", "10 часов"
    # ВАЖНО: (?:ч|час) сделано обязательным (без ?), чтобы находить только числа с "ч"/"час"
    hours_pattern = r'(\d+(?:[.,]\d+)?)\s*(?:ч|час(?:а|ов)?)\b'
    hours_match = re.search(hours_pattern, text)
    hours = float(hours_match.group(1).replace(',', '.')) if hours_match else None

    logger.info(f"[PARSE] Hours found: {hours}")

    # Убираем часы из текста для дальнейшего парсинга
    if hours_match:
        text = re.sub(hours_pattern, '', text).strip()
        logger.info(f"[PARSE] Text after removing hours: {text}")
    
    # Проверяем на перевод
    if text.startswith('перевод'):
        # Формат: "перевод 100 карта"
        match = re.match(r'перевод\s+(\d+(?:\.\d+)?)\s+(\S+)', text)
        if match:
            return {
                "type": "Перевод",
                "amount": float(match.group(1)),
                "to_account": match.group(2).capitalize(),
                "category": None,
                "comment": None,
                "hours": None
            }
        return None
    
    # Парсим сумму в начале (с опциональной валютой: р, руб, byn, бел)
    # Поддерживаемые форматы: "50 продукты", "50р продукты", "50 р продукты", "100 byn продукты", "100byn продукты"
    amount_match = re.match(r'(\d+(?:[.,]\d+)?)\s*(?:р|руб|byn|бел|bel)?\s+', text, re.IGNORECASE)
    if not amount_match:
        logger.info("[PARSE] No amount found at beginning")
        return None

    amount = float(amount_match.group(1).replace(',', '.'))
    rest = text[amount_match.end():].strip()

    logger.info(f"[PARSE] Amount: {amount}, Rest: {rest}")

    # Разбиваем остаток на части
    parts = rest.split(None, 1)  # Максимум 2 части: категория и комментарий

    if not parts:
        logger.info("[PARSE] No parts found after amount")
        return None

    category_input = parts[0]
    comment = parts[1] if len(parts) > 1 else None

    logger.info(f"[PARSE] Category input: {category_input}, Comment: {comment}")
    
    # Маппинг сокращений категорий
    category_map = {
        # Доходы
        "чаевые": "Чаевые",
        "зарплата": "Зарплата",
        "зп": "Зарплата",
        "подработка": "Подработка",

        # Расходы
        "продукты": "Продукты",
        "прод": "Продукты",
        "еда": "Продукты",
        "магазин": "Продукты",
        "маг": "Продукты",
        "кафе": "Кафе",
        "кафешка": "Кафе",
        "ресторан": "Кафе",
        "рест": "Кафе",
        "кофе": "Кафе",
        "досуг": "Досуг",
        "развлечения": "Досуг",
        "развл": "Досуг",
        "игры": "Досуг",
        "кино": "Досуг",
        "фильм": "Досуг",
        "транспорт": "Транспорт",
        "тр": "Транспорт",
        "трансп": "Транспорт",
        "метро": "Транспорт",
        "автобус": "Транспорт",
        "троллейбус": "Транспорт",
        "трамвай": "Транспорт",
        "такси": "Такси",
        "яндекс": "Такси",
        "убер": "Такси",
        "здоровье": "Здоровье и красота",
        "здор": "Здоровье и красота",
        "красота": "Здоровье и красота",
        "аптека": "Аптека",
        "лекарства": "Аптека",
        "лек": "Аптека",
        "ништяки": "Ништяки",
        "ништ": "Ништяки",
        "сладкое": "Ништяки",
        "покупки": "Покупки",
        "поку": "Покупки",
        "шоппинг": "Покупки",
        "шопинг": "Покупки",
        "вещи": "Покупки",
        "аренда": "Аренда",
        "квартира": "Аренда",
        "арен": "Аренда",
        "коммуналка": "Коммуналка",
        "комм": "Коммуналка",
        "ком": "Коммуналка",
        "жкх": "Коммуналка",
        "интернет": "Интернет и связь",
        "инет": "Интернет и связь",
        "связь": "Интернет и связь",
        "телефон": "Интернет и связь",
        "тел": "Интернет и связь",
        "мобильный": "Интернет и связь",
        "кошки": "Кошки",
        "коты": "Кошки",
        "кот": "Кошки",
        "кошка": "Кошки",
        "котики": "Кошки",
        "долги": "Долги",
        "долг": "Долги",
        "одежда": "Одежда",
        "одеж": "Одежда",
        "шмот": "Одежда",
        "подарки": "Подарки",
        "подар": "Подарки",
        "подарок": "Подарки"
    }
    
    category = category_map.get(category_input, category_input.capitalize())

    logger.info(f"[PARSE] Mapped category: {category}")

    # Определяем тип по категории
    income_categories = ["Зарплата", "Чаевые", "Подработка", "Другое"]
    trans_type = "Доход" if category in income_categories else "Расход"

    logger.info(f"[PARSE] Type: {trans_type}")

    result = {
        "type": trans_type,
        "amount": amount,
        "category": category,
        "comment": comment,
        "hours": hours,
        "to_account": None
    }

    logger.info(f"[PARSE] Final result: {result}")

    return result


def format_history(transactions: List[Dict[str, Any]]) -> str:
    """Форматировать историю транзакций"""
    if not transactions:
        return "📜 История пуста"

    lines = ["📜 **ПОСЛЕДНИЕ ТРАНЗАКЦИИ**\n"]

    for t in transactions:
        emoji = {"Доход": "💰", "Расход": "💸", "Перевод": "🔄", "Обмен валюты": "💱"}.get(t["type"], "📝")

        # Используем full_date если есть, иначе только день
        date_str = t.get("full_date") or t['day']
        currency = t.get("currency", "BYN") or "BYN"
        line = f"{emoji} {date_str}: {t['amount']} {currency}"

        # Для обмена валюты показываем курс и сумму зачисления
        if t["type"] == "Обмен валюты" and t.get("amount_to") and t.get("exchange_rate"):
            line += f" → {t['amount_to']} (курс {t['exchange_rate']})"

        # Для расхода в валюте показываем эквивалент
        if t["type"] == "Расход" and currency != "BYN" and t.get("amount_to") and t.get("exchange_rate"):
            line += f" = {t['amount_to']} BYN (курс {t['exchange_rate']})"

        if t.get("category"):
            line += f" ({t['category']})"

        if t.get("comment"):
            line += f" - {t['comment']}"

        lines.append(line)

    return "\n".join(lines)


def format_income_by_days(data: Dict[str, Any]) -> str:
    """Форматировать статистику доходов по дням"""
    if not data.get("sorted_days"):
        return "💰 **ДОХОДЫ ПО ДНЯМ**\n\nДоходов за месяц пока нет"

    total_hours = data['total_hours']
    total_tips = data['total_tips']
    hourly_rate = total_tips / total_hours if total_hours > 0 else 0

    hours_line = f"⏰ Отработано: **{total_hours:.1f} ч**"
    if hourly_rate > 0:
        hours_line += f" → **{format_money(hourly_rate)}/ч**"

    lines = [
        "💰 **ДОХОДЫ ПО ДНЯМ**\n",
        f"📊 Всего за месяц: **{format_money(data['total_income'])}**",
        f"💵 Чаевые: **{format_money(total_tips)}**",
        hours_line + "\n"
    ]

    by_day = data["by_day"]
    sorted_days = data["sorted_days"]
    month = data.get("month", datetime.now().month)
    year = data.get("year", datetime.now().year)

    # Названия дней недели
    weekday_names = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"]

    for day in sorted_days:
        day_data = by_day[day]

        # Определяем день недели
        try:
            day_num = int(day)
            date_obj = datetime(year, month, day_num)
            weekday = weekday_names[date_obj.weekday()]
            day_header = f"**{day} ({weekday})**"
        except (ValueError, IndexError):
            day_header = f"**День {day}**"

        # Заголовок дня
        lines.append(f"\n📅 {day_header} — {format_money(day_data['total'])}")

        # Чаевые
        if day_data["tips"] > 0:
            hourly_calc = ""
            if day_data["hours"] > 0:
                day_rate = day_data["tips"] / day_data["hours"]
                hourly_calc = f" ({day_data['hours']:.1f}ч → {format_money(day_rate)}/ч)"

            lines.append(f"  💵 Чаевые: {format_money(day_data['tips'])}{hourly_calc}")

        # Другие доходы
        if day_data["other"] > 0:
            lines.append(f"  💼 Другое: {format_money(day_data['other'])}")

        # Детализация по записям
        for entry in day_data["entries"]:
            if entry.get("comment"):
                comment_emoji = "💬"
                lines.append(f"    {comment_emoji} {entry['comment']}")

    return "\n".join(lines)


def format_weekly_report(data: Dict[str, Any]) -> str:
    """Форматировать еженедельный отчет"""

    lines = [
        "📊 **ОТЧЕТ ЗА НЕДЕЛЮ**",
        f"📅 {data['start_day']}-{data['end_day']} число\n"
    ]

    # Предупреждение если данные обрезаны началом месяца
    if data.get('truncated'):
        lines.append("⚠️ _Неполная неделя (начало месяца)_\n")

    # Общая сводка
    balance = data['balance']
    balance_emoji = "📈" if balance >= 0 else "📉"

    lines.append(f"💰 **Доходы:** {format_money(data['total_income'])}")
    lines.append(f"💸 **Расходы:** {format_money(data['total_expense'])}")
    lines.append(f"{balance_emoji} **Итого:** {format_money(balance)}\n")

    # Часы работы (если есть)
    if data['total_hours'] > 0:
        hourly_rate = 6.5
        expected = data['total_hours'] * hourly_rate
        lines.append(f"⏰ **Отработано:** {data['total_hours']:.1f} часов")
        lines.append(f"   (= {format_money(expected)} по ставке)\n")

    # Доходы по категориям
    if data['income_by_category']:
        lines.append("💰 **Доходы по категориям:**")
        for category, amount in list(data['income_by_category'].items())[:5]:  # Топ-5
            lines.append(f"  • {category}: {format_money(amount)}")
        lines.append("")

    # Расходы по категориям
    if data['expense_by_category']:
        lines.append("💸 **Расходы по категориям:**")
        for category, amount in list(data['expense_by_category'].items())[:5]:  # Топ-5
            lines.append(f"  • {category}: {format_money(amount)}")
        lines.append("")

    # Мотивационное сообщение
    if balance > 0:
        lines.append("✅ Отличная работа! Доходы превышают расходы!")
    elif balance == 0:
        lines.append("⚖️ Баланс нулевой - всё что заработал, то и потратил.")
    else:
        lines.append("⚠️ Расходы превысили доходы. Держи контроль!")

    return "\n".join(lines)

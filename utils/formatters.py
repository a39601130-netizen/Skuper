"""
Утилиты для форматирования сообщений
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
import re

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
            if cat["budget"] > 0:  # Показываем только категории с бюджетом
                # Рассчитываем прогресс правильно
                spent = cat["spent"]
                budget = cat["budget"]
                progress = int((spent / budget) * 100) if budget > 0 else 0

                # Создаем шкалу прогресса
                filled = int(progress / 10)  # Сколько заполненных блоков (0-10)
                if filled > 10:
                    filled = 10
                empty = 10 - filled
                bar = "█" * filled + "░" * empty

                # Выбираем эмодзи и статус
                emoji = category_emoji.get(cat['name'], "📁")

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

    return "\n".join(lines)


def format_transaction_success(
    trans_type: str,
    amount: float,
    category: Optional[str],
    comment: Optional[str],
    hours: Optional[float] = None
) -> str:
    """Форматировать сообщение об успешной транзакции"""
    
    emoji = {"Доход": "💰", "Расход": "💸", "Перевод": "🔄"}.get(trans_type, "✅")
    
    lines = [
        "✅ **Записано!**\n",
        f"{emoji} {trans_type}: **{format_money(amount)}**"
    ]
    
    if category:
        lines.append(f"📁 Категория: {category}")
    
    if comment:
        lines.append(f"💬 {comment}")
    
    if hours:
        hourly_rate = 6.5  # Ставка в час
        earned = hours * hourly_rate
        lines.append(f"⏰ Часы: {hours} (= {format_money(earned)} по ставке)")
    
    lines.append(f"📅 {datetime.now().strftime('%d.%m.%Y')}")
    
    return "\n".join(lines)


def parse_quick_input(text: str) -> Optional[Dict[str, Any]]:
    """
    Парсинг быстрого ввода транзакции

    Форматы:
    - "50 продукты магазин" -> Расход 50, Продукты, комментарий "магазин"
    - "135 чаевые смена 10ч" -> Доход 135, Зарплата/Чаевые, 10 часов
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
    
    # Парсим сумму в начале
    amount_match = re.match(r'(\d+(?:\.\d+)?)\s+', text)
    if not amount_match:
        logger.info("[PARSE] No amount found at beginning")
        return None

    amount = float(amount_match.group(1))
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
        "чаевые": "Зарплата/Чаевые",
        "зарплата": "Зарплата/Чаевые",
        "зп": "Зарплата/Чаевые",
        "подработка": "Подработка",
        
        # Расходы
        "продукты": "Продукты",
        "еда": "Продукты",
        "магазин": "Продукты",
        "кафе": "Кафе",
        "ресторан": "Кафе",
        "досуг": "Досуг",
        "развлечения": "Досуг",
        "транспорт": "Транспорт",
        "метро": "Транспорт",
        "автобус": "Транспорт",
        "такси": "Такси",
        "здоровье": "Здоровье и красота",
        "аптека": "Аптека",
        "лекарства": "Аптека",
        "ништяки": "Ништяки",
        "покупки": "Покупки",
        "шоппинг": "Покупки",
        "аренда": "Аренда",
        "квартира": "Аренда",
        "коммуналка": "Коммуналка",
        "интернет": "Интернет и связь",
        "связь": "Интернет и связь",
        "телефон": "Интернет и связь",
        "кошки": "Кошки",
        "коты": "Кошки",
        "долги": "Долги",
        "долг": "Долги"
    }
    
    category = category_map.get(category_input, category_input.capitalize())

    logger.info(f"[PARSE] Mapped category: {category}")

    # Определяем тип по категории
    income_categories = ["Зарплата/Чаевые", "Подработка", "Другое"]
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
        emoji = {"Доход": "💰", "Расход": "💸", "Перевод": "🔄"}.get(t["type"], "📝")

        line = f"{emoji} {t['day']}.{t.get('month', '?')}: {t['amount']} BYN"

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

    lines = [
        "💰 **ДОХОДЫ ПО ДНЯМ**\n",
        f"📊 Всего за месяц: **{format_money(data['total_income'])}**",
        f"💵 Чаевые: **{format_money(data['total_tips'])}**",
        f"⏰ Отработано часов: **{data['total_hours']:.1f}** (= {format_money(data['total_hours'] * 6.5)})\n"
    ]

    by_day = data["by_day"]
    sorted_days = data["sorted_days"]

    # Эмодзи для дней недели (опционально, можно добавить если знаем день недели)
    day_emoji = "📅"

    for day in sorted_days:
        day_data = by_day[day]

        # Заголовок дня
        lines.append(f"\n{day_emoji} **День {day}** — {format_money(day_data['total'])}")

        # Чаевые
        if day_data["tips"] > 0:
            hourly_calc = ""
            if day_data["hours"] > 0:
                hourly_calc = f" ({day_data['hours']:.1f}ч × 6.5 = {format_money(day_data['hours'] * 6.5)})"

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

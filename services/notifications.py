"""
Система умных уведомлений с DeepSeek
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, Any
import httpx
import config
from services.sheets import get_sheets_service

logger = logging.getLogger(__name__)


async def generate_notification_text(notification_type: str, context: Dict[str, Any]) -> str:
    """
    Генерация текста уведомления через DeepSeek

    Args:
        notification_type: Тип уведомления (daily_reminder, budget_alert, etc.)
        context: Контекст для генерации (статистика, данные пользователя)

    Returns:
        Текст уведомления
    """

    # Промпты для разных типов уведомлений
    prompts = {
        "daily_reminder": f"""Напиши короткое (1-2 предложения) дружеское напоминание пользователю записать расходы за день.
Контекст: пользователь не записывал траты сегодня.
Будь неформальным, используй эмодзи. Не больше 100 символов.""",

        "tips_reminder": f"""Напиши короткое напоминание официанту записать чаевые после смены.
Контекст: пользователь работал сегодня {context.get('hours', '?')} часов.
Будь мотивирующим, используй эмодзи. Не больше 100 символов.""",

        "budget_alert": f"""Напиши предупреждение о том, что бюджет категории "{context.get('category')}" израсходован на {context.get('percent')}%.
Потрачено: {context.get('spent')} BYN из {context.get('budget')} BYN.
Будь тактичным, но серьезным. Используй эмодзи. Не больше 150 символов.""",

        "weekly_summary": f"""Напиши краткую еженедельную сводку:
- Доходы: {context.get('income')} BYN
- Расходы: {context.get('expenses')} BYN
- Баланс: {context.get('balance')} BYN
Будь позитивным и мотивирующим. Используй эмодзи. Не больше 200 символов.""",

        "month_end": f"""Напиши напоминание о приближении конца месяца.
До конца месяца: {context.get('days_left')} дней
Осталось денег: {context.get('remaining')} BYN
Будь мотивирующим, дай совет. Используй эмодзи. Не больше 150 символов."""
    }

    prompt = prompts.get(notification_type, "Напиши короткое напоминание о финансах.")

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {config.DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [
                        {"role": "system", "content": "Ты помощник по финансам. Пиши коротко, дружелюбно, с эмодзи."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.8,
                    "max_tokens": 150
                },
                timeout=10.0
            )

            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"].strip()
            else:
                logger.error(f"DeepSeek API error: {response.status_code}")
                return get_fallback_text(notification_type)

    except Exception as e:
        logger.error(f"Error generating notification: {e}")
        return get_fallback_text(notification_type)


def get_fallback_text(notification_type: str) -> str:
    """Запасные тексты на случай недоступности DeepSeek"""
    fallbacks = {
        "daily_reminder": "📝 Привет! Не забудь записать расходы за сегодня 😊",
        "tips_reminder": "💵 Время записать чаевые за смену! Сколько заработал?",
        "budget_alert": "⚠️ Внимание! Бюджет на исходе, контролируй траты!",
        "weekly_summary": "📊 Итоги недели готовы! Посмотри статистику",
        "month_end": "📅 Конец месяца близко! Планируй траты разумно"
    }
    return fallbacks.get(notification_type, "💰 Напоминание о финансах!")


async def check_daily_reminder(user_id: int) -> tuple[bool, Dict[str, Any]]:
    """
    Проверка: записывал ли пользователь траты сегодня

    Returns:
        (should_send, context)
    """
    try:
        sheets = get_sheets_service()
        today = datetime.now().day

        # Получаем транзакции за сегодня
        transactions = sheets.get_recent_transactions(20)
        today_transactions = [t for t in transactions if int(t.get("day", 0)) == today]

        # Если нет транзакций сегодня - отправляем напоминание
        if not today_transactions:
            return True, {}

        return False, {}

    except Exception as e:
        logger.error(f"Error checking daily reminder: {e}")
        return False, {}


async def check_tips_reminder(user_id: int) -> tuple[bool, Dict[str, Any]]:
    """
    Проверка: работал ли сегодня и записал ли чаевые

    Returns:
        (should_send, context)
    """
    try:
        sheets = get_sheets_service()
        today = datetime.now().day

        # Проверяем есть ли доходы за сегодня с категорией "Зарплата/Чаевые"
        transactions = sheets.get_recent_transactions(20)
        today_tips = [
            t for t in transactions
            if int(t.get("day", 0)) == today
            and t.get("type") == "Доход"
            and "Зарплата/Чаевые" in t.get("category", "")
        ]

        # Если работал, но не записал чаевые - напоминаем
        if not today_tips:
            # Предполагаем, что работал (можно улучшить логику)
            return True, {"hours": "8-10"}

        return False, {}

    except Exception as e:
        logger.error(f"Error checking tips reminder: {e}")
        return False, {}


async def check_budget_alerts(user_id: int) -> tuple[bool, Dict[str, Any]]:
    """
    Проверка превышения бюджетов

    Returns:
        (should_send, context)
    """
    try:
        sheets = get_sheets_service()
        data = sheets.get_monthly_summary()

        # Ищем категории с превышением 80%
        for cat in data.get("categories", []):
            if cat["type"] == "Расход" and cat["budget"] > 0:
                progress = cat["progress"]

                if progress >= 0.8 and progress < 1.0:  # 80-99%
                    return True, {
                        "category": cat["name"],
                        "percent": int(progress * 100),
                        "spent": cat["spent"],
                        "budget": cat["budget"]
                    }
                elif progress >= 1.0:  # 100%+
                    return True, {
                        "category": cat["name"],
                        "percent": int(progress * 100),
                        "spent": cat["spent"],
                        "budget": cat["budget"]
                    }

        return False, {}

    except Exception as e:
        logger.error(f"Error checking budget alerts: {e}")
        return False, {}


async def generate_weekly_summary(user_id: int) -> tuple[bool, Dict[str, Any]]:
    """
    Генерация еженедельной статистики

    Returns:
        (should_send, context)
    """
    try:
        sheets = get_sheets_service()
        data = sheets.get_monthly_summary()

        context = {
            "income": data.get("total_income", 0),
            "expenses": data.get("total_expense", 0),
            "balance": data.get("balance", 0)
        }

        return True, context

    except Exception as e:
        logger.error(f"Error generating weekly summary: {e}")
        return False, {}


async def check_month_end_reminder(user_id: int) -> tuple[bool, Dict[str, Any]]:
    """
    Проверка приближения конца месяца

    Returns:
        (should_send, context)
    """
    try:
        now = datetime.now()
        # Последний день месяца
        if now.month == 12:
            next_month = datetime(now.year + 1, 1, 1)
        else:
            next_month = datetime(now.year, now.month + 1, 1)

        last_day = (next_month - timedelta(days=1)).day
        days_left = last_day - now.day

        # Напоминаем за 5 дней до конца месяца
        if days_left <= 5:
            sheets = get_sheets_service()
            accounts = sheets.get_accounts_balance()
            total = sum(acc["current"] for acc in accounts if acc["currency"] == "BYN")

            context = {
                "days_left": days_left,
                "remaining": total
            }

            return True, context

        return False, {}

    except Exception as e:
        logger.error(f"Error checking month end: {e}")
        return False, {}

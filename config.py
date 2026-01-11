"""
Конфигурация Budget Bot
"""
import os
from dotenv import load_dotenv

load_dotenv()

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")  # ID пользователя для автоматических отчетов

# Google Sheets
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID")
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "google_credentials.json")

# DeepSeek AI
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# Настройки пользователя
USER_TIMEZONE = os.getenv("USER_TIMEZONE", "Europe/Minsk")
USER_NAME = os.getenv("USER_NAME", "Артур")

# Google Sheets - названия листов
SHEET_TRANSACTIONS = "Транзакции"
SHEET_CATEGORIES = "Категории"
SHEET_ACCOUNTS = "Счета"
SHEET_REFERENCES = "Справочники"
SHEET_DASHBOARD = "Дашборд"

# Типы транзакций
TRANSACTION_TYPES = {
    "income": "Доход",
    "expense": "Расход",
    "transfer": "Перевод"
}

# Emoji для типов
TYPE_EMOJI = {
    "Доход": "💰",
    "Расход": "💸",
    "Перевод": "🔄"
}

# Human Design профиль для AI советника
HUMAN_DESIGN_CONTEXT = """
Пользователь - Артур Султанов, Эмоциональный Проектор 2/4.
Ключевые особенности:
- Тип: Проектор (ограниченная энергия, максимум 2-3 часа продуктивной работы)
- Авторитет: Эмоциональный (важно дать время на обдумывание решений 24-72 часа)
- Профиль: 2/4 (Отшельник-Оппортунист)
- Стратегия: Ждать приглашения, не инициировать

При даче советов:
- Напоминай о необходимости времени на решения
- Учитывай ограниченность энергии
- Фокусируйся на качестве, не количестве
- Давай практичные, конкретные советы
- Будь поддерживающим, но честным
"""

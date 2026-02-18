"""
Life Manager Bot - Конфигурация
Объединяет финансы и тренировки
"""
import os
from dotenv import load_dotenv

load_dotenv()

# ============================================
# TELEGRAM
# ============================================
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_USER_ID = os.getenv("TELEGRAM_USER_ID")

# ============================================
# GOOGLE SHEETS
# ============================================
GOOGLE_CREDENTIALS_FILE = os.getenv("GOOGLE_CREDENTIALS_FILE", "google_credentials.json")

# Финансы (основная таблица)
GOOGLE_SHEETS_ID = os.getenv("GOOGLE_SHEETS_ID")
GOOGLE_SHEETS_FINANCE_ID = os.getenv("GOOGLE_SHEETS_FINANCE_ID", os.getenv("GOOGLE_SHEETS_ID"))

# Тренировки (отдельная таблица)
GOOGLE_SHEETS_WORKOUT_ID = os.getenv("GOOGLE_SHEETS_WORKOUT_ID")

# Листы для финансов
SHEET_TRANSACTIONS = "Транзакции"
SHEET_CATEGORIES = "Категории"
SHEET_ACCOUNTS = "Счета"
SHEET_REFERENCES = "Справочники"
SHEET_DASHBOARD = "Дашборд"

# Листы для тренировок
SHEET_EXERCISES = "Упражнения"
SHEET_WORKOUTS = "Тренировки"
SHEET_SETS = "Подходы"
SHEET_CURRENT_WEIGHTS = "Текущие веса"
SHEET_PHASES = "Фазы"
SHEET_WARMUP = "Разминка"
SHEET_DASHBOARD_WORKOUT = "Дашборд"
SHEET_BOT_CONFIG = "Бот конфиг"

# ============================================
# DEEPSEEK AI
# ============================================
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-chat"         # Быстрые вопросы
DEEPSEEK_REASONER = "deepseek-reasoner"  # Глубокий анализ (/advisor)

# ============================================
# НАСТРОЙКИ ПОЛЬЗОВАТЕЛЯ
# ============================================
USER_TIMEZONE = os.getenv("USER_TIMEZONE", "Europe/Minsk")
USER_NAME = os.getenv("USER_NAME", "Артур")

# ============================================
# ТИПЫ ТРАНЗАКЦИЙ
# ============================================
TRANSACTION_TYPES = {
    "income": "Доход",
    "expense": "Расход",
    "transfer": "Перевод"
}

TYPE_EMOJI = {
    "Доход": "💰",
    "Расход": "💸",
    "Перевод": "🔄"
}

# ============================================
# HUMAN DESIGN КОНТЕКСТ (для AI)
# ============================================
HUMAN_DESIGN_CONTEXT = """
Пользователь - Артур Султанов, Эмоциональный Проектор 2/4.

КЛЮЧЕВЫЕ ОСОБЕННОСТИ:
- Тип: Проектор (ограниченная энергия, максимум 2-3 часа продуктивной работы)
- Авторитет: Эмоциональный (важно дать время на обдумывание решений 24-72 часа)
- Профиль: 2/4 (Отшельник-Оппортунист)
- Стратегия: Ждать приглашения, не инициировать
- Диета: Touch-Calm (спокойная обстановка для еды)
- Окружение: Valleys-Narrow (уютные, узкие пространства)

ДЛЯ ТРЕНИРОВОК:
- Максимум 45-60 минут тренировки
- Остановиться ДО усталости — после неё восстановление дольше
- 48-72 часа между тренировками
- Энергия < 5 → рекомендовать перенос или сокращение
- RPE 9+ три раза подряд → предупреждение о перегрузке

ПРИ ДАЧЕ СОВЕТОВ:
- Напоминай о необходимости времени на решения
- Учитывай ограниченность энергии
- Фокусируйся на качестве, не количестве
- Давай практичные, конкретные советы
- Будь поддерживающим, но честным
"""

# ============================================
# ТРЕНИРОВКИ - КОНСТАНТЫ
# ============================================
WORKOUT_PHASES = {
    "intro": {"name": "Знакомство", "weeks": "1-2", "rpe_min": 5, "rpe_max": 6, "sets_modifier": 0.5},
    "base": {"name": "Построение базы", "weeks": "3-4", "rpe_min": 6, "rpe_max": 7, "sets_modifier": 1.0},
    "develop": {"name": "Развитие", "weeks": "5-8", "rpe_min": 7, "rpe_max": 8, "sets_modifier": 1.0},
    "deload": {"name": "Разгрузка", "weeks": "9", "rpe_min": 6, "rpe_max": 7, "sets_modifier": 0.5},
}

# Время отдыха по умолчанию (секунды)
REST_TIMES = {
    "heavy": 150,    # Тяжёлые базовые (жим, присед, тяга)
    "medium": 90,    # Средние базовые
    "isolation": 60  # Изоляция
}

# Шаги прибавки веса (кг)
WEIGHT_STEPS = {
    "base": 2.5,      # Базовые упражнения
    "isolation": 1.0  # Изоляция
}

# ============================================
# ТРИГГЕРЫ ДЛЯ DEEPSEEK
# ============================================
AI_TRIGGERS = {
    "low_energy": 5,           # Энергия ниже этого → AI предупреждение
    "high_rpe_streak": 3,      # RPE 9+ подряд столько раз → AI совет
    "back_pain_threshold": 5,  # Боль в спине выше → AI адаптация
    "weekly_analysis": True,   # Еженедельный анализ
    "phase_transition": True,  # При переходе в новую фазу
}

"""
Состояния для ConversationHandler
"""
import time
from enum import IntEnum, auto

class TransactionStates(IntEnum):
    """Состояния при добавлении транзакции"""
    SELECT_TYPE = auto()       # Выбор типа (доход/расход/перевод/обмен)
    SELECT_DATE = auto()       # Выбор даты (сегодня или другой день)
    SELECT_ACCOUNT = auto()    # Выбор счета списания
    SELECT_CATEGORY = auto()   # Выбор категории
    ENTER_AMOUNT = auto()      # Ввод суммы
    SELECT_TO_ACCOUNT = auto() # Выбор счета зачисления (для переводов/обмена)
    ENTER_COMMENT = auto()     # Ввод комментария
    ENTER_HOURS = auto()       # Ввод часов (для доходов)
    ENTER_EXCHANGE_RATE = auto()  # Ввод курса обмена
    ENTER_AMOUNT_TO = auto()      # Ввод суммы зачисления
    SELECT_CURRENCY = auto()      # Выбор валюты
    CONFIRM = auto()           # Подтверждение


class AdvisorStates(IntEnum):
    """Состояния для AI советника"""
    WAITING_QUESTION = auto()  # Ожидание вопроса


class WorkoutStates(IntEnum):
    """Состояния для тренировки"""
    # Начало тренировки
    ENERGY_BEFORE = auto()      # Ввод энергии до
    SLEEP_HOURS = auto()        # Часы сна
    SLEEP_QUALITY = auto()      # Качество сна
    BACK_PAIN = auto()          # Боль в спине
    EMOTIONAL_WAVE = auto()     # Эмоциональная волна

    # Разминка
    WARMUP_PHASE1 = auto()      # Кардио
    WARMUP_PHASE2 = auto()      # McGill Big 3
    WARMUP_PHASE3 = auto()      # Подготовка к движению
    WARMUP_PHASE4 = auto()      # Специфическая

    # Основная часть
    EXERCISE_START = auto()     # Показ упражнения
    SET_INPUT = auto()          # Ввод веса и повторений
    SET_RPE = auto()            # Ввод RPE
    SET_NOTES = auto()          # Заметки к подходу
    REST_TIMER = auto()         # Таймер отдыха
    EXERCISE_COMPLETE = auto()  # Упражнение завершено

    # Завершение
    ENERGY_AFTER = auto()       # Энергия после
    WORKOUT_NOTES = auto()      # Общие заметки
    WORKOUT_COMPLETE = auto()   # Тренировка завершена


class SettingsStates(IntEnum):
    """Состояния для настроек"""
    MAIN_SETTINGS = auto()
    EDIT_ACCOUNTS = auto()
    EDIT_CATEGORIES = auto()


# Данные транзакции в процессе создания
class TransactionData:
    """Хранение данных транзакции во время диалога"""

    def __init__(self):
        self.reset()

    def reset(self):
        self.trans_type: str = None       # Доход/Расход/Перевод/Обмен валюты
        self.account: str = None          # Счёт списания
        self.category: str = None         # Категория
        self.amount: float = None         # Сумма списания
        self.to_account: str = None       # Счёт зачисления
        self.comment: str = None          # Комментарий
        self.hours: float = None          # Часы работы
        self.day: int = None              # День месяца
        self.exchange_rate: float = None  # Курс обмена
        self.amount_to: float = None      # Сумма зачисления
        self.currency: str = "BYN"        # Валюта операции
        self.created_at: float = time.time()  # Время создания для очистки

    def to_dict(self):
        return {
            "type": self.trans_type,
            "account": self.account,
            "category": self.category,
            "amount": self.amount,
            "to_account": self.to_account,
            "comment": self.comment,
            "hours": self.hours,
            "day": self.day,
            "exchange_rate": self.exchange_rate,
            "amount_to": self.amount_to,
            "currency": self.currency
        }

    def format_preview(self) -> str:
        """Форматировать превью транзакции"""
        emoji = {"Доход": "💰", "Расход": "💸", "Перевод": "🔄", "Обмен валюты": "💱"}.get(self.trans_type, "📝")

        lines = [
            f"{emoji} **{self.trans_type}**",
            f"📅 Дата: {self.day} число",
            f"💵 Сумма: **{self.amount}** {self.currency}",
            f"💳 Счёт: {self.account}"
        ]

        if self.category:
            lines.append(f"📁 Категория: {self.category}")

        if self.to_account:
            lines.append(f"➡️ На счёт: {self.to_account}")

        # Для обмена валюты показываем детали
        if self.trans_type == "Обмен валюты":
            if self.exchange_rate:
                lines.append(f"📊 Курс: {self.exchange_rate}")
            if self.amount_to:
                # Определяем валюту зачисления
                to_currency = self._get_to_currency()
                lines.append(f"💵 Получено: **{self.amount_to}** {to_currency}")

        # Для расхода в иностранной валюте показываем эквивалент в BYN
        if self.trans_type == "Расход" and self.currency != "BYN":
            if self.exchange_rate:
                lines.append(f"📊 Курс: {self.exchange_rate}")
            if self.amount_to:
                lines.append(f"💰 Эквивалент: **{self.amount_to:.2f}** BYN")

        if self.comment:
            lines.append(f"💬 Комментарий: {self.comment}")

        if self.hours:
            lines.append(f"⏰ Часы: {self.hours}")

        return "\n".join(lines)

    def _get_to_currency(self) -> str:
        """Определить валюту счёта зачисления"""
        if not self.to_account:
            return "BYN"
        try:
            from services.sheets import get_sheets_service
            sheets = get_sheets_service()
            return sheets.get_account_currency(self.to_account)
        except Exception:
            # Фоллбэк по имени счёта
            acc_upper = self.to_account.upper()
            if "USD" in acc_upper or "ДОЛЛАР" in acc_upper:
                return "USD"
            if "EUR" in acc_upper or "ЕВРО" in acc_upper:
                return "EUR"
            if "RUB" in acc_upper or "РУБЛ" in acc_upper:
                return "RUB"
            return "BYN"

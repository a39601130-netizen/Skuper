"""
Состояния для ConversationHandler
"""
from enum import IntEnum, auto

class TransactionStates(IntEnum):
    """Состояния при добавлении транзакции"""
    SELECT_TYPE = auto()      # Выбор типа (доход/расход/перевод)
    SELECT_DATE = auto()      # Выбор даты (сегодня или другой день)
    SELECT_ACCOUNT = auto()   # Выбор счета списания
    SELECT_CATEGORY = auto()  # Выбор категории
    ENTER_AMOUNT = auto()     # Ввод суммы
    SELECT_TO_ACCOUNT = auto() # Выбор счета зачисления (для переводов)
    ENTER_COMMENT = auto()    # Ввод комментария
    ENTER_HOURS = auto()      # Ввод часов (для доходов)
    CONFIRM = auto()          # Подтверждение


class AdvisorStates(IntEnum):
    """Состояния для AI советника"""
    WAITING_QUESTION = auto()  # Ожидание вопроса


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
        self.trans_type: str = None    # Доход/Расход/Перевод
        self.account: str = None        # Счёт списания
        self.category: str = None       # Категория
        self.amount: float = None       # Сумма
        self.to_account: str = None     # Счёт зачисления
        self.comment: str = None        # Комментарий
        self.hours: float = None        # Часы работы
        self.day: int = None            # День месяца
    
    def to_dict(self):
        return {
            "type": self.trans_type,
            "account": self.account,
            "category": self.category,
            "amount": self.amount,
            "to_account": self.to_account,
            "comment": self.comment,
            "hours": self.hours,
            "day": self.day
        }
    
    def format_preview(self) -> str:
        """Форматировать превью транзакции"""
        emoji = {"Доход": "💰", "Расход": "💸", "Перевод": "🔄"}.get(self.trans_type, "📝")
        
        lines = [
            f"{emoji} **{self.trans_type}**",
            f"📅 Дата: {self.day} число",
            f"💵 Сумма: **{self.amount}** BYN",
            f"💳 Счёт: {self.account}"
        ]
        
        if self.category:
            lines.append(f"📁 Категория: {self.category}")
        
        if self.to_account:
            lines.append(f"➡️ На счёт: {self.to_account}")
        
        if self.comment:
            lines.append(f"💬 Комментарий: {self.comment}")
        
        if self.hours:
            lines.append(f"⏰ Часы: {self.hours}")
        
        return "\n".join(lines)

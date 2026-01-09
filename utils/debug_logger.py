"""
Система отладки и логирования багов
Сохраняет подробную информацию об ошибках для последующего анализа
"""
import logging
import json
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any

# Папка для логов
LOGS_DIR = Path(__file__).parent.parent / "logs"
LOGS_DIR.mkdir(exist_ok=True)

# Файлы логов
DEBUG_LOG = LOGS_DIR / "debug.log"
BUGS_LOG = LOGS_DIR / "bugs.json"


class BugTracker:
    """Трекер багов с сохранением контекста"""

    def __init__(self):
        self.bugs = []
        self._load_bugs()

    def _load_bugs(self):
        """Загрузить сохраненные баги"""
        if BUGS_LOG.exists():
            try:
                with open(BUGS_LOG, 'r', encoding='utf-8') as f:
                    self.bugs = json.load(f)
            except:
                self.bugs = []

    def _save_bugs(self):
        """Сохранить баги"""
        with open(BUGS_LOG, 'w', encoding='utf-8') as f:
            json.dump(self.bugs, f, ensure_ascii=False, indent=2)

    def log_bug(
        self,
        error: Exception,
        context: Optional[Dict[str, Any]] = None,
        user_id: Optional[int] = None,
        handler: Optional[str] = None
    ):
        """
        Записать баг с полным контекстом

        Args:
            error: Исключение
            context: Дополнительный контекст (user_data, состояние и т.д.)
            user_id: ID пользователя
            handler: Название обработчика где произошла ошибка
        """
        bug_entry = {
            "timestamp": datetime.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
            "user_id": user_id,
            "handler": handler,
            "context": context or {},
            "resolved": False
        }

        self.bugs.append(bug_entry)
        self._save_bugs()

        # Логируем в файл
        logging.error(
            f"\n{'='*60}\n"
            f"БАГ ОБНАРУЖЕН!\n"
            f"Время: {bug_entry['timestamp']}\n"
            f"Обработчик: {handler}\n"
            f"Пользователь: {user_id}\n"
            f"Ошибка: {error}\n"
            f"Контекст: {json.dumps(context, ensure_ascii=False, indent=2)}\n"
            f"Traceback:\n{bug_entry['traceback']}\n"
            f"{'='*60}\n"
        )

    def get_unresolved_bugs(self):
        """Получить список нерешенных багов"""
        return [b for b in self.bugs if not b.get("resolved")]

    def mark_resolved(self, index: int):
        """Отметить баг как решенный"""
        if 0 <= index < len(self.bugs):
            self.bugs[index]["resolved"] = True
            self.bugs[index]["resolved_at"] = datetime.now().isoformat()
            self._save_bugs()

    def clear_resolved(self):
        """Удалить решенные баги"""
        self.bugs = [b for b in self.bugs if not b.get("resolved")]
        self._save_bugs()


# Глобальный трекер
bug_tracker = BugTracker()


def setup_debug_logging():
    """Настроить детальное логирование в файл"""

    # Создаем файловый handler
    file_handler = logging.FileHandler(
        DEBUG_LOG,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)

    # Формат с максимумом информации
    formatter = logging.Formatter(
        '%(asctime)s | %(name)s | %(levelname)s | %(funcName)s:%(lineno)d | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)

    # Добавляем к root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)
    root_logger.setLevel(logging.DEBUG)

    logging.info("="*60)
    logging.info("БОТ ЗАПУЩЕН - Система отладки активирована")
    logging.info("="*60)


def log_conversation_state(user_id: int, state: Any, handler: str, data: Dict = None):
    """Логировать состояние ConversationHandler"""
    logging.info(
        f"ConversationHandler | User: {user_id} | Handler: {handler} | "
        f"State: {state} | Data: {data}"
    )

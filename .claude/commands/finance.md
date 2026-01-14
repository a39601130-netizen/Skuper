# Финансовый бот - инструкция для отладки

## Файлы для изучения (в порядке приоритета):

### Основные хендлеры:
- `bot/handlers/transactions.py` - добавление транзакций (доходы/расходы/переводы/обмен)
- `bot/handlers/balance.py` - работа с балансом
- `bot/handlers/reports.py` - отчёты
- `bot/handlers/advisor.py` - AI советник

### Сервисы:
- `services/sheets.py` - работа с Google Sheets (класс `GoogleSheetsService`)
- `services/ai_advisor.py` - интеграция с DeepSeek AI

### Клавиатуры:
- `bot/keyboards/menus.py` - все меню для финансов

### Утилиты:
- `utils/formatters.py` - форматирование сообщений, парсинг quick input
- `utils/debug_logger.py` - логирование ошибок

---

## FSM состояния (TransactionStates):

```
SELECT_TYPE → SELECT_DATE → SELECT_ACCOUNT → SELECT_CATEGORY → ENTER_AMOUNT → ENTER_COMMENT → CONFIRM
                                ↓
                          SELECT_TO_ACCOUNT (для переводов)
                                ↓
                          SELECT_CURRENCY → ENTER_EXCHANGE_RATE → ENTER_AMOUNT_TO (для обмена валюты)
```

### Состояния:
- `SELECT_TYPE` - выбор типа (Доход/Расход/Перевод/Обмен валюты)
- `SELECT_DATE` - выбор даты (сегодня/вчера/позавчера/другой день)
- `SELECT_ACCOUNT` - выбор счёта списания
- `SELECT_CATEGORY` - выбор категории
- `ENTER_AMOUNT` - ввод суммы
- `SELECT_TO_ACCOUNT` - выбор счёта зачисления (переводы/обмен)
- `SELECT_CURRENCY` - выбор валюты (BYN/USD/EUR/RUB)
- `ENTER_EXCHANGE_RATE` - ввод курса обмена
- `ENTER_AMOUNT_TO` - ввод суммы зачисления
- `ENTER_COMMENT` - ввод комментария
- `ENTER_HOURS` - ввод часов (для дохода "Зарплата/Чаевые")
- `CONFIRM` - подтверждение

---

## Callback patterns:

### Типы транзакций:
- `add_expense` - расход
- `add_income` - доход
- `add_transfer` - перевод
- `add_exchange` - обмен валюты

### Даты:
- `date_today`, `date_yesterday`, `date_before_yesterday`
- `date_N` - конкретный день (N = 1-31)
- `date_custom` - ввод вручную

### Счета:
- `expense_ИмяСчета` - счёт для расхода
- `income_ИмяСчета` - счёт для дохода
- `from_ИмяСчета` - счёт списания (перевод)
- `to_ИмяСчета` - счёт зачисления (перевод)
- `exchange_from_ИмяСчета` - счёт списания (обмен)
- `exchange_to_ИмяСчета` - счёт зачисления (обмен)

### Категории:
- `quick_Категория` - быстрые категории расходов
- `cat_Категория` - полный список категорий
- `show_all_categories` - показать все категории

### Валюты:
- `currency_BYN`, `currency_USD`, `currency_EUR`, `currency_RUB`

### Подтверждение:
- `confirm_yes` - подтвердить
- `confirm_no` - отменить
- `confirm_edit` - редактировать

---

## Google Sheets структура:

### Таблица: `config.GOOGLE_SHEETS_ID`

| Лист | Константа | Описание |
|------|-----------|----------|
| Транзакции | `SHEET_TRANSACTIONS` | Все операции |
| Категории | `SHEET_CATEGORIES` | Бюджеты по категориям |
| Счета | `SHEET_ACCOUNTS` | Балансы счетов |
| Справочники | `SHEET_REFERENCES` | Типы, счета, категории |
| Дашборд | `SHEET_DASHBOARD` | Сводка |

### Структура листа "Транзакции":
| Колонка | Содержимое |
|---------|------------|
| A | День (1-31) |
| B | Тип (Доход/Расход/Перевод/Обмен валюты) |
| C | Счёт |
| D | Категория |
| E | Сумма |
| F | Счёт Куда |
| G | Комментарий |
| H | Полная дата (формула) |
| I | Часы |
| J | Часы×6.5 (формула) |
| K | Курс обмена |
| L | Сумма зачисления |
| M | Валюта |

**Важно:** Строки 1-3 - настройки/заголовки, данные начинаются с 4-й строки.

---

## Хранение данных транзакции:

```python
class TransactionData:
    trans_type: str       # Доход/Расход/Перевод/Обмен валюты
    account: str          # Счёт списания
    category: str         # Категория
    amount: float         # Сумма списания
    to_account: str       # Счёт зачисления
    comment: str          # Комментарий
    hours: float          # Часы работы
    day: int              # День месяца
    exchange_rate: float  # Курс обмена
    amount_to: float      # Сумма зачисления
    currency: str         # Валюта (по умолчанию "BYN")
```

Хранится в `user_transactions[user_id]` (глобальный словарь).

---

## Типичные проблемы и решения:

### 1. Транзакция не сохраняется
- Проверь `trans.to_dict()` перед записью
- Смотри логи в `bug_tracker.log_bug()`

### 2. FSM застревает
- Проверь возврат правильного состояния из хендлера
- Убедись что `ConversationHandler.END` возвращается при ошибке

### 3. Callback не обрабатывается
- Проверь pattern в `ConversationHandler`
- Логируй `query.data` для отладки

### 4. Ошибка Google Sheets API
- Проверь переподключение (`_ensure_connection()`)
- Смотри декоратор `@retry_on_error`

### 5. Quick input не работает
- Проверь `parse_quick_input()` в `utils/formatters.py`
- Формат: "сумма категория" или "сумма"

---

## Ключевые функции:

### sheets.py:
- `get_sheets_service()` - singleton сервиса
- `add_transaction()` - добавить транзакцию
- `get_references()` - получить справочники
- `get_accounts_balance()` - балансы счетов
- `get_categories_budget()` - бюджеты категорий
- `get_recent_transactions()` - последние транзакции
- `delete_transaction()` - удалить транзакцию

### transactions.py:
- `get_user_transaction(user_id)` - получить/создать TransactionData
- `menu_add_callback()` - точка входа из меню
- `show_confirmation()` - показать превью перед сохранением

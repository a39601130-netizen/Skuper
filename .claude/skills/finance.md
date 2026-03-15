# Финансовый бот — режим отладки

Жди описание проблемы от пользователя. НЕ читай файлы из workout-части.

## Файлы (в порядке приоритета)

### Хендлеры бота:
- `bot/handlers/transactions.py` — /add, быстрый ввод, ConversationHandler
- `bot/handlers/balance.py` — /balance, /stats, /history, /income
- `bot/handlers/reports.py` — /report
- `bot/handlers/advisor.py` — /advisor

### БД сервисы (PostgreSQL — primary):
- `db/services/finance.py` — CRUD: get_accounts, add_transaction, get_monthly_summary, get_category_spending, get_daily_spending, get_income_by_days, get_weekly_summary
- `db/models.py` — Account, Category, Transaction, RecurringTransaction

### API роутеры:
- `api/routers/transactions.py` — GET/POST/DELETE /api/transactions
- `api/routers/categories.py` — GET /api/categories, /api/categories/references
- `api/routers/stats.py` — GET /api/stats/monthly|income|weekly|daily-spending
- `api/routers/accounts.py` — GET /api/accounts
- `api/routers/recurring.py` — CRUD повторяющихся транзакций

### Прочее:
- `bot/keyboards/menus.py` — клавиатуры финансов
- `utils/formatters.py` — форматирование, parse_quick_input()
- `services/sheets.py` — Google Sheets (legacy backup)

## FSM (TransactionStates)

```
SELECT_TYPE → SELECT_DATE → SELECT_ACCOUNT → SELECT_CATEGORY → ENTER_AMOUNT → ENTER_COMMENT → CONFIRM
                                  ↓ (перевод)
                            SELECT_TO_ACCOUNT
                                  ↓ (обмен)
                            SELECT_CURRENCY → ENTER_EXCHANGE_RATE → ENTER_AMOUNT_TO
```

Состояния: SELECT_TYPE, SELECT_DATE, SELECT_ACCOUNT, SELECT_CATEGORY, ENTER_AMOUNT, SELECT_TO_ACCOUNT, SELECT_CURRENCY, ENTER_EXCHANGE_RATE, ENTER_AMOUNT_TO, ENTER_COMMENT, ENTER_HOURS (для Зарплата/Чаевые), CONFIRM.

## Callback patterns

- Типы: `add_expense`, `add_income`, `add_transfer`, `add_exchange`
- Даты: `date_today`, `date_yesterday`, `date_before_yesterday`, `date_N`, `date_custom`
- Счета: `expense_Имя`, `income_Имя`, `from_Имя`, `to_Имя`, `exchange_from_Имя`, `exchange_to_Имя`
- Категории: `quick_Категория`, `cat_Категория`, `show_all_categories`
- Валюты: `currency_BYN|USD|EUR|RUB`
- Подтверждение: `confirm_yes|no|edit`

## Типичные проблемы

1. **Транзакция не сохраняется** — проверь add_transaction() в db/services/finance.py
2. **FSM застревает** — проверь return правильного состояния, ConversationHandler.END при ошибке
3. **Callback не обрабатывается** — проверь pattern в ConversationHandler, логируй query.data
4. **Quick input не работает** — проверь parse_quick_input() в formatters.py
5. **ImportError в роутере** — убедись что функция существует в db/services/finance.py

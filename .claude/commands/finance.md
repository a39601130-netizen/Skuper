# Финансы — инструкция для отладки

## Архитектура
Весь UI финансов — в **Mini App** (React). Бот не участвует.

## Файлы для изучения (в порядке приоритета):

### API роутеры:
- `api/routers/transactions.py` — GET/POST/DELETE /api/transactions (фильтры, валидация)
- `api/routers/accounts.py` — GET /api/accounts
- `api/routers/categories.py` — GET /api/categories, GET /api/categories/references
- `api/routers/stats.py` — GET /api/stats/monthly|income|weekly|daily-spending
- `api/routers/recurring.py` — GET/POST /api/recurring, DELETE, POST apply
- `api/routers/advisor.py` — POST /api/advisor/ask, GET analysis, GET insights

### Сервис (БД):
- `db/services/finance.py` — вся бизнес-логика финансов (async, SQLAlchemy)
  - `get_accounts(db)` — список счетов с балансами
  - `add_transaction(db, ...)` — добавить транзакцию (обновляет балансы)
  - `get_monthly_summary(db, year, month)` — сводка за месяц
  - `get_category_spending(db, year, month)` — расходы по категориям
  - `get_daily_spending(db, year, month)` — расходы по дням
- `db/services/recurring.py` — CRUD повторяющихся транзакций + apply

### Frontend:
- `frontend/src/pages/DashboardPage.tsx` — сводка, счета, категории, графики, AI инсайты
- `frontend/src/pages/HistoryPage.tsx` — транзакции с фильтрами и свайп-удалением
- `frontend/src/pages/AddTransactionPage.tsx` — пошаговый ввод транзакции
- `frontend/src/pages/AdvisorPage.tsx` — AI советник
- `frontend/src/api/client.ts` — API вызовы
- `frontend/src/components/charts/` — ExpensePieChart, SpendingTrendChart

### Модели (db/models.py):
- **Account** — id, name, balance, currency
- **Category** — id, name, type (Расход/Доход/Перевод), emoji, budget_limit
- **Transaction** — id, date, type, account_id, category_id, amount, comment, hours, synced_to_sheets
- **RecurringTransaction** — id, name, type, account_id, category_id, amount, currency, frequency, next_date, is_active

### Сервисы:
- `services/ai_advisor.py` — AIAdvisor (DeepSeek API)
- `services/sheets.py` — GoogleSheetsService (бэкап)
- `services/backup.py` — BackupService.backup_finances()

### Утилиты:
- `utils/formatters.py` — форматирование, parse_quick_input()
- `utils/timezone.py` — now_minsk(), today_minsk()

---

## Ключевые константы (config.py):
- `BASE_HOURLY_RATE = 6.5` — ставка BYN/ч
- `CATEGORY_EMOJI` — маппинг категория→эмодзи

## API Authentication:
`X-Telegram-Init-Data` → HMAC-SHA256 → проверка TELEGRAM_USER_ID

---

## Типичные проблемы:

### 1. Транзакция не сохраняется
- Проверь `db/services/finance.py:add_transaction()`
- Проверь `api/routers/transactions.py` POST endpoint
- Проверь обновление баланса счёта

### 2. Статистика неправильная
- Проверь `db/services/finance.py:get_monthly_summary()`
- Проверь фильтрацию по дате (timezone!)

### 3. Категории не загружаются
- Проверь `api/routers/categories.py`
- Проверь seed данные в `db/seed.py`

### 4. AI советник не отвечает
- Проверь `services/ai_advisor.py` — DeepSeek API ключ
- Проверь `api/routers/advisor.py` endpoints

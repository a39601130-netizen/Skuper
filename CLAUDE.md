# Budget Bot — Справочник проекта

## Что это
Telegram Mini App + Bot для управления финансами и тренировками. Один пользователь (Артур).
- **Mini App**: React 19 + TypeScript → доступна через Telegram WebApp
- **Bot**: python-telegram-bot v20+ (async) — polling, работает параллельно
- **БД**: PostgreSQL (primary) + Google Sheets (опциональный экспорт/бэкап)
- **AI**: DeepSeek как советник

## Стек
- **Frontend**: React 19, TypeScript, Vite 6, react-router-dom 7
- **Backend**: FastAPI + uvicorn, SQLAlchemy 2.0 async, asyncpg
- **Bot**: python-telegram-bot v20+ (async)
- **DB**: PostgreSQL 16 + Google Sheets (backup)
- **AI**: DeepSeek API (deepseek-chat + deepseek-reasoner)
- **Deploy**: Docker Compose + Caddy reverse proxy

## URL
- Mini App: https://budget-bot.duckdns.org
- API: https://budget-bot.duckdns.org/api/*

## Структура файлов

```
run.py                           — Entry point: FastAPI + Bot polling параллельно
config.py                        — Конфигурация (DATABASE_URL, MINI_APP_URL, BASE_HOURLY_RATE...)
Dockerfile                       — Multi-stage: Node 20 (frontend) → Python 3.11 (backend)
docker-compose.yml               — budget_postgres + budget_bot + caddy
Caddyfile                        — budget-bot.duckdns.org → budget_bot:8000
requirements.txt

api/
  app.py                         — FastAPI приложение, SPA fallback, CORS, все роутеры
  auth.py                        — HMAC-SHA256 валидация Telegram initData
  deps.py                        — get_current_user(), get_ai()
  routers/
    health.py                    — GET /api/health
    transactions.py              — GET/POST/DELETE /api/transactions (с фильтрами, валидацией)
    accounts.py                  — GET /api/accounts
    categories.py                — GET /api/categories (реальные расходы), GET /api/categories/references
    stats.py                     — GET /api/stats/monthly|income|weekly|daily-spending
    workouts.py                  — GET/POST /api/workouts, PUT /api/workouts/{id}/complete,
                                   POST /api/workouts/{id}/sets, GET /api/workouts/calendar,
                                   GET /api/workouts/{id}/compare
    exercises.py                 — GET /api/exercises, GET /api/exercises/{id}/progress,
                                   PUT /api/exercises/{id}/weight
    advisor.py                   — POST /api/advisor/ask, GET /api/advisor/analysis,
                                   GET /api/advisor/insights
    recurring.py                 — GET/POST /api/recurring, DELETE /api/recurring/{id},
                                   POST /api/recurring/{id}/apply

db/
  database.py                    — engine, async_session, Base, get_db(), init_db()
  models.py                      — ORM: Account, Category, Transaction, Exercise, Phase,
                                   Workout, WorkoutSet, CurrentWeight, SheetsSyncLog
  seed.py                        — Начальные данные: счета, категории, фазы
  services/
    finance.py                   — get_accounts, add_transaction, get_monthly_summary,
                                   get_category_spending, get_daily_spending...
    workout.py                   — get_exercises, determine_next_day, get_current_weights,
                                   create_workout, complete_workout, add_workout_set,
                                   get_workout_with_sets, get_workouts_for_month,
                                   get_workout_comparison...
    recurring.py                 — CRUD повторяющихся транзакций + apply logic

frontend/
  package.json                   — React 19, react-router-dom 7, Vite 6
  vite.config.ts                 — proxy /api → localhost:8000
  src/
    main.tsx                     — Инициализация Telegram WebApp, рендер App
    App.tsx                      — Routes: 6 страниц (+ /workout/session)
    api/client.ts                — Все API вызовы с X-Telegram-Init-Data заголовком
    hooks/useTelegram.ts         — useTelegram(): tg, user, haptic
    components/
      BottomNav.tsx              — 5 вкладок навигации
      SwipeableListItem.tsx      — Свайп для удаления (touch events, 0 зависимостей)
      InsightsCard.tsx           — AI инсайты на Dashboard
      RecurringTransactionsList.tsx — Управление повторяющимися транзакциями
      charts/
        ExpensePieChart.tsx      — Pie chart расходов по категориям (recharts)
        SpendingTrendChart.tsx   — Line chart расходов по дням (recharts)
        ExerciseProgressChart.tsx — Line chart прогресса упражнения (recharts)
      (workout components встроены в WorkoutSessionPage)
    pages/
      DashboardPage.tsx          — Сводка, счета (multi-currency), категории, графики,
                                   AI инсайты, повторяющиеся транзакции
      HistoryPage.tsx            — Транзакции с фильтрами и свайп-удалением
      AddTransactionPage.tsx     — Пошаговый ввод транзакции
      WorkoutsPage.tsx           — Табы: план/веса/графики/календарь, сравнение
      AdvisorPage.tsx            — AI советник с localStorage историей и screen_context
      WorkoutSessionPage.tsx     — Полная сессия: pre→warmup→упражнения→RPE→таймер→итоги
    styles/global.css            — Dark theme, CSS variables, mobile-first
    styles/workout-session.css   — Стили тренировочной сессии
    types/index.ts               — TypeScript типы (Transaction, Workout, Recurring...)

main.py                          — Telegram bot: create_application(), _register_handlers()
bot/
  states.py                      — TransactionStates, AdvisorStates, WorkoutStates
  handlers/
    start.py                     — /start, /help
    transactions.py              — /add, быстрый ввод, ConversationHandler
    balance.py                   — /balance, /stats, /history, /income
    advisor.py                   — /advisor — AI советник
    reports.py                   — /report — еженедельный отчёт
    debug_commands.py            — /debug_* команды
    workout/
      session.py                 — /workout — сессия тренировки
      exercises.py               — Логика упражнений, подходов, RPE
      progress.py                — /weights, /progress
  keyboards/
    main_menu.py                 — get_main_menu()
    menus.py                     — Все остальные клавиатуры
    workout_kb.py                — Клавиатуры тренировок

services/
  sheets.py                      — GoogleSheetsService (legacy, для бэкапа)
  workout_sheets.py              — WorkoutSheetsService (legacy, для бэкапа)
  ai_advisor.py                  — AIAdvisor (DeepSeek API)

utils/
  formatters.py                  — Форматирование сообщений, parse_quick_input()
  telegram_helpers.py            — safe_edit_message()
  debug_logger.py                — Отладочное логирование

scripts/
  migrate_sheets_to_pg.py        — Одноразовая миграция Google Sheets → PostgreSQL
  archive_month.py               — Архивация месяца в Sheets
```

## API Authentication
Telegram Mini App присылает `X-Telegram-Init-Data` заголовок.
`api/auth.py` валидирует через HMAC-SHA256 с `TELEGRAM_BOT_TOKEN`.
`api/deps.py:get_current_user()` дополнительно проверяет `TELEGRAM_USER_ID`.

## Database Models (db/models.py)
- **Account**: id, name, balance, currency
- **Category**: id, name, type (Расход/Доход/Перевод), emoji, budget_limit
- **Transaction**: id, date, type, account_id, category_id, amount, comment, hours, synced_to_sheets
- **Exercise**: id, exercise_id, name, day (A/B), category, weight_step, reps_min, reps_max, rest_seconds, default_sets
- **Phase**: id, name, weeks, rpe_min, rpe_max, sets_modifier
- **Workout**: id, date, day_type, week, phase, energy_before, energy_after, sleep_hours, sleep_quality, back_pain, emotional_wave, notes
- **WorkoutSet**: id, workout_id, exercise_id, set_number, weight, reps, rpe
- **CurrentWeight**: id, exercise_id, weight, target_reps, last_sets (JSON), status
- **RecurringTransaction**: id, name, type, account_id, category_id, amount, currency, frequency, next_date, is_active

## Ключевые константы (config.py)
- `DATABASE_URL` — PostgreSQL connection string (asyncpg)
- `BASE_HOURLY_RATE = 6.5` — ставка BYN/ч
- `CATEGORY_EMOJI` — маппинг категория→эмодзи
- `HUMAN_DESIGN_CONTEXT` — контекст для AI советника

## Google Sheets (опциональный бэкап)
Флаг `synced_to_sheets=True` на Transaction и Workout означает "уже в Sheets".
Миграция данных: `python scripts/migrate_sheets_to_pg.py`

## Команды бота (telegram)
| Команда | Handler | Файл |
|---------|---------|------|
| /start | start_command | start.py |
| /help | help_command | start.py |
| /add | add_command | transactions.py |
| /balance | balance_command | balance.py |
| /stats | stats_command | balance.py |
| /history | history_command | balance.py |
| /income | income_stats_command | balance.py |
| /advisor | advisor_command | advisor.py |
| /report | weekly_report_command | reports.py |
| /workout | workout_command | workout/session.py |
| /weights | current_weights_command | workout/progress.py |
| /progress | progress_command | workout/progress.py |

## Деплой (Docker Compose)
- Сервер: VPS (193.106.251.72), `ssh bot`, `~/Artur/Skuper`
- Контейнеры: budget_postgres (PG 16) + budget_bot (Python 3.11 + frontend dist) + budget_caddy (отдельный compose)
- Деплой: `ssh bot "cd ~/Artur/Skuper && git pull && docker compose up --build -d"`
- Проверка: `ssh bot "cd ~/Artur/Skuper && docker compose ps"` — budget_bot должен быть Up (healthy)
- Логи: `ssh bot "cd ~/Artur/Skuper && docker compose logs --tail=50 budget_bot"`

### Skills:
- `/update-budget-bot` — коммит + push + docker rebuild на сервере
- `/restart-budget-bot` — только restart контейнера (без rebuild)
- `/budget-bot-logs` — просмотр логов и статуса
- `/start-local` — запуск локально для тестирования

## Локальная разработка
```bash
# Backend + Bot
cd /f/budget_bot && ./venv/Scripts/python.exe run.py

# Frontend (отдельно)
cd /f/budget_bot/frontend && npm run dev
```

## Важно при разработке
- НЕ переписывать бот handlers на aiogram — python-telegram-bot v20 оставляем
- `db/services/` — только async функции, принимают `AsyncSession`
- Google Sheets API: минимизировать вызовы (лимиты)
- Не коммитить `.env` и `google_credentials.json`
- Frontend собирается в `frontend/dist/` → копируется в Docker image

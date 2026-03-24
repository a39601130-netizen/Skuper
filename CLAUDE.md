# Budget Bot — Справочник проекта

## Что это
Telegram Mini App + минимальный Bot. Один пользователь (Артур).
- **Mini App**: React 19 + TypeScript — весь UI (финансы, тренировки, AI советник)
- **Bot**: python-telegram-bot v20+ — только /start (ссылка на Mini App), /backup, /help
- **БД**: PostgreSQL (primary) + Google Sheets (опциональный бэкап)
- **AI**: DeepSeek как советник (через API)

## Стек
- **Frontend**: React 19, TypeScript, Vite 6, react-router-dom 7
- **Backend**: FastAPI + uvicorn, SQLAlchemy 2.0 async, asyncpg
- **Bot**: python-telegram-bot v20+ (async), минимальный — 3 команды
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
main.py                          — Telegram bot: create_application(), _register_handlers()
Dockerfile                       — Multi-stage: Node 20 (frontend) → Python 3.11 (backend)
docker-compose.yml               — budget_postgres + budget_bot + caddy
Caddyfile                        — budget-bot.duckdns.org → budget_bot:8000
requirements.txt

bot/
  handlers/
    start.py                     — /start (кнопка Mini App), /help
    backup.py                    — /backup — бэкап PG → Google Sheets (inline меню)
    debug_commands.py            — /bugs, /clear_bugs, /sync_balances
  keyboards/
    main_menu.py                 — get_mini_app_button()

api/
  app.py                         — FastAPI приложение, SPA fallback, CORS, все роутеры
  auth.py                        — HMAC-SHA256 валидация Telegram initData
  deps.py                        — get_current_user(), get_ai()
  routers/
    health.py                    — GET /api/health
    transactions.py              — GET/POST/DELETE /api/transactions
    accounts.py                  — GET /api/accounts
    categories.py                — GET /api/categories, GET /api/categories/references
    stats.py                     — GET /api/stats/monthly|income|weekly|daily-spending
    workouts.py                  — GET/POST /api/workouts, PUT complete, POST sets, GET calendar/compare
    exercises.py                 — GET /api/exercises, GET progress, PUT weight
    advisor.py                   — POST /api/advisor/ask, GET analysis, GET insights
    recurring.py                 — GET/POST /api/recurring, DELETE, POST apply

db/
  database.py                    — engine, async_session, Base, get_db(), init_db()
  models.py                      — ORM модели (см. секцию Database Models)
  seed.py                        — Начальные данные: счета, категории, фазы
  services/
    finance.py                   — Финансовые операции (accounts, transactions, stats)
    workout.py                   — Тренировки (exercises, workouts, sets, weights)
    recurring.py                 — CRUD повторяющихся транзакций + apply

frontend/
  src/
    main.tsx                     — Инициализация Telegram WebApp
    App.tsx                      — Routes: 6 страниц (+ /workout/session)
    api/client.ts                — API вызовы с X-Telegram-Init-Data
    hooks/useTelegram.ts         — useTelegram(): tg, user, haptic
    components/
      BottomNav.tsx              — 5 вкладок навигации
      SwipeableListItem.tsx      — Свайп для удаления
      InsightsCard.tsx           — AI инсайты на Dashboard
      RecurringTransactionsList.tsx
      charts/                    — ExpensePieChart, SpendingTrendChart, ExerciseProgressChart
    pages/
      DashboardPage.tsx          — Сводка, счета, категории, графики, AI инсайты
      HistoryPage.tsx            — Транзакции с фильтрами и свайп-удалением
      AddTransactionPage.tsx     — Пошаговый ввод транзакции
      WorkoutsPage.tsx           — Табы: план/веса/графики/календарь
      AdvisorPage.tsx            — AI советник с localStorage историей
      WorkoutSessionPage.tsx     — Сессия: pre→warmup→упражнения→RPE→таймер→итоги
    styles/global.css            — Dark theme, CSS variables, mobile-first
    styles/workout-session.css
    types/index.ts               — TypeScript типы

services/
  sheets.py                      — GoogleSheetsService (Google Sheets API)
  backup.py                      — BackupService: экспорт PG → Google Sheets
  ai_advisor.py                  — AIAdvisor (DeepSeek API)

utils/
  formatters.py                  — Форматирование, parse_quick_input()
  timezone.py                    — now_minsk(), today_minsk()
  telegram_helpers.py            — safe_edit_message()
  debug_logger.py                — Отладочное логирование

scripts/
  migrate_sheets_to_pg.py        — Одноразовая миграция Sheets → PG
  archive_month.py               — Архивация месяца в Sheets
```

## Команды бота
| Команда | Файл |
|---------|------|
| /start | bot/handlers/start.py — кнопка "Открыть Mini App" |
| /help | bot/handlers/start.py — краткая справка |
| /backup | bot/handlers/backup.py — inline-меню бэкапа в Google Sheets |

## API Authentication
`X-Telegram-Init-Data` → HMAC-SHA256 с `TELEGRAM_BOT_TOKEN` → проверка `TELEGRAM_USER_ID`.

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

## Деплой (Docker Compose)
- Сервер: VPS (193.106.251.72), `ssh bot`, `~/Artur/Skuper`
- Контейнеры: budget_postgres (PG 16) + budget_bot (Python 3.11 + frontend dist) + budget_caddy (отдельный compose)
- Деплой: `ssh bot "cd ~/Artur/Skuper && git pull && docker compose up --build -d"`
- Проверка: `ssh bot "cd ~/Artur/Skuper && docker compose ps"`
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
- Бот минимальный — весь UI в Mini App, не добавлять новые команды/handlers в бот
- `db/services/` — только async функции, принимают `AsyncSession`
- Google Sheets API: минимизировать вызовы (лимиты)
- Не коммитить `.env` и `google_credentials.json`
- Frontend собирается в `frontend/dist/` → копируется в Docker image

# Budget Bot — Справочник проекта

## Что это
Telegram бот для управления финансами и тренировками. Один пользователь (Артур). Google Sheets как БД. DeepSeek AI как советник.

## Стек
- Python 3.10+, python-telegram-bot v20+ (async), gspread + oauth2client, httpx, python-dotenv

## Структура файлов

```
main.py                          (724 стр) — Точка входа, регистрация всех handlers
config.py                        (166 стр) — Конфигурация, константы (BASE_HOURLY_RATE, CATEGORY_EMOJI)

bot/
  states.py                      (151 стр) — TransactionStates, AdvisorStates, WorkoutStates, TransactionData
  handlers/
    start.py                     (83 стр)  — /start, /help, start_command, help_command
    transactions.py              (1073 стр) — /add, быстрый ввод, весь ConversationHandler транзакций
    balance.py                   (135 стр) — /balance, /stats, /history, /income
    advisor.py                   (143 стр) — /advisor — AI советник (обёртка)
    reports.py                   (59 стр)  — /report — еженедельный отчёт
    debug_commands.py            (57 стр)  — /debug_* команды
    workout/
      session.py                 (503 стр) — /workout — сессия тренировки
      exercises.py               (535 стр) — Логика упражнений, подходов, RPE
      progress.py                (258 стр) — /weights, /progress
  keyboards/
    main_menu.py                 (90 стр)  — get_main_menu() — главное inline-меню
    menus.py                     (205 стр) — Все остальные клавиатуры (add, accounts, categories, confirm, history)
    workout_kb.py                (173 стр) — Клавиатуры тренировок

services/
  sheets.py                      (832 стр) — GoogleSheetsService (singleton) — CRUD для финансов
  workout_sheets.py              (503 стр) — WorkoutSheetsService — CRUD для тренировок
  ai_advisor.py                  (338 стр) — DeepSeekAdvisor — AI через DeepSeek API

utils/
  formatters.py                  (544 стр) — Форматирование сообщений, parse_quick_input()
  telegram_helpers.py            (13 стр)  — safe_edit_message()
  debug_logger.py                (164 стр) — Отладочное логирование

scripts/
  archive_month.py               (250 стр) — Архивация месяца в Google Sheets
```

## Архитектурные паттерны

- **ConversationHandler** — пошаговый ввод транзакций (states.py определяет состояния)
- **Singleton** — `get_sheets_service()`, `get_advisor()` — глобальные экземпляры сервисов
- **Кэширование** — references_cache, accounts_cache (TTL 10 мин) в GoogleSheetsService
- **retry_on_error** — декоратор в sheets.py для повторных попыток при ошибках Google API
- **Быстрый ввод** — `parse_quick_input()` в formatters.py парсит текст вроде "50 продукты магазин"
- **user_transactions** — dict в transactions.py, хранит TransactionData в памяти по user_id

## Google Sheets — листы

### Финансы (GOOGLE_SHEETS_FINANCE_ID)
| Лист | Назначение |
|------|-----------|
| Транзакции | Записи: день, тип, счёт, категория, сумма, счёт_куда, комментарий, дата, часы |
| Справочники | Типы, счета, категории (читает бот) |
| Категории | Бюджеты по категориям |
| Счета | Балансы счетов, валюта |
| Дашборд | Сводка (читает бот для статистики) |

### Тренировки (GOOGLE_SHEETS_WORKOUT_ID)
| Лист | Назначение |
|------|-----------|
| Упражнения | Справочник упражнений |
| Тренировки | Логи тренировок |
| Подходы | Детали подходов |
| Текущие веса | Рабочие веса |
| Фазы | Фазы программы |
| Разминка | Шаги разминки |
| Бот конфиг | Настройки бота |

## Ключевые константы (config.py)
- `BASE_HOURLY_RATE = 6.5` — ставка BYN/ч
- `CATEGORY_EMOJI` — маппинг категория→эмодзи (единый для всего проекта)
- `HUMAN_DESIGN_CONTEXT` — контекст для AI советника

## Команды бота
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
| Текст без команды | handle_text_input | transactions.py (быстрый ввод) |

## Callback patterns (menus.py)
- `menu_*` — навигация по меню
- `add_*` — тип транзакции
- `acc_*` — выбор счёта
- `cat_*` / `quick_*` — выбор категории
- `confirm_*` — подтверждение
- `delete_*` — удаление транзакции
- `date_*` / `currency_*` — дата и валюта

## Деплой
- Сервер: VPS, systemd service `budget_bot`
- Для деплоя используй `/update-bot` (коммит → push → SSH обновление на сервере)
- Локальный запуск: `python main.py`

## Важно при разработке
- Это персональный бот (1 пользователь) — не оверинженирить
- Google Sheets API имеет лимиты — минимизировать вызовы
- gspread синхронный — блокирует event loop, но для 1 пользователя это ок
- Не коммитить .env и google_credentials.json

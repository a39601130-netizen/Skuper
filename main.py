"""
Life Manager Bot - Главный файл
Telegram бот для управления финансами и тренировками

Запуск: python main.py
"""
import logging
import os
import sys
import atexit
import warnings
from pathlib import Path
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ConversationHandler,
    filters
)
from telegram.error import BadRequest, NetworkError, TimedOut

# Подавляем предупреждение PTBUserWarning о per_message для CallbackQueryHandler
# Это ожидаемое поведение для callback-based разговоров
warnings.filterwarnings("ignore", message=".*per_message.*CallbackQueryHandler.*")

import config
from utils.debug_logger import setup_debug_logging, bug_tracker, log_conversation_state

# States
from bot.states import TransactionStates, AdvisorStates, WorkoutStates

# Keyboards
from bot.keyboards.main_menu import (
    get_main_menu,
    get_finance_menu,
    get_workout_menu,
    get_advisor_menu
)

# Handlers - Start
from bot.handlers.start import start_command, help_command

# Handlers - Finance (transactions)
from bot.handlers.transactions import (
    add_command,
    menu_add_callback,
    handle_quick_input,
    select_type_callback,
    select_date_callback,
    enter_custom_date,
    select_account_callback,
    select_to_account_callback,
    select_category_callback,
    select_currency_callback,
    enter_amount,
    enter_comment,
    enter_hours,
    enter_exchange_rate,
    use_auto_rate_callback,
    enter_amount_to,
    confirm_amount_to_callback,
    confirm_callback,
    cancel
)

# Handlers - Finance (balance/stats)
from bot.handlers.balance import (
    balance_command,
    balance_callback,
    stats_command,
    stats_callback,
    history_command,
    history_callback,
    income_stats_command,
    income_stats_callback,
    delete_transaction_callback
)

# Handlers - AI Advisor
from bot.handlers.advisor import (
    advisor_command,
    advisor_callback,
    ask_advisor_command,
    advisor_question,
    advisor_ask_callback,
    advisor_refresh_callback
)

# Handlers - Reports
from bot.handlers.reports import (
    weekly_report_command,
    weekly_report_callback,
    send_weekly_report
)

# Handlers - Debug
from bot.handlers.debug_commands import bugs_command, clear_bugs_command, sync_balances_command

# Handlers - Backup
from bot.handlers.backup import (
    backup_command, backup_menu_callback,
    backup_type_callback, backup_month_callback
)

# Handlers - Workout
from bot.handlers.workout.session import (
    workout_menu_callback,
    workout_start_callback,
    workout_begin_callback,
    energy_before_callback,
    low_energy_decision_callback,
    sleep_hours_input,
    sleep_quality_callback,
    back_pain_callback,
    day_select_callback,
    emotional_wave_callback,
    energy_after_callback,
    workout_cancel_callback
)
from bot.handlers.workout.exercises import (
    warmup_done_callback,
    warmup_skip_callback,
    warmup_complete_callback,
    set_input_handler,
    rpe_callback,
    timer_skip_callback,
    timer_add_callback,
    exercise_next_callback,
    exercise_skip_callback,
    exercise_alternative_callback,
    exercise_later_callback,
    workout_end_early_callback
)
from bot.handlers.workout.progress import (
    workout_progress_callback,
    workout_weights_callback,
    workout_history_callback,
    workout_next_callback,
    workout_ai_analysis_callback,
    workout_show_progress_callback,
    workout_delete_last_callback,
    workout_delete_confirm_callback
)

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)


# ============================================
# ОБРАБОТЧИКИ МЕНЮ
# ============================================

async def cancel_conversation_fallback(update: Update, context):
    """Универсальный fallback для выхода из любого диалога при навигации"""
    from telegram.ext import ConversationHandler

    query = update.callback_query

    # Очищаем данные транзакций
    user_id = update.effective_user.id
    from bot.handlers.transactions import user_transactions
    if user_id in user_transactions:
        user_transactions[user_id].reset()

    # Очищаем данные тренировок
    context.user_data.pop('workout', None)

    # Очищаем другие флаги
    context.user_data.pop('in_conversation', None)
    context.user_data.pop('waiting_advisor_question', None)

    # Показываем меню
    await menu_callback(update, context)

    # Завершаем conversation
    return ConversationHandler.END


async def menu_callback(update: Update, context):
    """Обработчик главного меню и модулей"""
    query = update.callback_query

    try:
        await query.answer()
    except BadRequest as e:
        if "query is too old" in str(e).lower():
            logger.warning(f"Устаревший callback query: {e}")
            return
        raise

    data = query.data

    # menu_add и finance_add обрабатываются в ConversationHandler
    if data in ["menu_add", "finance_add"]:
        return

    try:
        # === ГЛАВНОЕ МЕНЮ ===
        if data == "menu_main":
            await query.edit_message_text(
                "🏠 **Главное меню**\n\nВыбери модуль:",
                parse_mode="Markdown",
                reply_markup=get_main_menu()
            )

        # === МОДУЛЬ ФИНАНСЫ ===
        elif data == "module_finance":
            await query.edit_message_text(
                "💰 **ФИНАНСЫ**\n\nВыбери действие:",
                parse_mode="Markdown",
                reply_markup=get_finance_menu()
            )
        elif data == "finance_balance":
            await balance_callback(update, context)
        elif data == "finance_stats":
            await stats_callback(update, context)
        elif data == "finance_history":
            await history_callback(update, context)
        elif data == "finance_income_stats":
            await income_stats_callback(update, context)
        elif data == "finance_weekly":
            await weekly_report_callback(update, context)

        # === МОДУЛЬ ТРЕНИРОВКИ ===
        elif data == "module_workout":
            await workout_menu_callback(update, context)

        # === МОДУЛЬ AI СОВЕТНИК ===
        elif data == "module_advisor":
            await query.edit_message_text(
                "🤖 **AI СОВЕТНИК**\n\n"
                "Выбери что проанализировать:",
                parse_mode="Markdown",
                reply_markup=get_advisor_menu()
            )
        elif data == "advisor_finance":
            await advisor_callback(update, context)
        elif data == "advisor_workout":
            await workout_ai_analysis_callback(update, context)

        # === МОДУЛЬ НАСТРОЙКИ ===
        elif data == "module_settings":
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            settings_kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("💾 Бэкап в Google Sheets", callback_data="backup_menu")],
                [InlineKeyboardButton("🔙 Главное меню", callback_data="menu_main")]
            ])
            await query.edit_message_text(
                "⚙️ **НАСТРОЙКИ**\n\n"
                "Выбери действие:",
                parse_mode="Markdown",
                reply_markup=settings_kb
            )

        # === СТАРЫЕ MENU_ ПУТИ (совместимость) ===
        elif data == "menu_balance":
            await balance_callback(update, context)
        elif data == "menu_stats":
            await stats_callback(update, context)
        elif data == "menu_income":
            await income_stats_callback(update, context)
        elif data == "menu_weekly_report":
            await weekly_report_callback(update, context)
        elif data == "menu_advisor":
            await advisor_callback(update, context)
        elif data == "menu_history":
            await history_callback(update, context)
        elif data == "menu_settings":
            from telegram import InlineKeyboardButton, InlineKeyboardMarkup
            settings_kb = InlineKeyboardMarkup([
                [InlineKeyboardButton("💾 Бэкап в Google Sheets", callback_data="backup_menu")],
                [InlineKeyboardButton("🔙 Главное меню", callback_data="menu_main")]
            ])
            await query.edit_message_text(
                "⚙️ **НАСТРОЙКИ**\n\nВыбери действие:",
                parse_mode="Markdown",
                reply_markup=settings_kb
            )

    except BadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise


async def handle_text(update: Update, context):
    """Обработчик текстовых сообщений (быстрый ввод)"""
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()

    # Проверяем, идёт ли тренировка (ConversationHandler блокирует автоматически)
    user_data = context.user_data
    if user_data.get('workout'):
        return

    # Проверяем на reply клавиатуру
    if text in ["💰 финансы", "финансы"]:
        await update.message.reply_text(
            "💰 **ФИНАНСЫ**\n\nВыбери действие:",
            parse_mode="Markdown",
            reply_markup=get_finance_menu()
        )
        return

    elif text in ["🏋️ тренировки", "тренировки"]:
        await update.message.reply_text(
            "🏋️ **ТРЕНИРОВКИ**\n\nВыбери действие:",
            parse_mode="Markdown",
            reply_markup=get_workout_menu()
        )
        return

    elif text in ["🤖 советник", "советник"]:
        await update.message.reply_text(
            "🤖 **AI СОВЕТНИК**\n\nВыбери что проанализировать:",
            parse_mode="Markdown",
            reply_markup=get_advisor_menu()
        )
        return

    elif text in ["➕ расход", "расход"]:
        from bot.keyboards.menus import get_quick_expense_keyboard
        await update.message.reply_text(
            "💸 **Расход**\n\nВыбери категорию:",
            parse_mode="Markdown",
            reply_markup=get_quick_expense_keyboard()
        )
        return

    elif text in ["💰 доход", "доход"]:
        await update.message.reply_text(
            "💰 **Доход**\n\n"
            "Введи в формате: `сумма чаевые комментарий 10ч`\n\n"
            "Например: `135 чаевые смена 10ч`",
            parse_mode="Markdown"
        )
        return

    elif text in ["💳 баланс", "баланс"]:
        await balance_command(update, context)
        return

    elif text in ["📊 статистика", "статистика"]:
        await stats_command(update, context)
        return

    # Иначе пробуем парсить как быстрый ввод
    await handle_quick_input(update, context)


async def error_handler(update: object, context):
    """Глобальный обработчик ошибок"""
    try:
        error = context.error
        user_id = None

        if update and hasattr(update, 'effective_user'):
            user_id = update.effective_user.id

        bug_tracker.log_bug(
            error=error,
            context={
                'user_data': context.user_data,
                'chat_data': context.chat_data,
                'update': str(update)
            },
            user_id=user_id,
            handler='global_error_handler'
        )

        if isinstance(error, (NetworkError, TimedOut)):
            logger.warning(f"Сетевая ошибка: {error}")
            return

        if update and hasattr(update, 'effective_message'):
            try:
                await update.effective_message.reply_text(
                    "❌ Произошла ошибка. Попробуй /start для перезапуска.",
                    reply_markup=get_main_menu()
                )
            except Exception as send_error:
                logger.warning(f"Не удалось отправить сообщение об ошибке: {send_error}")

    except Exception as e:
        logger.error(f"Ошибка в error_handler: {e}")


# ============================================
# БЛОКИРОВКА МНОЖЕСТВЕННОГО ЗАПУСКА
# ============================================

LOCK_FILE = Path(__file__).parent / "bot.lock"

def acquire_lock():
    """Создает файл блокировки для предотвращения множественного запуска"""
    if LOCK_FILE.exists():
        try:
            with open(LOCK_FILE, 'r') as f:
                pid = int(f.read().strip())

            # Проверяем, существует ли процесс
            if sys.platform == 'win32':
                import subprocess
                result = subprocess.run(['tasklist', '/FI', f'PID eq {pid}'],
                                      capture_output=True, text=True)
                if str(pid) in result.stdout:
                    logger.error(f"❌ Бот уже запущен (PID: {pid})")
                    logger.error("Завершите предыдущий экземпляр или удалите bot.lock")
                    sys.exit(1)
            else:
                try:
                    os.kill(pid, 0)
                    logger.error(f"❌ Бот уже запущен (PID: {pid})")
                    logger.error("Завершите предыдущий экземпляр или удалите bot.lock")
                    sys.exit(1)
                except OSError:
                    pass  # Процесс не существует

            # Старый PID не существует, удаляем файл
            LOCK_FILE.unlink()
        except (ValueError, FileNotFoundError):
            LOCK_FILE.unlink()

    # Создаем новый файл блокировки
    with open(LOCK_FILE, 'w') as f:
        f.write(str(os.getpid()))

    logger.info(f"🔒 Блокировка создана (PID: {os.getpid()})")

def release_lock():
    """Удаляет файл блокировки при завершении"""
    try:
        if LOCK_FILE.exists():
            LOCK_FILE.unlink()
            logger.info("🔓 Блокировка снята")
    except Exception as e:
        logger.warning(f"Не удалось удалить файл блокировки: {e}")

# ============================================
# ГЛАВНАЯ ФУНКЦИЯ
# ============================================

def main():
    """Запуск бота"""

    setup_debug_logging()

    # Проверяем и создаем блокировку
    acquire_lock()
    atexit.register(release_lock)

    if not config.TELEGRAM_BOT_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN не задан в .env файле!")
        return

    # Инициализируем Google Sheets для финансов
    try:
        from services.sheets import get_sheets_service
        sheets = get_sheets_service()
        sheets.ensure_exchange_type_exists()
    except Exception as e:
        logger.warning(f"Не удалось проверить справочник типов: {e}")

    # Создаем приложение
    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()

    # ============================================
    # КОМАНДЫ
    # ============================================
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("income", income_stats_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("advisor", advisor_command))
    application.add_handler(CommandHandler("weekly", weekly_report_command))

    # Команды отладки
    application.add_handler(CommandHandler("bugs", bugs_command))
    application.add_handler(CommandHandler("clear_bugs", clear_bugs_command))

    # Бэкап в Google Sheets
    application.add_handler(CommandHandler("backup", backup_command))

    # ============================================
    # CONVERSATION HANDLER - ФИНАНСЫ
    # ============================================
    add_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("add", add_command),
            CallbackQueryHandler(menu_add_callback, pattern="^(menu_add|finance_add)$"),
            CallbackQueryHandler(select_type_callback, pattern="^add_(expense|income|transfer|exchange)$"),
            CallbackQueryHandler(select_category_callback, pattern="^(quick_|show_all)")
        ],
        states={
            TransactionStates.SELECT_TYPE: [
                CallbackQueryHandler(select_type_callback, pattern="^add_")
            ],
            TransactionStates.SELECT_DATE: [
                CallbackQueryHandler(select_date_callback, pattern="^date_"),
                CallbackQueryHandler(menu_add_callback, pattern="^(menu_add|finance_add)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_custom_date)
            ],
            TransactionStates.SELECT_ACCOUNT: [
                CallbackQueryHandler(select_account_callback, pattern="^(from_|income_|expense_|exchange_from_)")
            ],
            TransactionStates.SELECT_TO_ACCOUNT: [
                CallbackQueryHandler(select_to_account_callback, pattern="^(to_|exchange_to_)")
            ],
            TransactionStates.SELECT_CATEGORY: [
                CallbackQueryHandler(select_category_callback, pattern="^(quick_|cat_|show_all)")
            ],
            TransactionStates.SELECT_CURRENCY: [
                CallbackQueryHandler(select_currency_callback, pattern="^currency_")
            ],
            TransactionStates.ENTER_AMOUNT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_amount)
            ],
            TransactionStates.ENTER_EXCHANGE_RATE: [
                CallbackQueryHandler(use_auto_rate_callback, pattern="^use_auto_rate$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_exchange_rate),
                CommandHandler("skip", enter_exchange_rate)
            ],
            TransactionStates.ENTER_AMOUNT_TO: [
                CallbackQueryHandler(confirm_amount_to_callback, pattern="^confirm_amount_to$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_amount_to),
                CommandHandler("skip", enter_amount_to)
            ],
            TransactionStates.ENTER_COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_comment),
                CommandHandler("skip", enter_comment)
            ],
            TransactionStates.ENTER_HOURS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_hours),
                CommandHandler("skip", enter_hours)
            ],
            TransactionStates.CONFIRM: [
                CallbackQueryHandler(confirm_callback, pattern="^confirm_")
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(menu_add_callback, pattern="^(menu_add|finance_add)$"),
            CallbackQueryHandler(cancel_conversation_fallback, pattern="^(menu_|module_|finance_|advisor_|workout_)")
        ],
        per_message=False,
        per_user=True,
        per_chat=True,
        conversation_timeout=300
    )
    application.add_handler(add_conv_handler, group=0)

    # ============================================
    # CONVERSATION HANDLER - AI СОВЕТНИК
    # ============================================
    advisor_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("ask", ask_advisor_command),
            CallbackQueryHandler(advisor_ask_callback, pattern="^advisor_ask$")
        ],
        states={
            AdvisorStates.WAITING_QUESTION: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, advisor_question)
            ]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cancel_conversation_fallback, pattern="^(menu_|module_|finance_|workout_)")
        ],
        per_message=False,
        per_user=True,
        per_chat=True,
        conversation_timeout=300  # 5 минут на ввод вопроса
    )
    application.add_handler(advisor_conv_handler, group=0)

    # ============================================
    # CONVERSATION HANDLER - ТРЕНИРОВКИ
    # ============================================
    workout_conv_handler = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(workout_start_callback, pattern="^workout_start$"),
        ],
        states={
            WorkoutStates.ENERGY_BEFORE: [
                CallbackQueryHandler(workout_begin_callback, pattern="^workout_begin$"),
                CallbackQueryHandler(energy_before_callback, pattern="^energy_"),
                CallbackQueryHandler(low_energy_decision_callback, pattern="^low_energy_"),
            ],
            WorkoutStates.SLEEP_HOURS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, sleep_hours_input),
            ],
            WorkoutStates.SLEEP_QUALITY: [
                CallbackQueryHandler(sleep_quality_callback, pattern="^energy_"),
            ],
            WorkoutStates.BACK_PAIN: [
                CallbackQueryHandler(back_pain_callback, pattern="^energy_"),
            ],
            WorkoutStates.EMOTIONAL_WAVE: [
                CallbackQueryHandler(day_select_callback, pattern="^select_day_"),
                CallbackQueryHandler(emotional_wave_callback, pattern="^wave_"),
            ],
            WorkoutStates.WARMUP_PHASE1: [
                CallbackQueryHandler(warmup_done_callback, pattern="^warmup_done_"),
                CallbackQueryHandler(warmup_skip_callback, pattern="^warmup_skip_"),
            ],
            WorkoutStates.WARMUP_PHASE2: [
                CallbackQueryHandler(warmup_done_callback, pattern="^warmup_done_"),
                CallbackQueryHandler(warmup_skip_callback, pattern="^warmup_skip_"),
            ],
            WorkoutStates.WARMUP_PHASE3: [
                CallbackQueryHandler(warmup_done_callback, pattern="^warmup_done_"),
                CallbackQueryHandler(warmup_skip_callback, pattern="^warmup_skip_"),
            ],
            WorkoutStates.EXERCISE_START: [
                CallbackQueryHandler(warmup_complete_callback, pattern="^warmup_complete$"),
            ],
            WorkoutStates.SET_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_input_handler),
                CallbackQueryHandler(exercise_alternative_callback, pattern="^exercise_alt$"),
                CallbackQueryHandler(exercise_later_callback, pattern="^exercise_later$"),
                CallbackQueryHandler(exercise_skip_callback, pattern="^exercise_skip$"),
                CallbackQueryHandler(workout_end_early_callback, pattern="^workout_end_early$"),
            ],
            WorkoutStates.SET_RPE: [
                CallbackQueryHandler(rpe_callback, pattern="^rpe_"),
            ],
            WorkoutStates.REST_TIMER: [
                CallbackQueryHandler(timer_skip_callback, pattern="^timer_skip$"),
                CallbackQueryHandler(timer_add_callback, pattern="^timer_add_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_input_handler),
            ],
            WorkoutStates.EXERCISE_COMPLETE: [
                CallbackQueryHandler(exercise_next_callback, pattern="^exercise_next$"),
                CallbackQueryHandler(workout_end_early_callback, pattern="^workout_end_early$"),
            ],
            WorkoutStates.ENERGY_AFTER: [
                CallbackQueryHandler(energy_after_callback, pattern="^energy_"),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(workout_cancel_callback, pattern="^workout_cancel$"),
            CommandHandler("cancel", workout_cancel_callback),
            CallbackQueryHandler(cancel_conversation_fallback, pattern="^(menu_|module_|finance_|advisor_)")
        ],
        per_message=False,
        per_user=True,
        per_chat=True,
        conversation_timeout=3600  # 1 час на тренировку
    )
    application.add_handler(workout_conv_handler, group=0)

    # ============================================
    # CALLBACK HANDLERS - ТРЕНИРОВКИ (вне conversation)
    # ============================================
    application.add_handler(CallbackQueryHandler(
        workout_menu_callback, pattern="^module_workout$"
    ))
    application.add_handler(CallbackQueryHandler(
        workout_progress_callback, pattern="^workout_progress$"
    ))
    application.add_handler(CallbackQueryHandler(
        workout_weights_callback, pattern="^workout_weights$"
    ))
    application.add_handler(CallbackQueryHandler(
        workout_history_callback, pattern="^workout_history$"
    ))
    application.add_handler(CallbackQueryHandler(
        workout_next_callback, pattern="^workout_next$"
    ))
    application.add_handler(CallbackQueryHandler(
        workout_ai_analysis_callback, pattern="^workout_ai_analysis$"
    ))
    application.add_handler(CallbackQueryHandler(
        workout_show_progress_callback, pattern="^workout_show_progress$"
    ))
    application.add_handler(CallbackQueryHandler(
        workout_delete_last_callback, pattern="^workout_delete_last$"
    ))
    application.add_handler(CallbackQueryHandler(
        workout_delete_confirm_callback, pattern="^workout_delete_confirm$"
    ))

    # ============================================
    # CALLBACK HANDLERS - ОБЩИЕ
    # ============================================
    application.add_handler(CallbackQueryHandler(advisor_refresh_callback, pattern="^advisor_refresh$"))
    application.add_handler(CallbackQueryHandler(delete_transaction_callback, pattern="^delete_"))

    # Бэкап (до menu_callback, т.к. backup_menu перехватывается раньше module_)
    application.add_handler(CallbackQueryHandler(backup_menu_callback, pattern="^backup_menu$"))
    application.add_handler(CallbackQueryHandler(backup_type_callback, pattern="^backup_type_"))
    application.add_handler(CallbackQueryHandler(backup_month_callback, pattern="^backup_month_"))

    # Главное меню и модули
    application.add_handler(CallbackQueryHandler(menu_callback, pattern="^(menu_|module_|finance_|advisor_)"))

    # Обработчик текстовых сообщений (быстрый ввод)
    application.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text),
        group=1
    )

    # Глобальный обработчик ошибок
    application.add_error_handler(error_handler)

    # ============================================
    # ПЛАНИРОВЩИК ЗАДАЧ
    # ============================================
    if config.TELEGRAM_USER_ID:
        try:
            from datetime import time

            user_id = int(config.TELEGRAM_USER_ID)

            job_queue = application.job_queue
            job_queue.run_daily(
                send_weekly_report,
                time=time(hour=20, minute=0),
                days=(6,),  # воскресенье
                chat_id=user_id,
                name="weekly_report"
            )

            logger.info(f"✅ Еженедельные отчеты настроены для пользователя {user_id}")

        except Exception as e:
            logger.error(f"❌ Ошибка настройки отчетов: {e}")
    else:
        logger.warning("⚠️ TELEGRAM_USER_ID не задан - автоматические отчеты отключены")

    # Запуск
    logger.info("🤖 Life Manager Bot запущен!")
    logger.info("📊 Модули: Финансы + Тренировки + AI Советник")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


def create_application():
    """Создаёт и возвращает Application (без запуска polling).
    Используется из run.py для параллельного запуска с FastAPI."""
    setup_debug_logging()
    acquire_lock()
    atexit.register(release_lock)

    application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
    _register_handlers(application)
    return application


def _register_handlers(application):
    """Регистрирует все handlers на application."""
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("balance", balance_command))
    application.add_handler(CommandHandler("stats", stats_command))
    application.add_handler(CommandHandler("income", income_stats_command))
    application.add_handler(CommandHandler("history", history_command))
    application.add_handler(CommandHandler("advisor", advisor_command))
    application.add_handler(CommandHandler("weekly", weekly_report_command))
    application.add_handler(CommandHandler("bugs", bugs_command))
    application.add_handler(CommandHandler("clear_bugs", clear_bugs_command))
    application.add_handler(CommandHandler("sync_balances", sync_balances_command))
    application.add_handler(CommandHandler("backup", backup_command))

    add_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("add", add_command),
            CallbackQueryHandler(menu_add_callback, pattern="^(menu_add|finance_add)$"),
            CallbackQueryHandler(select_type_callback, pattern="^add_(expense|income|transfer|exchange)$"),
            CallbackQueryHandler(select_category_callback, pattern="^(quick_|show_all)")
        ],
        states={
            TransactionStates.SELECT_TYPE: [CallbackQueryHandler(select_type_callback, pattern="^add_")],
            TransactionStates.SELECT_DATE: [
                CallbackQueryHandler(select_date_callback, pattern="^date_"),
                CallbackQueryHandler(menu_add_callback, pattern="^(menu_add|finance_add)$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_custom_date)
            ],
            TransactionStates.SELECT_ACCOUNT: [CallbackQueryHandler(select_account_callback, pattern="^(from_|income_|expense_|exchange_from_)")],
            TransactionStates.SELECT_TO_ACCOUNT: [CallbackQueryHandler(select_to_account_callback, pattern="^(to_|exchange_to_)")],
            TransactionStates.SELECT_CATEGORY: [CallbackQueryHandler(select_category_callback, pattern="^(quick_|cat_|show_all)")],
            TransactionStates.SELECT_CURRENCY: [CallbackQueryHandler(select_currency_callback, pattern="^currency_")],
            TransactionStates.ENTER_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, enter_amount)],
            TransactionStates.ENTER_EXCHANGE_RATE: [
                CallbackQueryHandler(use_auto_rate_callback, pattern="^use_auto_rate$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_exchange_rate),
                CommandHandler("skip", enter_exchange_rate)
            ],
            TransactionStates.ENTER_AMOUNT_TO: [
                CallbackQueryHandler(confirm_amount_to_callback, pattern="^confirm_amount_to$"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_amount_to),
                CommandHandler("skip", enter_amount_to)
            ],
            TransactionStates.ENTER_COMMENT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_comment),
                CommandHandler("skip", enter_comment)
            ],
            TransactionStates.ENTER_HOURS: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, enter_hours),
                CommandHandler("skip", enter_hours)
            ],
            TransactionStates.CONFIRM: [CallbackQueryHandler(confirm_callback, pattern="^confirm_")]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(menu_add_callback, pattern="^(menu_add|finance_add)$"),
            CallbackQueryHandler(cancel_conversation_fallback, pattern="^(menu_|module_|finance_|advisor_|workout_)")
        ],
        per_message=False, per_user=True, per_chat=True, conversation_timeout=300
    )
    application.add_handler(add_conv_handler, group=0)

    advisor_conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler("ask", ask_advisor_command),
            CallbackQueryHandler(advisor_ask_callback, pattern="^advisor_ask$")
        ],
        states={
            AdvisorStates.WAITING_QUESTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, advisor_question)]
        },
        fallbacks=[
            CommandHandler("cancel", cancel),
            CallbackQueryHandler(cancel_conversation_fallback, pattern="^(menu_|module_|finance_|workout_)")
        ],
        per_message=False, per_user=True, per_chat=True, conversation_timeout=300
    )
    application.add_handler(advisor_conv_handler, group=0)

    workout_conv_handler = ConversationHandler(
        entry_points=[CallbackQueryHandler(workout_start_callback, pattern="^workout_start$")],
        states={
            WorkoutStates.ENERGY_BEFORE: [
                CallbackQueryHandler(workout_begin_callback, pattern="^workout_begin$"),
                CallbackQueryHandler(energy_before_callback, pattern="^energy_"),
                CallbackQueryHandler(low_energy_decision_callback, pattern="^low_energy_"),
            ],
            WorkoutStates.SLEEP_HOURS: [MessageHandler(filters.TEXT & ~filters.COMMAND, sleep_hours_input)],
            WorkoutStates.SLEEP_QUALITY: [CallbackQueryHandler(sleep_quality_callback, pattern="^energy_")],
            WorkoutStates.BACK_PAIN: [CallbackQueryHandler(back_pain_callback, pattern="^energy_")],
            WorkoutStates.EMOTIONAL_WAVE: [
                CallbackQueryHandler(day_select_callback, pattern="^select_day_"),
                CallbackQueryHandler(emotional_wave_callback, pattern="^wave_"),
            ],
            WorkoutStates.WARMUP_PHASE1: [
                CallbackQueryHandler(warmup_done_callback, pattern="^warmup_done_"),
                CallbackQueryHandler(warmup_skip_callback, pattern="^warmup_skip_"),
            ],
            WorkoutStates.WARMUP_PHASE2: [
                CallbackQueryHandler(warmup_done_callback, pattern="^warmup_done_"),
                CallbackQueryHandler(warmup_skip_callback, pattern="^warmup_skip_"),
            ],
            WorkoutStates.WARMUP_PHASE3: [
                CallbackQueryHandler(warmup_done_callback, pattern="^warmup_done_"),
                CallbackQueryHandler(warmup_skip_callback, pattern="^warmup_skip_"),
            ],
            WorkoutStates.EXERCISE_START: [CallbackQueryHandler(warmup_complete_callback, pattern="^warmup_complete$")],
            WorkoutStates.SET_INPUT: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_input_handler),
                CallbackQueryHandler(exercise_alternative_callback, pattern="^exercise_alt$"),
                CallbackQueryHandler(exercise_later_callback, pattern="^exercise_later$"),
                CallbackQueryHandler(exercise_skip_callback, pattern="^exercise_skip$"),
                CallbackQueryHandler(workout_end_early_callback, pattern="^workout_end_early$"),
            ],
            WorkoutStates.SET_RPE: [CallbackQueryHandler(rpe_callback, pattern="^rpe_")],
            WorkoutStates.REST_TIMER: [
                CallbackQueryHandler(timer_skip_callback, pattern="^timer_skip$"),
                CallbackQueryHandler(timer_add_callback, pattern="^timer_add_"),
                MessageHandler(filters.TEXT & ~filters.COMMAND, set_input_handler),
            ],
            WorkoutStates.EXERCISE_COMPLETE: [
                CallbackQueryHandler(exercise_next_callback, pattern="^exercise_next$"),
                CallbackQueryHandler(workout_end_early_callback, pattern="^workout_end_early$"),
            ],
            WorkoutStates.ENERGY_AFTER: [CallbackQueryHandler(energy_after_callback, pattern="^energy_")],
        },
        fallbacks=[
            CallbackQueryHandler(workout_cancel_callback, pattern="^workout_cancel$"),
            CommandHandler("cancel", workout_cancel_callback),
            CallbackQueryHandler(cancel_conversation_fallback, pattern="^(menu_|module_|finance_|advisor_)")
        ],
        per_message=False, per_user=True, per_chat=True, conversation_timeout=3600
    )
    application.add_handler(workout_conv_handler, group=0)

    application.add_handler(CallbackQueryHandler(workout_menu_callback, pattern="^module_workout$"))
    application.add_handler(CallbackQueryHandler(workout_progress_callback, pattern="^workout_progress$"))
    application.add_handler(CallbackQueryHandler(workout_weights_callback, pattern="^workout_weights$"))
    application.add_handler(CallbackQueryHandler(workout_history_callback, pattern="^workout_history$"))
    application.add_handler(CallbackQueryHandler(workout_next_callback, pattern="^workout_next$"))
    application.add_handler(CallbackQueryHandler(workout_ai_analysis_callback, pattern="^workout_ai_analysis$"))
    application.add_handler(CallbackQueryHandler(workout_show_progress_callback, pattern="^workout_show_progress$"))
    application.add_handler(CallbackQueryHandler(workout_delete_last_callback, pattern="^workout_delete_last$"))
    application.add_handler(CallbackQueryHandler(workout_delete_confirm_callback, pattern="^workout_delete_confirm$"))

    application.add_handler(CallbackQueryHandler(advisor_refresh_callback, pattern="^advisor_refresh$"))
    application.add_handler(CallbackQueryHandler(delete_transaction_callback, pattern="^delete_"))

    # Бэкап
    application.add_handler(CallbackQueryHandler(backup_menu_callback, pattern="^backup_menu$"))
    application.add_handler(CallbackQueryHandler(backup_type_callback, pattern="^backup_type_"))
    application.add_handler(CallbackQueryHandler(backup_month_callback, pattern="^backup_month_"))

    application.add_handler(CallbackQueryHandler(menu_callback, pattern="^(menu_|module_|finance_|advisor_)"))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text), group=1)
    application.add_error_handler(error_handler)


if __name__ == "__main__":
    main()

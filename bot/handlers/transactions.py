"""
Обработчики транзакций
"""
import logging
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from datetime import datetime
from utils.debug_logger import bug_tracker, log_conversation_state
from bot.keyboards.menus import (
    get_add_menu,
    get_accounts_keyboard,
    get_categories_keyboard,
    get_quick_expense_keyboard,
    get_confirm_keyboard,
    get_main_menu,
    get_date_keyboard,
    get_currency_keyboard
)
from bot.states import TransactionStates, TransactionData
from services.sheets import get_sheets_service
from utils.formatters import format_transaction_success, parse_quick_input
import config

logger = logging.getLogger(__name__)

# Хранилище данных транзакций по user_id
user_transactions = {}

# Время жизни незавершённой транзакции (1 час)
TRANSACTION_TTL = 3600


def cleanup_old_transactions():
    """Удалить устаревшие транзакции из памяти (старше 1 часа)"""
    now = time.time()
    expired = [
        uid for uid, trans in user_transactions.items()
        if now - trans.created_at > TRANSACTION_TTL
    ]
    for uid in expired:
        del user_transactions[uid]
    if expired:
        logger.info(f"Очищено {len(expired)} устаревших транзакций")


def clear_user_transaction(user_id: int):
    """Полностью удалить данные транзакции пользователя"""
    if user_id in user_transactions:
        del user_transactions[user_id]


def get_user_transaction(user_id: int) -> TransactionData:
    """Получить или создать данные транзакции для пользователя"""
    # Периодически очищаем старые транзакции
    if len(user_transactions) > 100:
        cleanup_old_transactions()

    if user_id not in user_transactions:
        user_transactions[user_id] = TransactionData()
    return user_transactions[user_id]


async def add_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Команда /add - начало добавления транзакции"""
    await update.message.reply_text(
        "➕ **Добавить транзакцию**\n\nВыбери тип:",
        parse_mode="Markdown",
        reply_markup=get_add_menu()
    )
    return TransactionStates.SELECT_TYPE


async def menu_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия кнопки 'Добавить' из главного меню"""
    query = update.callback_query
    await query.answer()

    # Сбрасываем данные предыдущей незавершённой транзакции
    user_id = update.effective_user.id
    user_transactions[user_id] = TransactionData()

    await query.edit_message_text(
        "➕ **Добавить транзакцию**\n\nВыбери тип:",
        parse_mode="Markdown",
        reply_markup=get_add_menu()
    )
    return TransactionStates.SELECT_TYPE


async def handle_quick_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка быстрого текстового ввода"""
    if not update.message or not update.message.text:
        return

    text = update.message.text

    logger.info(f"Quick input received: {text}")

    parsed = parse_quick_input(text)

    logger.info(f"Parsed result: {parsed}")

    if not parsed:
        logger.info("Quick input not recognized")
        return
    
    try:
        sheets = get_sheets_service()
        day = datetime.now().day
        
        success = sheets.add_transaction(
            day=day,
            trans_type=parsed["type"],
            account="Наличные",
            category=parsed["category"],
            amount=parsed["amount"],
            to_account=parsed.get("to_account"),
            comment=parsed.get("comment"),
            hours=parsed.get("hours")
        )
        
        if success:
            response = format_transaction_success(
                trans_type=parsed["type"],
                amount=parsed["amount"],
                category=parsed["category"],
                comment=parsed.get("comment"),
                hours=parsed.get("hours"),
                account="Наличные"
            )
            await update.message.reply_text(response, parse_mode="Markdown")
        else:
            await update.message.reply_text("❌ Ошибка записи в таблицу.")
            
    except Exception as e:
        logger.error(f"Ошибка quick_input: {e}")
        await update.message.reply_text(f"❌ Ошибка: {str(e)}")


async def select_type_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора типа транзакции"""
    query = update.callback_query
    user_id = query.from_user.id

    try:
        await query.answer()

        data = query.data
        trans = get_user_transaction(user_id)
        trans.reset()

        log_conversation_state(user_id, "SELECT_TYPE", "select_type_callback", {"data": data})

        if data == "add_expense":
            trans.trans_type = "Расход"
            await query.edit_message_text(
                "💸 **Расход**\n\n📅 Выбери дату:",
                parse_mode="Markdown",
                reply_markup=get_date_keyboard()
            )
            return TransactionStates.SELECT_DATE

        elif data == "add_income":
            trans.trans_type = "Доход"
            await query.edit_message_text(
                "💰 **Доход**\n\n📅 Выбери дату:",
                parse_mode="Markdown",
                reply_markup=get_date_keyboard()
            )
            return TransactionStates.SELECT_DATE

        elif data == "add_transfer":
            trans.trans_type = "Перевод"
            await query.edit_message_text(
                "🔄 **Перевод**\n\n📅 Выбери дату:",
                parse_mode="Markdown",
                reply_markup=get_date_keyboard()
            )
            return TransactionStates.SELECT_DATE

        elif data == "add_exchange":
            trans.trans_type = "Обмен валюты"
            await query.edit_message_text(
                "💱 **Обмен валюты**\n\n📅 Выбери дату:",
                parse_mode="Markdown",
                reply_markup=get_date_keyboard()
            )
            return TransactionStates.SELECT_DATE

        return ConversationHandler.END

    except Exception as e:
        bug_tracker.log_bug(e, {"trans_data": trans.to_dict() if 'trans' in dir() else None}, user_id, "select_type_callback")
        try:
            await query.edit_message_text("❌ Ошибка. Попробуй /add снова.", reply_markup=get_main_menu())
        except Exception:
            await context.bot.send_message(chat_id=user_id, text="❌ Ошибка. Попробуй /add снова.")
        return ConversationHandler.END


async def select_date_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора даты"""
    query = update.callback_query
    user_id = query.from_user.id

    try:
        await query.answer()

        data = query.data
        trans = get_user_transaction(user_id)

        log_conversation_state(user_id, "SELECT_DATE", "select_date_callback", {
            "data": data,
            "trans_type": trans.trans_type
        })

        if data == "date_custom":
            await query.edit_message_text(
                f"📆 **{trans.trans_type}**\n\nВведи день месяца (1-31):",
                parse_mode="Markdown"
            )
            return TransactionStates.SELECT_DATE

        elif data.startswith("date_"):
            day = int(data.replace("date_", ""))
            trans.day = day

            return await proceed_after_date(query, trans, day)

        return TransactionStates.SELECT_DATE

    except Exception as e:
        bug_tracker.log_bug(e, {
            "trans_data": trans.to_dict() if 'trans' in dir() and trans else None,
            "callback_data": data if 'data' in dir() else None
        }, user_id, "select_date_callback")
        try:
            await query.edit_message_text("❌ Ошибка. Попробуй /add снова.", reply_markup=get_main_menu())
        except Exception:
            await context.bot.send_message(chat_id=user_id, text="❌ Ошибка. Попробуй /add снова.")
        return ConversationHandler.END


async def proceed_after_date(query, trans, day):
    """Переход к следующему шагу после выбора даты"""

    if trans.trans_type == "Расход":
        await query.edit_message_text(
            f"💸 **Расход** (📅 {day} число)\n\nВыбери категорию:",
            parse_mode="Markdown",
            reply_markup=get_quick_expense_keyboard()
        )
        return TransactionStates.SELECT_CATEGORY

    elif trans.trans_type == "Доход":
        # Для дохода сначала выбираем счет
        try:
            sheets = get_sheets_service()
            refs = sheets.get_references()
            accounts = refs["accounts"]
        except Exception as e:
            logger.warning(f"Не удалось загрузить счета: {e}")
            accounts = ["Наличные", "Карта", "Карта Сбер"]

        await query.edit_message_text(
            f"💰 **Доход** (📅 {day} число)\n\n💳 На какой счет зачислить?",
            parse_mode="Markdown",
            reply_markup=get_accounts_keyboard(accounts, "income")
        )
        return TransactionStates.SELECT_ACCOUNT

    elif trans.trans_type == "Перевод":
        try:
            sheets = get_sheets_service()
            refs = sheets.get_references()
            accounts = refs["accounts"]
        except Exception as e:
            logger.warning(f"Не удалось загрузить счета: {e}")
            accounts = ["Наличные", "Карта", "Карта Сбер"]

        await query.edit_message_text(
            f"🔄 **Перевод** (📅 {day} число)\n\n💳 С какого счета списать?",
            parse_mode="Markdown",
            reply_markup=get_accounts_keyboard(accounts, "from")
        )
        return TransactionStates.SELECT_ACCOUNT

    elif trans.trans_type == "Обмен валюты":
        try:
            sheets = get_sheets_service()
            refs = sheets.get_references()
            accounts = refs["accounts"]
        except Exception as e:
            logger.warning(f"Не удалось загрузить счета: {e}")
            accounts = ["Наличные", "Карта", "Карта Сбер"]

        await query.edit_message_text(
            f"💱 **Обмен валюты** (📅 {day} число)\n\n💳 С какого счета списать?",
            parse_mode="Markdown",
            reply_markup=get_accounts_keyboard(accounts, "exchange_from")
        )
        return TransactionStates.SELECT_ACCOUNT


async def enter_custom_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода произвольной даты"""
    user_id = update.effective_user.id
    trans = get_user_transaction(user_id)
    
    try:
        day = int(update.message.text.strip())
        if day < 1 or day > 31:
            await update.message.reply_text("❌ День должен быть от 1 до 31!")
            return TransactionStates.SELECT_DATE
        
        trans.day = day
        
        if trans.trans_type == "Расход":
            await update.message.reply_text(
                f"💸 **Расход** (📅 {day} число)\n\nВыбери категорию:",
                parse_mode="Markdown",
                reply_markup=get_quick_expense_keyboard()
            )
            return TransactionStates.SELECT_CATEGORY
            
        elif trans.trans_type == "Доход":
            # Для дохода сначала выбираем счет
            try:
                sheets = get_sheets_service()
                refs = sheets.get_references()
                accounts = refs["accounts"]
            except Exception as e:
                logger.warning(f"Не удалось загрузить счета: {e}")
                accounts = ["Наличные", "Карта", "Карта Сбер"]

            await update.message.reply_text(
                f"💰 **Доход** (📅 {day} число)\n\n💳 На какой счет зачислить?",
                parse_mode="Markdown",
                reply_markup=get_accounts_keyboard(accounts, "income")
            )
            return TransactionStates.SELECT_ACCOUNT
            
        elif trans.trans_type == "Перевод":
            try:
                sheets = get_sheets_service()
                refs = sheets.get_references()
                accounts = refs["accounts"]
            except Exception as e:
                logger.warning(f"Не удалось загрузить счета: {e}")
                accounts = ["Наличные", "Карта", "Карта Сбер"]

            await update.message.reply_text(
                f"🔄 **Перевод** (📅 {day} число)\n\n💳 С какого счета списать?",
                parse_mode="Markdown",
                reply_markup=get_accounts_keyboard(accounts, "from")
            )
            return TransactionStates.SELECT_ACCOUNT

        elif trans.trans_type == "Обмен валюты":
            try:
                sheets = get_sheets_service()
                refs = sheets.get_references()
                accounts = refs["accounts"]
            except Exception as e:
                logger.warning(f"Не удалось загрузить счета: {e}")
                accounts = ["Наличные", "Карта", "Карта Сбер"]

            await update.message.reply_text(
                f"💱 **Обмен валюты** (📅 {day} число)\n\n💳 С какого счета списать?",
                parse_mode="Markdown",
                reply_markup=get_accounts_keyboard(accounts, "exchange_from")
            )
            return TransactionStates.SELECT_ACCOUNT

    except ValueError:
        await update.message.reply_text("❌ Введи число от 1 до 31!")
        return TransactionStates.SELECT_DATE


async def select_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора счета (для доходов, расходов и переводов)"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data
    trans = get_user_transaction(user_id)

    logger.info(f"select_account: {data}")

    # Выбор счета для расхода
    if data.startswith("expense_"):
        account = data.replace("expense_", "")
        trans.account = account

        # Определяем валюту счета
        try:
            sheets = get_sheets_service()
            account_currency = sheets.get_account_currency(account)
            trans.currency = account_currency

            # Если валюта не BYN - получаем последний курс
            if account_currency != "BYN":
                last_rate = sheets.get_last_exchange_rate(account_currency)
                if last_rate:
                    trans.exchange_rate = last_rate
                    logger.info(f"Автоматически подставлен курс {account_currency}: {last_rate}")
        except Exception as e:
            logger.warning(f"Ошибка определения валюты счета: {e}")
            trans.currency = "BYN"

        day_str = f" (📅 {trans.day} число)" if trans.day else ""
        currency_info = f" ({trans.currency})" if trans.currency != "BYN" else ""

        await query.edit_message_text(
            f"💸 **Расход**{day_str}\n"
            f"📁 Категория: {trans.category}\n"
            f"💳 Счёт: {account}{currency_info}\n\n"
            f"💵 Введи сумму{currency_info}:",
            parse_mode="Markdown"
        )
        return TransactionStates.ENTER_AMOUNT

    # Выбор счета для дохода
    if data.startswith("income_"):
        account = data.replace("income_", "")
        trans.account = account

        await query.edit_message_text(
            f"💰 **Доход** (📅 {trans.day} число)\n"
            f"💳 Счёт: {account}\n\n"
            f"💵 Введи сумму:",
            parse_mode="Markdown"
        )
        return TransactionStates.ENTER_AMOUNT

    # Выбор счета списания для перевода
    if data.startswith("from_"):
        account = data.replace("from_", "")
        trans.account = account

        try:
            sheets = get_sheets_service()
            refs = sheets.get_references()
            accounts = [a for a in refs["accounts"] if a != account]
        except Exception as e:
            logger.warning(f"Не удалось загрузить счета: {e}")
            accounts = [a for a in ["Наличные", "Карта", "Карта Сбер"] if a != account]

        await query.edit_message_text(
            f"🔄 **Перевод**\n"
            f"📤 С: {account}\n\n"
            f"💳 На какой счет зачислить?",
            parse_mode="Markdown",
            reply_markup=get_accounts_keyboard(accounts, "to")
        )
        return TransactionStates.SELECT_TO_ACCOUNT

    # Выбор счета списания для обмена валюты
    if data.startswith("exchange_from_"):
        account = data.replace("exchange_from_", "")
        trans.account = account

        try:
            sheets = get_sheets_service()
            refs = sheets.get_references()
            accounts = [a for a in refs["accounts"] if a != account]
        except Exception as e:
            logger.warning(f"Не удалось загрузить счета: {e}")
            accounts = [a for a in ["Наличные", "Карта", "Карта Сбер"] if a != account]

        await query.edit_message_text(
            f"💱 **Обмен валюты**\n"
            f"📤 С: {account}\n\n"
            f"💳 На какой счет зачислить?",
            parse_mode="Markdown",
            reply_markup=get_accounts_keyboard(accounts, "exchange_to")
        )
        return TransactionStates.SELECT_TO_ACCOUNT

    return TransactionStates.SELECT_ACCOUNT


async def select_to_account_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора счета зачисления (для переводов и обмена)"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data
    trans = get_user_transaction(user_id)

    logger.info(f"select_to_account: {data}")

    if data.startswith("to_"):
        to_account = data.replace("to_", "")
        trans.to_account = to_account

        await query.edit_message_text(
            f"🔄 **Перевод**\n"
            f"📤 С: {trans.account}\n"
            f"📥 На: {to_account}\n\n"
            f"💵 Введи сумму перевода:",
            parse_mode="Markdown"
        )
        return TransactionStates.ENTER_AMOUNT

    # Для обмена валюты - автоопределяем валюту и переходим к вводу суммы
    if data.startswith("exchange_to_"):
        to_account = data.replace("exchange_to_", "")
        trans.to_account = to_account

        # Автоопределение валюты счёта списания
        try:
            sheets = get_sheets_service()
            from_currency = sheets.get_account_currency(trans.account)
            trans.currency = from_currency
        except Exception:
            trans.currency = "BYN"

        await query.edit_message_text(
            f"💱 **Обмен валюты**\n"
            f"📤 С: {trans.account}\n"
            f"📥 На: {to_account}\n"
            f"🏦 Валюта: {trans.currency}\n\n"
            f"💵 Введи сумму списания ({trans.currency}):",
            parse_mode="Markdown"
        )
        return TransactionStates.ENTER_AMOUNT

    return TransactionStates.SELECT_TO_ACCOUNT


async def select_currency_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора валюты для обмена и расхода"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data
    trans = get_user_transaction(user_id)

    logger.info(f"select_currency: {data}")

    if data.startswith("currency_"):
        currency = data.replace("currency_", "")
        trans.currency = currency

        # Для обмена валюты
        if trans.trans_type == "Обмен валюты":
            await query.edit_message_text(
                f"💱 **Обмен валюты**\n"
                f"📤 С: {trans.account}\n"
                f"📥 На: {trans.to_account}\n"
                f"🏦 Валюта: {currency}\n\n"
                f"💵 Введи сумму списания ({currency}):",
                parse_mode="Markdown"
            )
            return TransactionStates.ENTER_AMOUNT

        # Для расхода
        if trans.trans_type == "Расход":
            day_str = f" (📅 {trans.day} число)" if trans.day else ""
            await query.edit_message_text(
                f"💸 **Расход**{day_str}\n"
                f"📁 Категория: {trans.category}\n"
                f"💳 Счёт: {trans.account}\n"
                f"🏦 Валюта: {currency}\n\n"
                f"💵 Введи сумму ({currency}):",
                parse_mode="Markdown"
            )
            return TransactionStates.ENTER_AMOUNT

    return TransactionStates.SELECT_CURRENCY


async def enter_exchange_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода курса обмена"""
    user_id = update.effective_user.id
    trans = get_user_transaction(user_id)

    # Если пользователь подтвердил автоматический курс через /skip
    if update.message.text.strip() == "/skip":
        # Курс уже установлен и amount_to рассчитан - переходим к комментарию
        if trans.trans_type == "Расход" and trans.exchange_rate and trans.amount_to:
            await update.message.reply_text(
                f"✅ Используем курс: **{trans.exchange_rate}**\n"
                f"💰 Эквивалент: **{trans.amount_to:.2f}** BYN\n\n"
                "💬 Добавь комментарий (или /skip):",
                parse_mode="Markdown"
            )
            return TransactionStates.ENTER_COMMENT

    try:
        rate_text = update.message.text.replace(",", ".").strip()
        rate = float(rate_text)

        if rate <= 0:
            await update.message.reply_text("❌ Курс должен быть положительным!")
            return TransactionStates.ENTER_EXCHANGE_RATE

        trans.exchange_rate = rate

        # Для РАСХОДА в валюте - рассчитываем эквивалент в BYN и переходим к комментарию
        if trans.trans_type == "Расход":
            amount_byn = trans.amount * rate
            trans.amount_to = amount_byn  # Сохраняем эквивалент в BYN

            await update.message.reply_text(
                f"💸 **Расход в {trans.currency}**\n"
                f"💵 Сумма: **{trans.amount}** {trans.currency}\n"
                f"📊 Курс: {rate}\n"
                f"💰 Эквивалент: **{amount_byn:.2f}** BYN\n\n"
                "💬 Добавь комментарий (или /skip):",
                parse_mode="Markdown"
            )
            return TransactionStates.ENTER_COMMENT

        # Для ОБМЕНА валюты - рассчитываем сумму зачисления автоматически
        try:
            sheets = get_sheets_service()
            to_currency = sheets.get_account_currency(trans.to_account)
        except Exception:
            to_currency = "BYN"

        calculated_amount = round(trans.amount / rate, 2)
        trans.amount_to = calculated_amount

        await update.message.reply_text(
            f"💱 **Обмен валюты**\n"
            f"📤 С: {trans.account} ({trans.amount} {trans.currency})\n"
            f"📥 На: {trans.to_account}\n"
            f"📊 Курс: {rate}\n"
            f"💵 Сумма зачисления: **{calculated_amount}** {to_currency}\n\n"
            f"✅ Нажми **Подтвердить** или введи свою сумму:",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Подтвердить", callback_data="confirm_amount_to")]
            ])
        )
        return TransactionStates.ENTER_AMOUNT_TO

    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат курса!\nВведи число: `3.33` или `3,33`",
            parse_mode="Markdown"
        )
        return TransactionStates.ENTER_EXCHANGE_RATE


async def confirm_amount_to_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение автоматически рассчитанной суммы зачисления (кнопка)"""
    query = update.callback_query
    await query.answer()
    user_id = update.effective_user.id
    trans = get_user_transaction(user_id)

    if not trans or not trans.amount_to:
        await query.edit_message_text("❌ Данные транзакции не найдены. Начни заново.")
        return ConversationHandler.END

    try:
        sheets = get_sheets_service()
        to_currency = sheets.get_account_currency(trans.to_account)
    except Exception:
        to_currency = "BYN"

    await query.edit_message_text(
        f"💵 Сумма зачисления: **{trans.amount_to}** {to_currency}\n\n"
        "💬 Добавь комментарий (или /skip):",
        parse_mode="Markdown"
    )
    return TransactionStates.ENTER_COMMENT


async def enter_amount_to(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода суммы зачисления"""
    user_id = update.effective_user.id
    trans = get_user_transaction(user_id)

    # Если /skip — используем автоматически рассчитанную сумму
    if update.message.text.strip() == "/skip" and trans.amount_to:
        try:
            sheets = get_sheets_service()
            to_currency = sheets.get_account_currency(trans.to_account)
        except Exception:
            to_currency = "BYN"

        await update.message.reply_text(
            f"💵 Сумма зачисления: **{trans.amount_to}** {to_currency}\n\n"
            "💬 Добавь комментарий (или /skip):",
            parse_mode="Markdown"
        )
        return TransactionStates.ENTER_COMMENT

    try:
        amount_text = update.message.text.replace(",", ".").strip()
        amount_to = float(amount_text)

        if amount_to <= 0:
            await update.message.reply_text("❌ Сумма должна быть положительной!")
            return TransactionStates.ENTER_AMOUNT_TO

        trans.amount_to = amount_to

        await update.message.reply_text(
            f"💵 Сумма зачисления: **{amount_to}** {trans._get_to_currency()}\n\n"
            "💬 Добавь комментарий (или /skip):",
            parse_mode="Markdown"
        )
        return TransactionStates.ENTER_COMMENT

    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат суммы!\nВведи число: `100` или `99.50`",
            parse_mode="Markdown"
        )
        return TransactionStates.ENTER_AMOUNT_TO


async def select_category_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора категории"""
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    data = query.data
    trans = get_user_transaction(user_id)

    logger.info(f"select_category: {data}")

    # Если транзакция не инициализирована (вход через quick кнопку)
    if not trans.trans_type:
        trans.trans_type = "Расход"
        trans.day = datetime.now().day

    # Кнопка "Все категории"
    if data == "show_all_categories":
        try:
            sheets = get_sheets_service()
            refs = sheets.get_references()
            categories = refs["categories"]
        except Exception as e:
            logger.warning(f"Не удалось загрузить категории: {e}")
            categories = ["Продукты", "Кафе", "Транспорт", "Такси", "Досуг", "Покупки",
                         "Здоровье", "Связь", "ЖКХ", "Одежда"]

        day_str = f" (📅 {trans.day} число)" if trans.day else ""
        await query.edit_message_text(
            f"💸 **Расход**{day_str}\n\nВыбери категорию:",
            parse_mode="Markdown",
            reply_markup=get_categories_keyboard(categories, "Расход")
        )
        return TransactionStates.SELECT_CATEGORY

    if data.startswith("quick_"):
        category = data.replace("quick_", "")
        trans.category = category

        # Показываем выбор счёта для расхода
        try:
            sheets = get_sheets_service()
            refs = sheets.get_references()
            accounts = refs["accounts"]
        except Exception as e:
            logger.warning(f"Не удалось загрузить счета: {e}")
            accounts = ["Наличные", "Карта", "Карта Сбер"]

        day_str = f" (📅 {trans.day} число)" if trans.day else ""
        await query.edit_message_text(
            f"💸 **Расход**{day_str}\n"
            f"📁 Категория: {category}\n\n"
            f"💳 С какого счёта списать?",
            parse_mode="Markdown",
            reply_markup=get_accounts_keyboard(accounts, "expense")
        )
        return TransactionStates.SELECT_ACCOUNT

    elif data.startswith("cat_"):
        category = data.replace("cat_", "")
        trans.category = category

        # Если это ДОХОД и сумма уже введена - идём к комментарию
        if trans.trans_type == "Доход" and trans.amount is not None:
            await query.edit_message_text(
                f"💰 **Доход**: {trans.amount} BYN\n"
                f"📁 Категория: {category}\n\n"
                "💬 Добавь комментарий (или /skip):",
                parse_mode="Markdown"
            )
            return TransactionStates.ENTER_COMMENT

        # Для расхода показываем выбор счёта
        if trans.trans_type == "Расход":
            try:
                sheets = get_sheets_service()
                refs = sheets.get_references()
                accounts = refs["accounts"]
            except Exception as e:
                logger.warning(f"Не удалось загрузить счета: {e}")
                accounts = ["Наличные", "Карта", "Карта Сбер"]

            day_str = f" (📅 {trans.day} число)" if trans.day else ""
            await query.edit_message_text(
                f"💸 **Расход**{day_str}\n"
                f"📁 Категория: {category}\n\n"
                f"💳 С какого счёта списать?",
                parse_mode="Markdown",
                reply_markup=get_accounts_keyboard(accounts, "expense")
            )
            return TransactionStates.SELECT_ACCOUNT

        await query.edit_message_text(
            f"📁 Категория: {category}\n\n💵 Введи сумму:",
            parse_mode="Markdown"
        )
        return TransactionStates.ENTER_AMOUNT

    return TransactionStates.SELECT_CATEGORY


async def enter_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода суммы"""
    user_id = update.effective_user.id
    trans = get_user_transaction(user_id)

    try:
        amount_text = update.message.text.replace(",", ".").strip()
        amount = float(amount_text)

        log_conversation_state(user_id, "ENTER_AMOUNT", "enter_amount", {
            "amount_text": amount_text,
            "amount": amount,
            "trans_type": trans.trans_type
        })

        if amount <= 0:
            await update.message.reply_text("❌ Сумма должна быть положительной!")
            return TransactionStates.ENTER_AMOUNT

        trans.amount = amount

        # Для дохода спрашиваем категорию
        if trans.trans_type == "Доход":
            # Загружаем категории доходов из Google Sheets
            try:
                sheets = get_sheets_service()
                all_categories = sheets.get_categories_budget()
                income_categories = [c["name"] for c in all_categories if c["type"] == "Доход"]
                if not income_categories:
                    income_categories = ["Зарплата", "Чаевые", "Подработка", "Другое"]
            except Exception as e:
                logger.error(f"Ошибка загрузки категорий: {e}")
                income_categories = ["Зарплата", "Чаевые", "Подработка", "Другое"]

            await update.message.reply_text(
                f"💰 Сумма: **{amount}** BYN\n\n📁 Выбери категорию дохода:",
                parse_mode="Markdown",
                reply_markup=get_categories_keyboard(
                    income_categories,
                    "Доход"
                )
            )
            return TransactionStates.SELECT_CATEGORY

        # Для обмена валюты - спрашиваем курс
        if trans.trans_type == "Обмен валюты":
            await update.message.reply_text(
                f"💱 **Обмен валюты**\n"
                f"💵 Сумма списания: **{amount}** {trans.currency}\n\n"
                f"📊 Введи курс обмена:",
                parse_mode="Markdown"
            )
            return TransactionStates.ENTER_EXCHANGE_RATE

        # Для расхода в иностранной валюте
        if trans.trans_type == "Расход" and trans.currency != "BYN":
            # Если курс уже получен автоматически - показываем его
            if trans.exchange_rate and trans.exchange_rate > 0:
                # Рассчитываем эквивалент в BYN
                amount_byn = amount * trans.exchange_rate
                trans.amount_to = amount_byn

                await update.message.reply_text(
                    f"💸 **Расход в {trans.currency}**\n"
                    f"💵 Сумма: **{amount}** {trans.currency}\n"
                    f"📊 Курс: **{trans.exchange_rate}** (последний)\n"
                    f"💰 Эквивалент: **{amount_byn:.2f}** BYN\n\n"
                    f"✅ Курс верный? Отправь `/skip` чтобы продолжить\n"
                    f"✏️ Или введи новый курс {trans.currency}/BYN:",
                    parse_mode="Markdown"
                )
                return TransactionStates.ENTER_EXCHANGE_RATE
            else:
                # Курса нет - просим ввести
                await update.message.reply_text(
                    f"💸 **Расход в {trans.currency}**\n"
                    f"💵 Сумма: **{amount}** {trans.currency}\n\n"
                    f"📊 Введи текущий курс {trans.currency}/BYN:\n"
                    f"(для расчёта суммы в BYN)",
                    parse_mode="Markdown"
                )
                return TransactionStates.ENTER_EXCHANGE_RATE

        # Для расхода в BYN и перевода - к комментарию
        await update.message.reply_text(
            f"💵 Сумма: **{amount}** {trans.currency}\n\n"
            "💬 Добавь комментарий (или /skip):",
            parse_mode="Markdown"
        )
        return TransactionStates.ENTER_COMMENT

    except ValueError:
        await update.message.reply_text(
            "❌ Неверный формат суммы!\nВведи число: `150` или `99.50`",
            parse_mode="Markdown"
        )
        return TransactionStates.ENTER_AMOUNT

    except Exception as e:
        bug_tracker.log_bug(e, {
            "trans_data": trans.to_dict(),
            "input_text": update.message.text
        }, user_id, "enter_amount")
        await update.message.reply_text("❌ Ошибка. Попробуй /add снова.")
        return ConversationHandler.END


async def enter_comment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода комментария"""
    user_id = update.effective_user.id
    trans = get_user_transaction(user_id)
    
    text = update.message.text
    
    if text != "/skip":
        trans.comment = text
    
    if not trans.account:
        trans.account = "Наличные"
    
    if not trans.day:
        trans.day = datetime.now().day
    
    logger.info(f"enter_comment: type={trans.trans_type}, category={trans.category}")

    # Для дохода с категорией "Чаевые" спрашиваем часы (только для чаевых!)
    if trans.trans_type == "Доход" and trans.category == "Чаевые":
        await update.message.reply_text(
            "⏰ Сколько часов отработано?\n(введи число или /skip)",
            parse_mode="Markdown"
        )
        return TransactionStates.ENTER_HOURS

    return await show_confirmation(update, context)


async def enter_hours(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода часов"""
    user_id = update.effective_user.id
    trans = get_user_transaction(user_id)
    
    text = update.message.text
    
    if text != "/skip":
        try:
            hours_text = text.replace(",", ".").replace("ч", "").strip()
            hours = float(hours_text)
            trans.hours = hours
        except ValueError:
            await update.message.reply_text(
                "❌ Введи число часов: `10` или `10.5`",
                parse_mode="Markdown"
            )
            return TransactionStates.ENTER_HOURS
    
    if not trans.account:
        trans.account = "Наличные"
    
    if not trans.day:
        trans.day = datetime.now().day
    
    return await show_confirmation(update, context)


async def show_confirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать подтверждение транзакции"""
    user_id = update.effective_user.id
    trans = get_user_transaction(user_id)
    
    preview = trans.format_preview()
    
    await update.message.reply_text(
        f"📋 **Проверь данные:**\n\n{preview}\n\nВсё верно?",
        parse_mode="Markdown",
        reply_markup=get_confirm_keyboard()
    )
    return TransactionStates.CONFIRM


async def confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка подтверждения"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    trans = get_user_transaction(user_id)
    
    logger.info(f"confirm: {data}")
    
    if data == "confirm_yes":
        if not trans.amount or not trans.trans_type:
            await query.edit_message_text(
                "❌ Ошибка: данные не заполнены. Начни с /add",
                reply_markup=get_main_menu()
            )
            trans.reset()
            return ConversationHandler.END
        
        try:
            sheets = get_sheets_service()
            day = trans.day or datetime.now().day
            account = trans.account or "Наличные"
            
            logger.info(f"Записываю: {trans.trans_type}, {account}, {trans.amount}")
            
            success = sheets.add_transaction(
                day=day,
                trans_type=trans.trans_type,
                account=account,
                category=trans.category,
                amount=trans.amount,
                to_account=trans.to_account,
                comment=trans.comment,
                hours=trans.hours,
                exchange_rate=trans.exchange_rate,
                amount_to=trans.amount_to,
                currency=trans.currency
            )

            if success:
                response = format_transaction_success(
                    trans_type=trans.trans_type,
                    amount=trans.amount,
                    category=trans.category,
                    comment=trans.comment,
                    hours=trans.hours,
                    account=account,
                    currency=trans.currency,
                    exchange_rate=trans.exchange_rate,
                    amount_to=trans.amount_to,
                    to_account=trans.to_account
                )
                await query.edit_message_text(
                    response,
                    parse_mode="Markdown",
                    reply_markup=get_main_menu()
                )
            else:
                await query.edit_message_text(
                    "❌ Ошибка записи в таблицу.",
                    reply_markup=get_main_menu()
                )
                
        except Exception as e:
            logger.error(f"Ошибка записи: {e}")
            await query.edit_message_text(
                f"❌ Ошибка: {str(e)}",
                reply_markup=get_main_menu()
            )
        
        trans.reset()
        return ConversationHandler.END
        
    elif data == "confirm_no":
        trans.reset()
        await query.edit_message_text(
            "❌ Отменено",
            reply_markup=get_main_menu()
        )
        return ConversationHandler.END
        
    elif data == "confirm_edit":
        trans.reset()
        await query.edit_message_text(
            "✏️ Начнём заново.\n\nВыбери тип:",
            reply_markup=get_add_menu()
        )
        return TransactionStates.SELECT_TYPE
    
    return ConversationHandler.END


async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена операции"""
    user_id = update.effective_user.id
    if user_id in user_transactions:
        user_transactions[user_id].reset()
    
    await update.message.reply_text(
        "❌ Операция отменена",
        reply_markup=get_main_menu()
    )
    return ConversationHandler.END

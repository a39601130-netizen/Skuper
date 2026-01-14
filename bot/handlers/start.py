"""
Обработчики команд /start и /help
"""
from telegram import Update
from telegram.ext import ContextTypes
from bot.keyboards.main_menu import get_main_menu
from bot.keyboards.menus import get_reply_keyboard
import config

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""

    user = update.effective_user

    welcome_text = f"""
🏠 Привет, {config.USER_NAME}!

Я твой **Life Manager Bot**

📊 **Модули:**
• 💰 **Финансы** - учёт доходов и расходов
• 🏋️ **Тренировки** - трекер тренировок
• 🤖 **AI Советник** - умные рекомендации

**Быстрый ввод финансов:**
`50 продукты магазин`
`135 чаевые смена 10ч`

Выбери модуль в меню 👇
"""

    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=get_main_menu()
    )

    # Устанавливаем постоянную клавиатуру
    await update.message.reply_text(
        "⌨️ Клавиатура активирована",
        reply_markup=get_reply_keyboard()
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /help"""

    help_text = """📚 СПРАВКА ПО БОТУ

📦 Модули:
• 💰 Финансы - учёт транзакций
• 🏋️ Тренировки - трекер тренировок
• 🤖 AI Советник - анализ и рекомендации

⌨️ Команды:
• /start - Главное меню
• /add - Добавить транзакцию
• /balance - Показать балансы
• /stats - Статистика за месяц
• /advisor - AI советник
• /history - История транзакций
• /weekly - Еженедельный отчёт

✍️ Быстрый ввод финансов:
Формат: сумма категория комментарий

Примеры:
• 50 продукты пятерочка - расход
• 135 чаевые смена 10ч - доход с часами
• перевод 100 карта - перевод

📝 Сокращения категорий:
• продукты, еда, магазин → Продукты
• чаевые, зп, зарплата → Зарплата
• такси, транспорт → соотв. категории

🔮 Бот учитывает твой Human Design профиль!
"""

    await update.message.reply_text(
        help_text,
        reply_markup=get_main_menu()
    )

"""
Обработчики прогресса и статистики тренировок
"""
import logging
from telegram import Update
from telegram.ext import ContextTypes

from bot.keyboards.main_menu import get_workout_menu, get_back_to_main
from bot.keyboards.workout_kb import get_back_keyboard
from services.workout_sheets import get_workout_service
from services.ai_advisor import get_advisor

logger = logging.getLogger(__name__)


async def workout_progress_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать прогресс по упражнениям"""
    query = update.callback_query
    await query.answer()
    
    service = get_workout_service()
    
    # Получаем ключевые упражнения
    key_exercises = ['bench_press', 'goblet_squat', 'trap_bar_deadlift', 'ohp']
    
    text = "📈 **ПРОГРЕСС ПО УПРАЖНЕНИЯМ**\n\n"
    
    for ex_id in key_exercises:
        progress = service.get_exercise_progress(ex_id)
        
        if not progress['exercise']:
            continue
        
        ex = progress['exercise']
        trend_emoji = {
            'up': '📈',
            'down': '📉',
            'stable': '➡️'
        }.get(progress['trend'], '➡️')
        
        text += f"""**{ex['name_short']}**
   Текущий: {progress['current_weight']} кг {trend_emoji}
   Максимум: {progress['max_weight']} кг

"""
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_back_keyboard("module_workout")
    )


async def workout_weights_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать текущие рабочие веса"""
    query = update.callback_query
    await query.answer()
    
    service = get_workout_service()
    weights = service.get_current_weights()
    
    text = "🏋️ **ТЕКУЩИЕ РАБОЧИЕ ВЕСА**\n\n"

    # День A
    text += "**День A** (Горизонтальный):\n"
    day_a = ['goblet_squat', 'bench_press', 'cable_row', 'rdl_dumbbell', 'face_pull', 'tricep_extension']
    for ex_id in day_a:
        if ex_id in weights:
            w = weights[ex_id]
            text += f"  • {w.get('name', ex_id)}: **{w.get('current_weight', 0)}** кг\n"

    text += "\n**День B** (Вертикальный):\n"
    day_b = ['trap_bar_deadlift', 'ohp', 'lat_pulldown', 'leg_press', 'lateral_raise', 'bicep_curl']
    for ex_id in day_b:
        if ex_id in weights:
            w = weights[ex_id]
            text += f"  • {w.get('name', ex_id)}: **{w.get('current_weight', 0)}** кг\n"
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_back_keyboard("module_workout")
    )


async def workout_history_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать историю тренировок"""
    query = update.callback_query
    await query.answer()

    service = get_workout_service()
    history = service.get_workout_history(limit=10)

    if not history:
        text = "📜 История пуста. Начни свою первую тренировку!"
        keyboard = get_back_keyboard("module_workout")
    else:
        text = "📜 **ИСТОРИЯ ТРЕНИРОВОК**\n\n"

        for w in reversed(history):
            day_emoji = "🔵" if w.get('day_type') == 'A' else "🟢"
            energy_before = w.get('energy_before', '?')
            energy_after = w.get('energy_after', '?')

            text += f"""{day_emoji} **{w.get('date', 'N/A')}** — День {w.get('day_type', '?')}
   Неделя {w.get('week_num', '?')} • {w.get('phase', '')}
   Энергия: {energy_before} → {energy_after}

"""

        # Добавляем кнопку удаления если есть записи
        from telegram import InlineKeyboardButton, InlineKeyboardMarkup
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🗑️ Удалить последнюю запись", callback_data="workout_delete_last")],
            [InlineKeyboardButton("🔙 Назад", callback_data="module_workout")]
        ])

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def workout_next_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать информацию о следующей тренировке"""
    query = update.callback_query
    await query.answer()
    
    service = get_workout_service()
    
    next_day = service.determine_next_day()
    week_phase = service.get_current_week_and_phase()
    exercises = service.get_exercises(day=next_day)
    
    day_emoji = "🔵" if next_day == "A" else "🟢"
    day_name = "Горизонтальный акцент" if next_day == "A" else "Вертикальный акцент"
    
    text = f"""📅 **СЛЕДУЮЩАЯ ТРЕНИРОВКА**

{day_emoji} **День {next_day}: {day_name}**
📆 Неделя: {week_phase['week']}
🎯 Фаза: {week_phase['phase_name']}

**Упражнения:**
"""
    
    for i, ex in enumerate(exercises, 1):
        weight_data = service.get_current_weight(ex['exercise_id'])
        weight = weight_data.get('current_weight', '?') if weight_data else '?'
        text += f"{i}. {ex['name_short']} — {weight} кг\n"
    
    # Рекомендации по времени
    text += f"""
⏱️ Ожидаемое время: 50-55 мин
🎯 RPE: {week_phase.get('rpe_min', 7)}-{week_phase.get('rpe_max', 8)}
"""
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_workout_menu()
    )


async def workout_ai_analysis_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """AI анализ тренировки"""
    query = update.callback_query
    await query.answer("🤖 Анализирую...")
    
    service = get_workout_service()
    advisor = get_advisor()
    
    # Собираем данные
    history = service.get_workout_history(limit=5)
    last_workout = history[-1] if history else {}
    
    # Запрашиваем анализ
    analysis = await advisor.analyze_workout(
        workout_data=last_workout,
        history=history,
        trigger="manual"
    )

    text = f"🤖 AI АНАЛИЗ ТРЕНИРОВКИ\n\n{analysis}"

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_back_to_main()
    )


async def workout_show_progress_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать график прогресса после тренировки"""
    query = update.callback_query
    await query.answer()

    # Пока просто показываем текстовую статистику
    await workout_progress_callback(update, context)


async def workout_delete_last_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение удаления последней тренировки"""
    query = update.callback_query
    await query.answer()

    service = get_workout_service()
    history = service.get_workout_history(limit=1)

    if not history:
        await query.edit_message_text(
            "❌ Нет тренировок для удаления.",
            reply_markup=get_back_keyboard("module_workout")
        )
        return

    last_workout = history[0]
    day_emoji = "🔵" if last_workout.get('day_type') == 'A' else "🟢"

    text = f"""⚠️ **ПОДТВЕРЖДЕНИЕ УДАЛЕНИЯ**

{day_emoji} **{last_workout.get('date', 'N/A')}** — День {last_workout.get('day_type', '?')}
Неделя {last_workout.get('week_num', '?')} • {last_workout.get('phase', '')}

Удалить эту тренировку?
"""

    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("✅ Да, удалить", callback_data="workout_delete_confirm")],
        [InlineKeyboardButton("❌ Отмена", callback_data="workout_history")]
    ])

    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=keyboard
    )


async def workout_delete_confirm_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удалить последнюю тренировку"""
    query = update.callback_query
    await query.answer()

    service = get_workout_service()
    result = service.delete_last_workout()

    if result:
        text = "✅ Последняя тренировка удалена."
    else:
        text = "❌ Ошибка при удалении тренировки."

    await query.edit_message_text(
        text,
        reply_markup=get_back_keyboard("workout_history")
    )

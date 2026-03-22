"""
Обработчики сессии тренировки
Начало, завершение, управление состоянием
"""
import asyncio
import logging
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

import config
from bot.states import WorkoutStates
from bot.keyboards.workout_kb import (
    get_workout_start_keyboard,
    get_energy_keyboard,
    get_emotional_wave_keyboard,
    get_workout_complete_keyboard,
    get_yes_no_keyboard,
    get_day_select_keyboard
)
from bot.keyboards.main_menu import get_workout_menu
from services.workout_sheets import get_workout_service
from services.ai_advisor import get_advisor

logger = logging.getLogger(__name__)


async def workout_menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать меню тренировок"""
    query = update.callback_query
    await query.answer()
    
    service = get_workout_service()
    
    # Получаем информацию о следующей тренировке
    next_day = service.determine_next_day()
    week_phase = service.get_current_week_and_phase()
    last_workout = service.get_last_workout()
    
    # Формируем текст
    day_emoji = "🔵" if next_day == "A" else "🟢"
    day_name = "Горизонтальный акцент" if next_day == "A" else "Вертикальный акцент"
    
    text = f"""🏋️ **ТРЕНИРОВКИ**

📅 Следующая: **День {next_day}** {day_emoji}
   _{day_name}_

📆 Неделя: **{week_phase['week']}**
🎯 Фаза: **{week_phase['phase_name']}**
"""
    
    if last_workout:
        text += f"\n📜 Последняя: {last_workout.get('date', 'N/A')} (День {last_workout.get('day_type', '?')})"
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_workout_menu()
    )


async def workout_start_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать новую тренировку - показать информацию"""
    query = update.callback_query
    await query.answer()
    
    service = get_workout_service()
    
    # Определяем день и фазу
    next_day = service.determine_next_day()
    week_phase = service.get_current_week_and_phase()
    exercises = service.get_exercises(day=next_day)
    
    # Сохраняем в контекст
    context.user_data['workout'] = {
        'day_type': next_day,
        'week_num': week_phase['week'],
        'phase': week_phase['phase'],
        'phase_name': week_phase['phase_name'],
        'exercises': exercises,
        'current_exercise_idx': 0,
        'current_set': 1,
        'sets_data': [],
        'warmup_phases': {}
    }
    
    day_emoji = "🔵" if next_day == "A" else "🟢"
    day_name = "Горизонтальный акцент" if next_day == "A" else "Вертикальный акцент"
    
    # Список упражнений с подсказками техники
    ex_lines = []
    for i, e in enumerate(exercises):
        line = f"  {i+1}. {e.get('name_short', e.get('name', ''))}"
        notes = e.get('notes', '')
        if notes:
            line += f"\n      _💡 {notes}_"
        ex_lines.append(line)
    ex_list = "\n".join(ex_lines)
    
    # Целевой RPE для фазы
    phase_config = config.WORKOUT_PHASES.get(week_phase['phase'], {})
    target_rpe = f"{phase_config.get('rpe_min', 7)}-{phase_config.get('rpe_max', 8)}"
    
    text = f"""🏋️ **НОВАЯ ТРЕНИРОВКА**

{day_emoji} **День {next_day}: {day_name}**
📆 Неделя {week_phase['week']} • {week_phase['phase_name']}
🎯 Целевой RPE: {target_rpe}

**Упражнения:**
{ex_list}

Готов начать?
"""
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_workout_start_keyboard()
    )
    
    return WorkoutStates.ENERGY_BEFORE


async def workout_begin_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждение начала - запрос энергии"""
    query = update.callback_query
    await query.answer()
    
    text = """⚡ **Как твоя энергия сейчас?**

Оцени от 1 до 10:
• 1-3: Очень низкая
• 4-5: Ниже среднего
• 6-7: Норма
• 8-10: Отличная
"""
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_energy_keyboard()
    )
    
    return WorkoutStates.ENERGY_BEFORE


async def energy_before_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора энергии до тренировки"""
    query = update.callback_query
    await query.answer()
    
    # Извлекаем значение энергии
    parts = query.data.split('_')
    if len(parts) < 2:
        return
    try:
        energy = int(parts[1])
    except (ValueError, IndexError):
        return
    context.user_data['workout']['energy_before'] = energy
    
    # Если энергия низкая - предупреждение от AI
    if energy < config.AI_TRIGGERS['low_energy']:
        advisor = get_advisor()
        warning = await advisor.ask(
            "Моя энергия сегодня низкая. Стоит ли тренироваться?",
            f"Энергия: {energy}/10",
            mode="brief"
        )
        
        await query.edit_message_text(
            f"⚠️ **Низкая энергия: {energy}/10**\n\n{warning}\n\n"
            "Продолжить тренировку?",
            parse_mode="Markdown",
            reply_markup=get_yes_no_keyboard("low_energy")
        )
        return WorkoutStates.ENERGY_BEFORE
    
    # Переходим к вопросу о сне
    text = """😴 **Сколько часов ты спал?**

Введи число (например: `7` или `7.5`):
"""
    
    await query.edit_message_text(text, parse_mode="Markdown")
    return WorkoutStates.SLEEP_HOURS


async def low_energy_decision_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Решение при низкой энергии"""
    query = update.callback_query
    await query.answer()
    
    if query.data == "low_energy_yes":
        # Продолжаем
        text = """😴 **Сколько часов ты спал?**

Введи число (например: `7` или `7.5`):
"""
        await query.edit_message_text(text, parse_mode="Markdown")
        return WorkoutStates.SLEEP_HOURS
    else:
        # Отменяем
        await query.edit_message_text(
            "🧘 **Тренировка отменена**\n\n"
            "Как Проектор, ты правильно делаешь, что слушаешь своё тело.\n"
            "Отдохни и попробуй завтра!",
            parse_mode="Markdown",
            reply_markup=get_workout_menu()
        )
        return ConversationHandler.END


async def sleep_hours_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода часов сна"""
    try:
        hours = float(update.message.text.replace(',', '.'))
        if hours < 0 or hours > 24:
            raise ValueError("Invalid hours")
        
        context.user_data['workout']['sleep_hours'] = hours
        
        # Спрашиваем качество сна
        text = """💤 **Как оцениваешь качество сна?**

1-10 (где 10 = идеальный сон):
"""
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_energy_keyboard()  # Переиспользуем
        )
        return WorkoutStates.SLEEP_QUALITY
        
    except ValueError:
        await update.message.reply_text(
            "❌ Введи число от 0 до 24 (например: `7` или `7.5`)",
            parse_mode="Markdown"
        )
        return WorkoutStates.SLEEP_HOURS


async def sleep_quality_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка качества сна"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    if len(parts) < 2:
        return
    try:
        quality = int(parts[1])
    except (ValueError, IndexError):
        return
    context.user_data['workout']['sleep_quality'] = quality
    
    # Спрашиваем о боли в спине
    text = """🦴 **Как спина сегодня?**

1 = нет боли, 10 = сильная боль:
"""
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_energy_keyboard()
    )
    return WorkoutStates.BACK_PAIN


async def back_pain_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка боли в спине"""
    query = update.callback_query
    await query.answer()

    parts = query.data.split('_')
    if len(parts) < 2:
        return
    try:
        pain = int(parts[1])
    except (ValueError, IndexError):
        return
    context.user_data['workout']['back_pain'] = pain

    # Если боль высокая - предупреждение AI
    warning_text = ""
    if pain >= config.AI_TRIGGERS['back_pain_threshold']:
        advisor = get_advisor()
        warning = await advisor.ask(
            "У меня болит спина. Как адаптировать тренировку?",
            f"Боль в спине: {pain}/10",
            mode="brief"
        )
        warning_text = f"⚠️ **Внимание: боль в спине {pain}/10**\n{warning}\n\n"

    # День уже определён автоматически в workout_start_callback — показываем его
    workout_data = context.user_data.get('workout', {})
    day_type = workout_data.get('day_type', 'A')
    day_emoji = "🔵" if day_type == "A" else "🟢"
    day_name = "Горизонтальный акцент" if day_type == "A" else "Вертикальный акцент"

    text = f"""{warning_text}🌊 **Где ты на эмоциональной волне?**

📅 День тренировки: {day_emoji} **День {day_type}** ({day_name})

Это важно для Эмоционального Проектора:
"""
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_emotional_wave_keyboard()
    )
    return WorkoutStates.EMOTIONAL_WAVE


async def day_select_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора дня тренировки"""
    query = update.callback_query
    await query.answer()

    # Извлекаем выбранный день из callback_data
    parts = query.data.split('_')
    selected_day = parts[-1] if len(parts) >= 3 else "A"
    if selected_day not in ("A", "B"):
        selected_day = "A"

    # Обновляем день в контексте
    service = get_workout_service()
    week_phase = service.get_current_week_and_phase()
    exercises = service.get_exercises(day=selected_day)

    context.user_data['workout']['day_type'] = selected_day
    context.user_data['workout']['exercises'] = exercises

    # Спрашиваем эмоциональную волну
    text = """🌊 **Где ты на эмоциональной волне?**

Это важно для Эмоционального Проектора:
"""
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_emotional_wave_keyboard()
    )
    return WorkoutStates.EMOTIONAL_WAVE


async def emotional_wave_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка эмоциональной волны"""
    query = update.callback_query
    await query.answer()

    wave_map = {
        'wave_up': '↑',
        'wave_neutral': '→',
        'wave_down': '↓'
    }
    wave = wave_map.get(query.data, '→')
    context.user_data['workout']['emotional_wave'] = wave

    # Создаём тренировку в таблице
    service = get_workout_service()
    workout_data = context.user_data['workout']

    workout_id = service.create_workout(
        day_type=workout_data['day_type'],
        week_num=workout_data['week_num'],
        phase=workout_data['phase_name'],
        energy_before=workout_data['energy_before'],
        sleep_hours=workout_data['sleep_hours'],
        sleep_quality=workout_data['sleep_quality'],
        back_pain=workout_data['back_pain'],
        emotional_wave=wave
    )

    context.user_data['workout']['workout_id'] = workout_id

    # Переходим к разминке
    from bot.handlers.workout.exercises import show_warmup_phase1
    return await show_warmup_phase1(update, context)


async def workout_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершение тренировки"""
    query = update.callback_query
    if query:
        await query.answer()
    
    workout_data = context.user_data.get('workout', {})
    service = get_workout_service()
    
    # Запрашиваем энергию после
    text = """🏁 **Тренировка завершена!**

⚡ Как энергия сейчас?
"""
    
    if query:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_energy_keyboard()
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_energy_keyboard()
        )
    
    return WorkoutStates.ENERGY_AFTER


async def energy_after_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка энергии после тренировки"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    if len(parts) < 2:
        return
    try:
        energy_after = int(parts[1])
    except (ValueError, IndexError):
        return
    workout_data = context.user_data.get('workout', {})
    
    # Сохраняем в таблицу
    service = get_workout_service()
    service.complete_workout(
        workout_id=workout_data['workout_id'],
        energy_after=energy_after,
        warmup_done=bool(workout_data.get('warmup_phases')),
        mcgill_done=False,  # McGill Big 3 делается утром отдельно
        notes=""
    )
    
    # Обновляем текущие веса на основе подходов
    _update_current_weights(service, workout_data)
    
    # Формируем итоговое сообщение
    energy_before = workout_data.get('energy_before', '?')
    energy_change = energy_after - energy_before if isinstance(energy_before, int) else 0
    change_emoji = "📈" if energy_change > 0 else "📉" if energy_change < 0 else "➡️"
    
    # Считаем статистику
    sets_data = workout_data.get('sets_data', [])
    total_sets = len(sets_data)
    exercises_done = len(set(s['exercise_id'] for s in sets_data))
    
    text = f"""🎉 **ТРЕНИРОВКА #{workout_data['workout_id']} ЗАВЕРШЕНА!**

📅 День {workout_data['day_type']} • Неделя {workout_data['week_num']}

📊 **Статистика:**
• Упражнений: {exercises_done}
• Подходов: {total_sets}
• Энергия: {energy_before} → {energy_after} {change_emoji}
"""
    
    # Проверяем прогресс
    progress_messages = []
    for exercise_id in set(s['exercise_id'] for s in sets_data):
        check = service.check_ready_for_increase(exercise_id)
        if check['ready']:
            ex = service.get_exercise_by_id(exercise_id)
            progress_messages.append(
                f"🎉 {ex['name_short']}: +{ex['weight_step']} кг!"
            )
    
    if progress_messages:
        text += "\n**Прогресс:**\n" + "\n".join(progress_messages)
    
    # Предупреждение если энергия сильно упала
    if energy_change < -3:
        text += f"""

⚠️ **Внимание:** энергия упала на {abs(energy_change)} пунктов.
Как Проектор, следи за восстановлением!
Рекомендую 48-72ч до следующей тренировки.
"""
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_workout_complete_keyboard()
    )
    
    # Очищаем данные
    context.user_data.pop('workout', None)
    
    return ConversationHandler.END


def _update_current_weights(service, workout_data: dict):
    """Обновить текущие веса на основе подходов тренировки"""
    sets_data = workout_data.get('sets_data', [])
    
    # Группируем подходы по упражнениям
    by_exercise = {}
    for s in sets_data:
        ex_id = s['exercise_id']
        if ex_id not in by_exercise:
            by_exercise[ex_id] = []
        by_exercise[ex_id].append(s)
    
    # Обновляем каждое упражнение
    for exercise_id, sets in by_exercise.items():
        if not sets:
            continue
        
        # Берём последний использованный вес
        last_weight = sets[-1]['weight']
        # Собираем повторения
        last_reps = [s['reps'] for s in sets[-4:]]  # Последние 4 подхода
        
        service.update_current_weight(exercise_id, last_weight, last_reps)


async def workout_cancel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отмена тренировки"""
    query = update.callback_query
    await query.answer()

    # Отменяем активный таймер если есть
    workout_data = context.user_data.get('workout', {})
    timer_task = workout_data.get('timer_task')
    if timer_task and not timer_task.done():
        timer_task.cancel()
        try:
            await timer_task
        except asyncio.CancelledError:
            pass

    context.user_data.pop('workout', None)

    await query.edit_message_text(
        "❌ Тренировка отменена",
        reply_markup=get_workout_menu()
    )

    return ConversationHandler.END

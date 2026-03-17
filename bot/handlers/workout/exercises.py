"""
Обработчики упражнений и подходов
"""
import logging
import asyncio
from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler

import config
from bot.states import WorkoutStates
from bot.keyboards.workout_kb import (
    get_warmup_phase_keyboard,
    get_warmup_complete_keyboard,
    get_set_input_keyboard,
    get_rpe_keyboard,
    get_rest_timer_keyboard,
    get_exercise_complete_keyboard
)
from services.workout_sheets import get_workout_service

logger = logging.getLogger(__name__)


# ============================================
# РАЗМИНКА
# ============================================

WARMUP_PHASES = {
    1: {
        'name': 'Фаза 1: Кардио',
        'description': '🔥 Быстрая ходьба или велотренажёр **3 минуты**',
        'key': 'phase1_cardio'
    },
    2: {
        'name': 'Фаза 2: McGill Big 3',
        'description': """🧘 **Стабилизация позвоночника:**

1️⃣ Скручивание Макгилла (8-6-4, удержание 8 сек)
2️⃣ Боковая планка (8-6-4 на каждую сторону)
3️⃣ Птица-собака (8-6-4 на каждую сторону)""",
        'key': 'phase2_mcgill'
    },
    3: {
        'name': 'Фаза 3: Подготовка к движению',
        'description': """🏋️ **Активация:**

• Гоблет-присед без веса: 10 повторов (пауза 3 сек внизу)
• Кошка-корова: 10 медленных циклов
• Ягодичный мостик: 15 повторов (удержание 2 сек)""",
        'key': 'phase3_movement'
    },
    4: {
        'name': 'Фаза 4: Специфическая',
        'description': '🎯 1 подход каждого упражнения с **50% рабочего веса**',
        'key': 'phase4_specific'
    }
}


async def show_warmup_phase1(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать первую фазу разминки"""
    return await _show_warmup_phase(update, context, 1)


async def _show_warmup_phase(update: Update, context: ContextTypes.DEFAULT_TYPE, phase: int):
    """Показать фазу разминки"""
    query = update.callback_query
    
    phase_info = WARMUP_PHASES[phase]
    
    text = f"""🔥 **РАЗМИНКА**

**{phase_info['name']}**

{phase_info['description']}
"""
    
    if query:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_warmup_phase_keyboard(phase)
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_warmup_phase_keyboard(phase)
        )
    
    return WorkoutStates.WARMUP_PHASE1 + phase - 1


async def warmup_done_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Фаза разминки выполнена"""
    query = update.callback_query
    await query.answer("✅")

    parts = query.data.split('_')
    if len(parts) < 2:
        return
    try:
        phase = int(parts[-1])
    except (ValueError, IndexError):
        return
    phase_key = WARMUP_PHASES[phase]['key']
    context.user_data['workout']['warmup_phases'][phase_key] = True
    
    # Переходим к следующей фазе или к упражнениям
    if phase < 4:
        return await _show_warmup_phase(update, context, phase + 1)
    else:
        return await _warmup_complete(update, context)


async def warmup_skip_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пропуск фазы разминки"""
    query = update.callback_query
    await query.answer("⏭️")

    parts = query.data.split('_')
    if len(parts) < 2:
        return
    try:
        phase = int(parts[-1])
    except (ValueError, IndexError):
        return
    
    if phase < 4:
        return await _show_warmup_phase(update, context, phase + 1)
    else:
        return await _warmup_complete(update, context)


async def _warmup_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Разминка завершена, переходим к упражнениям"""
    query = update.callback_query
    
    warmup_done = context.user_data['workout'].get('warmup_phases', {})
    done_count = sum(1 for v in warmup_done.values() if v)
    
    text = f"""✅ **Разминка завершена!**

Выполнено фаз: {done_count}/4

Готов к основной части?
"""
    
    await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_warmup_complete_keyboard()
    )
    
    return WorkoutStates.EXERCISE_START


async def warmup_complete_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начать основную часть тренировки"""
    query = update.callback_query
    await query.answer()
    
    # Показываем первое упражнение
    return await show_current_exercise(update, context)


# ============================================
# УПРАЖНЕНИЯ
# ============================================

async def show_current_exercise(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать текущее упражнение"""
    query = update.callback_query
    workout_data = context.user_data['workout']
    
    exercises = workout_data['exercises']
    idx = workout_data['current_exercise_idx']
    
    if idx >= len(exercises):
        # Все упражнения выполнены
        from bot.handlers.workout.session import workout_complete
        return await workout_complete(update, context)
    
    exercise = exercises[idx]
    service = get_workout_service()
    
    # Получаем рекомендуемый вес
    weight_check = service.check_ready_for_increase(exercise['exercise_id'])
    current_weight = weight_check.get('current_weight', 0)
    
    # Получаем историю последних подходов
    history = service.get_sets_for_exercise(exercise['exercise_id'], limit=4)
    history_text = ""
    if history:
        last_reps = [str(h['reps']) for h in history[-4:]]
        last_weight = history[-1]['weight'] if history else current_weight
        history_text = f"📈 Прошлый раз: {last_weight} кг → {', '.join(last_reps)}"
    
    # Формируем сообщение
    is_favorite = exercise.get('is_favorite', False)
    star = "⭐ " if is_favorite else ""
    
    reps_range = f"{exercise['reps_min']}-{exercise['reps_max']}"
    rest_sec = exercise.get('rest_sec', 120)
    rest_min = rest_sec // 60
    rest_text = f"{rest_min} мин" if rest_min > 0 else f"{rest_sec} сек"
    
    # Целевой RPE для фазы
    phase = workout_data.get('phase', 'develop')
    phase_config = config.WORKOUT_PHASES.get(phase, {})
    target_rpe = f"{phase_config.get('rpe_min', 7)}-{phase_config.get('rpe_max', 8)}"
    
    text = f"""
{star}**{exercise['name']}** ({idx + 1}/{len(exercises)})
━━━━━━━━━━━━━━━━━━━━━━━

📊 **Рекомендую:** {current_weight} кг × {reps_range} повторений
{history_text}
💡 {weight_check['message']}

⏱️ Отдых: {rest_text}
🎯 Целевой RPE: {target_rpe}

📝 _{exercise.get('notes', '')}_

━━━━━━━━━━━━━━━━━━━━━━━
**Подход {workout_data['current_set']} из {exercise['sets']}**

Запиши результат (вес повторения):
_Например: `{current_weight} 8`_
"""
    
    if query:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_set_input_keyboard()
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_set_input_keyboard()
        )
    
    return WorkoutStates.SET_INPUT


async def set_input_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка ввода подхода (вес повторения)"""
    text = update.message.text.strip().lower()

    try:
        # Поддержка разных форматов:
        # "16 8", "16 на 8", "16х8", "16x8", "16*8", "16по8"

        # Заменяем разделители на пробел
        for separator in [' на ', 'х', 'x', '*', ' по ', 'на', 'по']:
            text = text.replace(separator, ' ')

        # Парсим
        parts = text.split()
        if len(parts) < 2:
            raise ValueError("Need weight and reps")

        weight = float(parts[0].replace(',', '.'))
        reps = int(parts[1])

        if weight <= 0 or reps <= 0:
            raise ValueError("Invalid values")

        # Сохраняем временно
        context.user_data['workout']['pending_set'] = {
            'weight': weight,
            'reps': reps
        }

        # Спрашиваем RPE
        text = f"""✅ {weight} кг × {reps} повторений

**RPE?** (насколько тяжело было, 1-10)

• 6-7: Комфортно, есть запас
• 8: Тяжело, но 1-2 в запасе
• 9: Очень тяжело, 1 в запасе
• 10: Максимум, на пределе
"""

        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_rpe_keyboard()
        )

        return WorkoutStates.SET_RPE

    except (ValueError, IndexError):
        await update.message.reply_text(
            "❌ Введи результат в любом формате:\n"
            "• `16 8`\n"
            "• `16 на 8`\n"
            "• `16х8` или `16x8`\n"
            "• `16*8`",
            parse_mode="Markdown"
        )
        return WorkoutStates.SET_INPUT


async def rpe_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка выбора RPE"""
    query = update.callback_query
    await query.answer()
    
    parts = query.data.split('_')
    if len(parts) < 2:
        return
    try:
        rpe = int(parts[1])
    except (ValueError, IndexError):
        return
    workout_data = context.user_data['workout']
    pending = workout_data.pop('pending_set', {})
    
    exercise = workout_data['exercises'][workout_data['current_exercise_idx']]
    service = get_workout_service()
    
    # Сохраняем подход в таблицу
    set_id = service.add_set(
        workout_id=workout_data['workout_id'],
        exercise_id=exercise['exercise_id'],
        set_num=workout_data['current_set'],
        weight=pending['weight'],
        reps=pending['reps'],
        rpe=rpe
    )
    
    # Сохраняем локально для статистики
    workout_data['sets_data'].append({
        'exercise_id': exercise['exercise_id'],
        'set_num': workout_data['current_set'],
        'weight': pending['weight'],
        'reps': pending['reps'],
        'rpe': rpe
    })
    
    # Проверяем, есть ли ещё подходы
    if workout_data['current_set'] < exercise['sets']:
        # Ещё есть подходы - запускаем таймер
        workout_data['current_set'] += 1
        rest_sec = exercise.get('rest_sec', 120)
        
        return await start_rest_timer(update, context, rest_sec)
    else:
        # Упражнение завершено
        return await exercise_complete(update, context)


async def start_rest_timer(update: Update, context: ContextTypes.DEFAULT_TYPE, seconds: int):
    """Запустить таймер отдыха"""
    query = update.callback_query
    workout_data = context.user_data['workout']
    
    exercise = workout_data['exercises'][workout_data['current_exercise_idx']]
    
    text = f"""💾 **Записано!**

⏱️ **Отдых: {seconds // 60}:{seconds % 60:02d}**

Следующий: Подход {workout_data['current_set']} из {exercise['sets']}
"""
    
    msg = await query.edit_message_text(
        text,
        parse_mode="Markdown",
        reply_markup=get_rest_timer_keyboard(seconds)
    )
    
    # Запускаем обратный отсчёт
    context.user_data['workout']['timer_message_id'] = msg.message_id
    context.user_data['workout']['timer_seconds'] = seconds

    # Отменяем предыдущий таймер если есть
    old_task = context.user_data['workout'].get('timer_task')
    if old_task and not old_task.done():
        old_task.cancel()
        try:
            await old_task
        except asyncio.CancelledError:
            pass

    # Создаём задачу таймера и сохраняем ссылку
    task = asyncio.create_task(
        _run_timer(update, context, seconds, msg.chat_id, msg.message_id)
    )
    context.user_data['workout']['timer_task'] = task

    return WorkoutStates.REST_TIMER


async def _run_timer(update, context, seconds: int, chat_id: int, message_id: int):
    """Фоновая задача таймера"""
    try:
        remaining = seconds
        
        while remaining > 0:
            await asyncio.sleep(10)  # Обновляем каждые 10 секунд
            remaining -= 10
            
            if remaining <= 0:
                break
            
            # Проверяем, не был ли таймер отменён
            workout_data = context.user_data.get('workout', {})
            if workout_data.get('timer_message_id') != message_id:
                return
            
            try:
                await context.bot.edit_message_reply_markup(
                    chat_id=chat_id,
                    message_id=message_id,
                    reply_markup=get_rest_timer_keyboard(remaining)
                )
            except Exception:
                pass
        
        # Таймер завершён
        workout_data = context.user_data.get('workout', {})
        if workout_data.get('timer_message_id') == message_id:
            exercise = workout_data['exercises'][workout_data['current_exercise_idx']]
            
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=message_id,
                text=f"""⏰ **Время вышло!**

**Подход {workout_data['current_set']} из {exercise['sets']}**

Запиши результат (вес повторения):""",
                parse_mode="Markdown",
                reply_markup=get_set_input_keyboard()
            )
            
    except Exception as e:
        logger.error(f"Timer error: {e}")


async def timer_skip_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пропустить таймер (готов раньше)"""
    query = update.callback_query
    await query.answer("⏩")
    
    # Отменяем таймер
    context.user_data['workout']['timer_message_id'] = None
    
    # Показываем ввод следующего подхода
    return await show_current_exercise(update, context)


async def timer_add_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Добавить 30 секунд к таймеру"""
    query = update.callback_query
    await query.answer("+30 сек")
    
    workout_data = context.user_data['workout']
    workout_data['timer_seconds'] = workout_data.get('timer_seconds', 0) + 30
    
    await query.edit_message_reply_markup(
        reply_markup=get_rest_timer_keyboard(workout_data['timer_seconds'])
    )
    
    return WorkoutStates.REST_TIMER


async def exercise_complete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Упражнение завершено"""
    query = update.callback_query
    workout_data = context.user_data['workout']
    
    exercise = workout_data['exercises'][workout_data['current_exercise_idx']]
    
    # Собираем статистику по упражнению
    ex_sets = [s for s in workout_data['sets_data'] 
               if s['exercise_id'] == exercise['exercise_id']]
    
    if ex_sets:
        reps_list = [str(s['reps']) for s in ex_sets]
        weight = ex_sets[-1]['weight']
        avg_rpe = sum(s['rpe'] for s in ex_sets) / len(ex_sets)
    else:
        reps_list = []
        weight = 0
        avg_rpe = 0
    
    # Проверяем прогресс
    service = get_workout_service()
    progress = service.check_ready_for_increase(exercise['exercise_id'])
    
    text = f"""✅ **{exercise['name_short']} завершён!**

📊 Результат: {weight} кг → {', '.join(reps_list)}
💪 Средний RPE: {avg_rpe:.1f}

{progress['message']}
"""
    
    # Готовимся к следующему упражнению
    workout_data['current_exercise_idx'] += 1
    workout_data['current_set'] = 1
    
    remaining = len(workout_data['exercises']) - workout_data['current_exercise_idx']
    
    if remaining > 0:
        text += f"\n📋 Осталось упражнений: {remaining}"
    
    if query:
        await query.edit_message_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_exercise_complete_keyboard()
        )
    else:
        await update.message.reply_text(
            text,
            parse_mode="Markdown",
            reply_markup=get_exercise_complete_keyboard()
        )
    
    return WorkoutStates.EXERCISE_COMPLETE


async def exercise_next_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Перейти к следующему упражнению"""
    query = update.callback_query
    await query.answer()
    
    return await show_current_exercise(update, context)


async def exercise_skip_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Пропустить упражнение"""
    query = update.callback_query
    await query.answer("⏭️")
    
    workout_data = context.user_data['workout']
    workout_data['current_exercise_idx'] += 1
    workout_data['current_set'] = 1
    
    return await show_current_exercise(update, context)


async def workout_end_early_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Завершить тренировку досрочно"""
    query = update.callback_query
    await query.answer()
    
    from bot.handlers.workout.session import workout_complete
    return await workout_complete(update, context)

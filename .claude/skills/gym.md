# Gym бот — режим отладки

Жди описание проблемы от пользователя. НЕ читай файлы из финансовой части.

## Файлы (в порядке приоритета)

### Хендлеры бота:
- `bot/handlers/workout/session.py` — /workout, начало/завершение тренировки
- `bot/handlers/workout/exercises.py` — упражнения, подходы, RPE
- `bot/handlers/workout/progress.py` — /weights, /progress

### БД сервисы (PostgreSQL — primary):
- `db/services/workout.py` — CRUD: get_exercises, create_workout, complete_workout, add_workout_set, get_current_weights, determine_next_day, get_workout_comparison
- `db/models.py` — Exercise, Phase, Workout, WorkoutSet, CurrentWeight

### API роутеры:
- `api/routers/workouts.py` — GET/POST /api/workouts, PUT complete, POST sets, GET calendar/compare
- `api/routers/exercises.py` — GET /api/exercises, progress, PUT weight

### Прочее:
- `bot/keyboards/workout_kb.py` — клавиатуры тренировок
- `services/workout_sheets.py` — Google Sheets (legacy backup)

## FSM (WorkoutStates)

```
Начало:    ENERGY_BEFORE → SLEEP_HOURS → SLEEP_QUALITY → BACK_PAIN → EMOTIONAL_WAVE
Разминка:  WARMUP_PHASE1 → PHASE2 → PHASE3 → PHASE4
Основная:  EXERCISE_START → SET_INPUT → SET_RPE → SET_NOTES → REST_TIMER → EXERCISE_COMPLETE → (след. упражнение)
Конец:     ENERGY_AFTER → WORKOUT_NOTES → WORKOUT_COMPLETE
```

## Callback patterns

- Меню: `menu_workout`, `workout_start`, `workout_begin`, `workout_cancel`
- Оценки: `energy_N` (1-10), `quality_N`, `wave_up|neutral|down`
- Низкая энергия: `low_energy_yes|no`
- Разминка: `warmup_phase1..4_done`, `warmup_skip`
- Упражнения: `exercise_start|skip|finish`, `set_done`, `add_note`
- Завершение: `workout_complete`, `workout_summary`

## Фазы программы

| Фаза | Недели | RPE | Подходы |
|------|--------|-----|---------|
| intro | 1-2 | 5-6 | 50% |
| base | 3-4 | 6-7 | 100% |
| develop | 5-8 | 7-8 | 100% |
| deload | 9 (цикл) | 6-7 | 50% |

## Human Design контекст

Эмоциональный Проектор 2/4: макс 45-60 мин, стоп ДО усталости, 48-72ч между тренировками, энергия < 5 → предложить отмену.

## Типичные проблемы

1. **Тренировка не создаётся** — проверь create_workout() в db/services/workout.py
2. **Упражнения не загружаются** — проверь get_exercises(day='A'/'B')
3. **Подход не записывается** — проверь add_workout_set(), наличие workout_id в context
4. **Прогресс не обновляется** — смотри update current weights логику
5. **FSM застревает в разминке** — проверь переходы WARMUP_PHASE1..4

# Gym — инструкция для отладки

## Архитектура
Весь UI тренировок — в **Mini App** (React). Бот не участвует.

## Файлы для изучения (в порядке приоритета):

### API роутеры:
- `api/routers/workouts.py` — GET/POST /api/workouts, PUT complete, POST sets, GET calendar/compare
- `api/routers/exercises.py` — GET /api/exercises, GET progress, PUT weight

### Сервис (БД):
- `db/services/workout.py` — вся бизнес-логика тренировок (async, SQLAlchemy)
  - `get_exercises(db, day)` — упражнения дня A/B
  - `get_current_weights(db)` — текущие рабочие веса
  - `determine_next_day(db)` — определить следующий день
  - `create_workout(db, ...)` — создать тренировку
  - `complete_workout(db, workout_id, ...)` — завершить тренировку
  - `add_workout_set(db, ...)` — добавить подход
  - `get_workout_with_sets(db, workout_id)` — тренировка с подходами
  - `get_workouts_for_month(db, year, month)` — календарь
  - `get_workout_comparison(db, workout_id)` — сравнение с предыдущей

### Frontend:
- `frontend/src/pages/WorkoutsPage.tsx` — табы: план/веса/графики/календарь
- `frontend/src/pages/WorkoutSessionPage.tsx` — сессия: pre→warmup→упражнения→RPE→таймер→итоги
- `frontend/src/api/client.ts` — API вызовы (fetchWorkouts, createWorkout, addWorkoutSet, ...)
- `frontend/src/styles/workout-session.css` — стили сессии

### Модели (db/models.py):
- **Exercise** — exercise_id, name, day (A/B), category, weight_step, reps_min, reps_max, rest_seconds, default_sets
- **Phase** — name, weeks, rpe_min, rpe_max, sets_modifier
- **Workout** — date, day_type, week, phase, energy_before/after, sleep, back_pain, emotional_wave, notes
- **WorkoutSet** — workout_id, exercise_id, set_number, weight, reps, rpe
- **CurrentWeight** — exercise_id, weight, target_reps, last_sets (JSON), status

### Бэкап тренировок:
- `services/backup.py` — BackupService.backup_workouts(), backup_current_weights()
- `bot/handlers/backup.py` — /backup команда (inline-меню)

---

## Типичные проблемы:

### 1. Тренировка не создаётся
- Проверь `db/services/workout.py:create_workout()`
- Проверь `api/routers/workouts.py` POST endpoint

### 2. Упражнения не загружаются
- Проверь `db/services/workout.py:get_exercises(db, day)`
- Проверь seed данные в `db/seed.py`

### 3. Подход не записывается
- Проверь `db/services/workout.py:add_workout_set()`
- Проверь API endpoint POST /api/workouts/{id}/sets

### 4. Веса не обновляются
- Проверь `api/routers/exercises.py` PUT /api/exercises/{id}/weight
- Проверь `db/services/workout.py` логику обновления CurrentWeight

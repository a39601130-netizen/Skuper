# Gym бот - инструкция для отладки

## Файлы для изучения (в порядке приоритета):

### Основные хендлеры:
- `bot/handlers/workout/__init__.py` - роутер, регистрация handlers
- `bot/handlers/workout/session.py` - начало/завершение тренировки
- `bot/handlers/workout/exercises.py` - упражнения, подходы, разминка
- `bot/handlers/workout/progress.py` - прогресс и статистика

### Сервисы:
- `services/workout_sheets.py` - работа с Google Sheets (класс `WorkoutSheetsService`)
- `services/ai_advisor.py` - AI советы (DeepSeek)

### Клавиатуры:
- `bot/keyboards/workout_kb.py` - клавиатуры для тренировок
- `bot/keyboards/main_menu.py` - меню тренировок (`get_workout_menu()`)

---

## FSM состояния (WorkoutStates):

### Начало тренировки:
```
ENERGY_BEFORE → SLEEP_HOURS → SLEEP_QUALITY → BACK_PAIN → EMOTIONAL_WAVE
```

### Разминка:
```
WARMUP_PHASE1 (кардио) → WARMUP_PHASE2 (McGill) → WARMUP_PHASE3 (подготовка) → WARMUP_PHASE4 (специфическая)
```

### Основная часть:
```
EXERCISE_START → SET_INPUT → SET_RPE → SET_NOTES → REST_TIMER → EXERCISE_COMPLETE
      ↑                                                              ↓
      └──────────────────── (следующее упражнение) ←─────────────────┘
```

### Завершение:
```
ENERGY_AFTER → WORKOUT_NOTES → WORKOUT_COMPLETE
```

---

## Callback patterns:

### Меню тренировок:
- `menu_workout` - открыть меню тренировок
- `workout_start` - начать тренировку (показать инфо)
- `workout_begin` - подтвердить начало
- `workout_cancel` - отменить

### Энергия/оценки:
- `energy_N` - энергия (N = 1-10)
- `quality_N` - качество сна

### При низкой энергии:
- `low_energy_yes` - продолжить тренировку
- `low_energy_no` - отменить

### Эмоциональная волна:
- `wave_up` - на подъёме ↑
- `wave_neutral` - нейтрально →
- `wave_down` - на спаде ↓

### Разминка:
- `warmup_phase1_done` - кардио выполнено
- `warmup_phase2_done` - McGill выполнено
- `warmup_phase3_done` - подготовка выполнена
- `warmup_phase4_done` - специфическая выполнена
- `warmup_skip` - пропустить

### Упражнения:
- `exercise_start` - начать упражнение
- `exercise_skip` - пропустить
- `exercise_finish` - завершить упражнение
- `set_done` - подход завершён
- `add_note` - добавить заметку

### Завершение:
- `workout_complete` - завершить тренировку
- `workout_summary` - показать итоги

---

## Google Sheets структура:

### Таблица: `config.GOOGLE_SHEETS_WORKOUT_ID`

| Лист | Константа | Описание |
|------|-----------|----------|
| Упражнения | `SHEET_EXERCISES` | Каталог упражнений |
| Тренировки | `SHEET_WORKOUTS` | История тренировок |
| Подходы | `SHEET_SETS` | Все подходы |
| Текущие веса | `SHEET_CURRENT_WEIGHTS` | Рабочие веса |
| Фазы | `SHEET_PHASES` | Фазы программы |
| Разминка | `SHEET_WARMUP` | Данные разминки |
| Бот конфиг | `SHEET_BOT_CONFIG` | Настройки бота |

### Структура листа "Упражнения":
| Поле | Описание |
|------|----------|
| exercise_id | Уникальный ID |
| name | Полное название |
| name_short | Короткое название |
| day | День (A или B) |
| order | Порядок в дне |
| sets_target | Целевое кол-во подходов |
| weight_step | Шаг прибавки веса (кг) |

### Структура листа "Тренировки":
| Колонка | Содержимое |
|---------|------------|
| A | workout_id |
| B | date |
| C | day_type (A/B) |
| D | week_num |
| E | phase |
| F | started_at |
| G | finished_at |
| H | duration_min |
| I | energy_before |
| J | energy_after |
| K | emotional_wave |
| L | sleep_hours |
| M | sleep_quality |
| N | back_pain |
| O | warmup_done |
| P | mcgill_done |
| Q | notes |

### Структура листа "Подходы":
| Колонка | Содержимое |
|---------|------------|
| A | set_id |
| B | workout_id |
| C | exercise_id |
| D | set_num |
| E | weight |
| F | reps |
| G | rpe |
| H | tempo |
| I | notes |
| J | created_at |

### Структура листа "Текущие веса":
| Колонка | Содержимое |
|---------|------------|
| A | exercise_id |
| B | name |
| C | current_weight |
| D | target_reps_min |
| E | target_reps_max |
| F-I | last_set_1..4 (повторения) |
| J-M | last_rpe_1..4 |
| N | last_updated |

---

## Хранение данных тренировки:

```python
context.user_data['workout'] = {
    'day_type': 'A' или 'B',
    'week_num': int,
    'phase': str,              # 'intro', 'base', 'develop', 'deload'
    'phase_name': str,
    'exercises': List[Dict],   # Список упражнений дня
    'current_exercise_idx': int,
    'current_set': int,
    'sets_data': List[Dict],   # Записанные подходы
    'warmup_phases': Dict,     # Выполненные фазы разминки
    'workout_id': int,         # ID тренировки в таблице
    'energy_before': int,
    'sleep_hours': float,
    'sleep_quality': int,
    'back_pain': int,
    'emotional_wave': str      # '↑', '→', '↓'
}
```

---

## Фазы программы (config.py):

| Фаза | Недели | RPE | Подходы |
|------|--------|-----|---------|
| intro | 1-2 | 5-6 | 50% |
| base | 3-4 | 6-7 | 100% |
| develop | 5-8 | 7-8 | 100% |
| deload | 9 (цикл) | 6-7 | 50% |

---

## AI триггеры (config.py):

- `low_energy: 5` - энергия ниже → AI предупреждение
- `high_rpe_streak: 3` - RPE 9+ подряд → AI совет
- `back_pain_threshold: 5` - боль в спине выше → AI адаптация

---

## Типичные проблемы и решения:

### 1. Тренировка не создаётся
- Проверь `context.user_data['workout']`
- Смотри `service.create_workout()` в session.py

### 2. Упражнения не загружаются
- Проверь `service.get_exercises(day='A')` или `'B'`
- Смотри кэш `_exercises_cache`

### 3. Подход не записывается
- Проверь `service.add_set()` в exercises.py
- Убедись что `workout_id` есть в context

### 4. Прогресс не обновляется
- Смотри `_update_current_weights()` в session.py
- Проверь `service.update_current_weight()`

### 5. FSM застревает в разминке
- Проверь переходы между WARMUP_PHASE1..4
- Убедись что возвращается правильное состояние

---

## Ключевые функции:

### workout_sheets.py:
- `get_workout_service()` - singleton сервиса
- `get_exercises(day)` - упражнения дня
- `get_current_weight(exercise_id)` - текущий вес
- `create_workout()` - создать тренировку
- `complete_workout()` - завершить тренировку
- `add_set()` - добавить подход
- `check_ready_for_increase()` - проверить готовность к увеличению веса
- `determine_next_day()` - определить следующий день (A/B)
- `get_current_week_and_phase()` - текущая неделя и фаза

### session.py:
- `workout_menu_callback()` - меню тренировок
- `workout_start_callback()` - показать инфо о тренировке
- `workout_begin_callback()` - начать сбор данных
- `workout_complete()` - завершение
- `energy_after_callback()` - финальная энергия

---

## Human Design контекст:

Пользователь - **Эмоциональный Проектор 2/4**:
- Максимум 45-60 минут тренировки
- Остановиться ДО усталости
- 48-72 часа между тренировками
- При энергии < 5 → предложить отмену
- При падении энергии > 3 пунктов → предупреждение

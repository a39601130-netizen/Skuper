"""
Google Sheets - Сервис тренировок
Работа с таблицей тренировок
"""
import logging
from datetime import datetime
from utils.timezone import now_minsk
from typing import List, Dict, Any, Optional

import config
from services.sheets import BaseSheetsService

logger = logging.getLogger(__name__)


class WorkoutSheetsService(BaseSheetsService):
    """Сервис для работы с таблицей тренировок"""

    def __init__(self):
        super().__init__(config.GOOGLE_SHEETS_WORKOUT_ID)
        self._exercises_cache = None
        self._current_weights_cache = None
        self._weights_cache_time = 0
        self._sets_cache = None
        self._sets_cache_time = 0
        # Кэш истории тренировок
        self._workouts_cache = None
        self._workouts_cache_time = 0
        self._workouts_cache_ttl = 60  # 60 секунд
    
    # ============================================
    # УПРАЖНЕНИЯ
    # ============================================
    
    def get_exercises(self, day: str = None) -> List[Dict]:
        """
        Получить список упражнений
        
        Args:
            day: 'A', 'B' или None для всех
        """
        if self._exercises_cache is None:
            self._exercises_cache = self.get_all_records(config.SHEET_EXERCISES)
        
        exercises = self._exercises_cache
        if day:
            exercises = [e for e in exercises if e.get('day') == day]
        
        return sorted(exercises, key=lambda x: x.get('order', 0))
    
    def get_exercise_by_id(self, exercise_id: str) -> Optional[Dict]:
        """Получить упражнение по ID"""
        exercises = self.get_exercises()
        for ex in exercises:
            if ex.get('exercise_id') == exercise_id:
                return ex
        return None
    
    # ============================================
    # ТЕКУЩИЕ ВЕСА
    # ============================================
    
    def get_current_weights(self) -> Dict[str, Dict]:
        """Получить текущие рабочие веса (словарь по exercise_id)"""
        import time
        # Кэшируем на 60 секунд
        if self._current_weights_cache is None or (time.time() - self._weights_cache_time) > 60:
            records = self.get_all_records(config.SHEET_CURRENT_WEIGHTS)
            self._current_weights_cache = {r['exercise_id']: r for r in records}
            self._weights_cache_time = time.time()
        return self._current_weights_cache
    
    def get_current_weight(self, exercise_id: str) -> Optional[Dict]:
        """Получить текущий вес для упражнения"""
        weights = self.get_current_weights()
        return weights.get(exercise_id)
    
    def update_current_weight(
        self,
        exercise_id: str,
        new_weight: float,
        last_sets: List[int]
    ):
        """
        Обновить текущий вес и результаты последних подходов

        Args:
            exercise_id: ID упражнения
            new_weight: Новый рабочий вес
            last_sets: Список повторений в последних подходах
        """
        # Находим строку локально из кэша
        weights = self.get_current_weights()
        weight_data = weights.get(exercise_id)

        if not weight_data:
            logger.warning(f"Exercise {exercise_id} not found in current weights")
            return

        # Получаем номер строки (из ID или поиском)
        row_num = self.find_row_by_value(config.SHEET_CURRENT_WEIGHTS, 1, exercise_id)

        if row_num:
            # Формируем batch update для всех изменений за раз
            updates = [
                {'range': f'C{row_num}', 'value': new_weight},  # Вес
                {'range': f'M{row_num}', 'value': now_minsk().strftime('%Y-%m-%d')}  # Дата
            ]

            # Добавляем последние подходы (F, G, H, I = 6, 7, 8, 9)
            cols = ['F', 'G', 'H', 'I']
            for i, reps in enumerate(last_sets[:4]):
                updates.append({'range': f'{cols[i]}{row_num}', 'value': reps})

            self.batch_update(config.SHEET_CURRENT_WEIGHTS, updates)

            # Инвалидируем кэш
            self._current_weights_cache = None

            logger.info(f"Updated weight for {exercise_id}: {new_weight} kg")
    
    def check_ready_for_increase(self, exercise_id: str) -> Dict:
        """
        Проверить готовность к увеличению веса

        Returns:
            {
                'ready': bool,
                'current_weight': float,
                'next_weight': float,
                'message': str
            }
        """
        weight_data = self.get_current_weight(exercise_id)
        exercise = self.get_exercise_by_id(exercise_id)

        if not weight_data or not exercise:
            return {'ready': False, 'current_weight': 0, 'next_weight': 0, 'message': 'Данные не найдены'}
        
        current = weight_data.get('current_weight', 0)
        target_max = weight_data.get('target_reps_max', 8)
        step = exercise.get('weight_step', 2.5)
        
        # Проверяем последние подходы
        last_sets = [
            weight_data.get('last_set_1', 0),
            weight_data.get('last_set_2', 0),
            weight_data.get('last_set_3', 0),
            weight_data.get('last_set_4', 0)
        ]
        last_sets = [s for s in last_sets if s]  # Убираем пустые
        
        # Все подходы на максимуме?
        all_at_max = all(s >= target_max for s in last_sets) if last_sets else False
        
        if all_at_max:
            return {
                'ready': True,
                'current_weight': current,
                'next_weight': current + step,
                'message': f'🎉 Все подходы на максимуме! Добавляем +{step} кг'
            }
        else:
            return {
                'ready': False,
                'current_weight': current,
                'next_weight': current,
                'message': f'Цель: все подходы по {target_max} повторений'
            }
    
    # ============================================
    # ТРЕНИРОВКИ
    # ============================================
    
    def create_workout(
        self,
        day_type: str,
        week_num: int,
        phase: str,
        energy_before: int,
        sleep_hours: float,
        sleep_quality: int,
        back_pain: int,
        emotional_wave: str
    ) -> int:
        """
        Создать новую тренировку
        
        Returns:
            workout_id (номер строки)
        """
        now = now_minsk()
        
        # Получаем следующий ID
        last_row = self.get_last_row_number(config.SHEET_WORKOUTS)
        workout_id = last_row  # ID = номер строки (т.к. есть заголовок)
        
        row = [
            workout_id,                         # A: workout_id
            now.strftime('%Y-%m-%d'),           # B: date
            day_type,                           # C: day_type
            week_num,                           # D: week_num
            phase,                              # E: phase
            now.strftime('%H:%M'),              # F: started_at
            '',                                 # G: finished_at (заполним позже)
            '',                                 # H: duration_min (формула)
            energy_before,                      # I: energy_before
            '',                                 # J: energy_after (заполним позже)
            emotional_wave,                     # K: emotional_wave
            sleep_hours,                        # L: sleep_hours
            sleep_quality,                      # M: sleep_quality
            back_pain,                          # N: back_pain
            '',                                 # O: warmup_done
            '',                                 # P: mcgill_done
            ''                                  # Q: notes
        ]
        
        self.append_row(config.SHEET_WORKOUTS, row)
        logger.info(f"Created workout #{workout_id} - Day {day_type}")

        # Инвалидируем кэш
        self._workouts_cache = None

        return workout_id
    
    def complete_workout(
        self,
        workout_id: int,
        energy_after: int,
        warmup_done: bool,
        mcgill_done: bool,
        notes: str = ""
    ):
        """Завершить тренировку"""
        sheet = self.get_sheet(config.SHEET_WORKOUTS)
        row_num = workout_id + 1  # +1 из-за заголовка
        
        now = now_minsk()
        
        # Обновляем поля
        updates = [
            {'range': f'G{row_num}', 'value': now.strftime('%H:%M')},  # finished_at
            {'range': f'H{row_num}', 'value': f'=IF(G{row_num}<>"",HOUR(G{row_num}-F{row_num})*60+MINUTE(G{row_num}-F{row_num}),"")'},  # duration
            {'range': f'J{row_num}', 'value': energy_after},
            {'range': f'O{row_num}', 'value': warmup_done},
            {'range': f'P{row_num}', 'value': mcgill_done},
            {'range': f'Q{row_num}', 'value': notes}
        ]
        
        self.batch_update(config.SHEET_WORKOUTS, updates)
        logger.info(f"Completed workout #{workout_id}")
    
    def _get_workouts_cached(self) -> List[Dict]:
        """Получить все тренировки с кэшированием"""
        import time
        if self._workouts_cache is None or (time.time() - self._workouts_cache_time) > self._workouts_cache_ttl:
            self._workouts_cache = self.get_all_records(config.SHEET_WORKOUTS)
            self._workouts_cache_time = time.time()
        return self._workouts_cache

    def get_last_workout(self) -> Optional[Dict]:
        """Получить последнюю тренировку"""
        records = self._get_workouts_cached()
        return records[-1] if records else None

    def get_workout_history(self, limit: int = 5) -> List[Dict]:
        """Получить историю тренировок"""
        records = self._get_workouts_cached()
        return records[-limit:] if records else []

    def delete_last_workout(self) -> bool:
        """Удалить последнюю тренировку"""
        try:
            records = self._get_workouts_cached()
            if not records:
                return False

            # Номер последней строки (данные + заголовок)
            last_row = len(records) + 1
            self.delete_row(config.SHEET_WORKOUTS, last_row)
            logger.info(f"Deleted last workout (row {last_row})")

            # Инвалидируем кэш
            self._workouts_cache = None
            return True
        except Exception as e:
            logger.error(f"Failed to delete last workout: {e}")
            return False
    
    def determine_next_day(self) -> str:
        """Определить следующий день тренировки (A или B)"""
        last = self.get_last_workout()
        if not last:
            return 'A'
        
        last_day = last.get('day_type', 'B')
        return 'B' if last_day == 'A' else 'A'
    
    def get_current_week_and_phase(self) -> Dict:
        """Определить текущую неделю и фазу программы"""
        all_workouts = self._get_workouts_cached()

        if not all_workouts:
            return {'week': 1, 'phase': 'intro', 'phase_name': 'Знакомство'}

        # Считаем ВСЕ тренировки, а не только последние 20
        total_workouts = len(all_workouts)
        
        # 2 тренировки в неделю
        week = (total_workouts // 2) + 1
        
        # Определяем фазу
        if week <= 2:
            phase = 'intro'
            phase_name = 'Знакомство'
        elif week <= 4:
            phase = 'base'
            phase_name = 'Построение базы'
        elif week <= 8:
            phase = 'develop'
            phase_name = 'Развитие'
        else:
            # После недели 8 - циклы по 8 недель с разгрузкой на 9-й
            cycle_week = ((week - 1) % 9) + 1
            if cycle_week == 9:
                phase = 'deload'
                phase_name = 'Разгрузка'
            else:
                phase = 'develop'
                phase_name = 'Развитие'
        
        return {
            'week': week,
            'phase': phase,
            'phase_name': phase_name
        }
    
    # ============================================
    # ПОДХОДЫ
    # ============================================
    
    def add_set(
        self,
        workout_id: int,
        exercise_id: str,
        set_num: int,
        weight: float,
        reps: int,
        rpe: int,
        notes: str = ""
    ) -> int:
        """
        Добавить подход
        
        Returns:
            set_id
        """
        now = now_minsk()
        
        # Получаем следующий ID
        last_row = self.get_last_row_number(config.SHEET_SETS)
        set_id = last_row  # ID = номер строки
        
        row = [
            set_id,                             # A: set_id
            workout_id,                         # B: workout_id
            exercise_id,                        # C: exercise_id
            set_num,                            # D: set_num
            weight,                             # E: weight
            reps,                               # F: reps
            rpe,                                # G: rpe
            '',                                 # H: tempo
            notes,                              # I: notes
            now.strftime('%Y-%m-%d %H:%M')      # J: created_at
        ]
        
        self.append_row(config.SHEET_SETS, row)
        logger.info(f"Added set: {exercise_id} - {weight}kg x {reps} @ RPE {rpe}")

        # Инвалидируем кэш подходов
        self._sets_cache = None

        return set_id
    
    def get_sets_for_workout(self, workout_id: int) -> List[Dict]:
        """Получить все подходы тренировки"""
        all_sets = self.get_all_records(config.SHEET_SETS)
        return [s for s in all_sets if s.get('workout_id') == workout_id]
    
    def get_sets_for_exercise(
        self,
        exercise_id: str,
        limit: int = 12
    ) -> List[Dict]:
        """Получить последние подходы для упражнения"""
        import time
        # Кэшируем подходы на 30 секунд
        if self._sets_cache is None or (time.time() - self._sets_cache_time) > 30:
            self._sets_cache = self.get_all_records(config.SHEET_SETS)
            self._sets_cache_time = time.time()

        exercise_sets = [s for s in self._sets_cache if s.get('exercise_id') == exercise_id]
        return exercise_sets[-limit:] if exercise_sets else []
    
    # ============================================
    # РАЗМИНКА
    # ============================================
    
    def save_warmup(
        self,
        workout_id: int,
        phases: Dict[str, bool],
        total_time: int = 0,
        notes: str = ""
    ):
        """Сохранить данные разминки"""
        row = [
            workout_id,
            phases.get('phase1_cardio', False),
            phases.get('phase2_mcgill_curl', False),
            phases.get('phase2_mcgill_plank', False),
            phases.get('phase2_mcgill_bird', False),
            phases.get('phase3_goblet', False),
            phases.get('phase3_cat_cow', False),
            phases.get('phase3_bridge', False),
            phases.get('phase4_specific', False),
            total_time,
            notes
        ]
        
        self.append_row(config.SHEET_WARMUP, row)
    
    # ============================================
    # АНАЛИТИКА
    # ============================================
    
    def get_exercise_progress(self, exercise_id: str) -> Dict:
        """
        Получить прогресс по упражнению
        
        Returns:
            {
                'exercise': Dict,
                'current_weight': float,
                'max_weight': float,
                'history': List[Dict],
                'trend': str  # 'up', 'down', 'stable'
            }
        """
        exercise = self.get_exercise_by_id(exercise_id)
        sets = self.get_sets_for_exercise(exercise_id, limit=20)
        weight_data = self.get_current_weight(exercise_id)
        
        if not sets:
            return {
                'exercise': exercise,
                'current_weight': weight_data.get('current_weight', 0) if weight_data else 0,
                'max_weight': 0,
                'history': [],
                'trend': 'stable'
            }
        
        weights = [s.get('weight', 0) for s in sets]
        current = weights[-1] if weights else 0
        max_weight = max(weights) if weights else 0
        
        # Определяем тренд
        if len(weights) >= 4:
            recent_avg = sum(weights[-4:]) / 4
            older_avg = sum(weights[:4]) / 4
            if recent_avg > older_avg * 1.05:
                trend = 'up'
            elif recent_avg < older_avg * 0.95:
                trend = 'down'
            else:
                trend = 'stable'
        else:
            trend = 'stable'
        
        return {
            'exercise': exercise,
            'current_weight': current,
            'max_weight': max_weight,
            'history': sets,
            'trend': trend
        }
    
    def invalidate_cache(self):
        """Сбросить кэш (вызывать после изменений)"""
        self._exercises_cache = None
        self._current_weights_cache = None
        self._workouts_cache = None
        self._sets_cache = None


# Синглтон
_workout_service = None

def get_workout_service() -> WorkoutSheetsService:
    """Получить сервис тренировок"""
    global _workout_service
    if _workout_service is None:
        _workout_service = WorkoutSheetsService()
    return _workout_service

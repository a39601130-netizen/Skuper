"""Workout CRUD operations (PostgreSQL)."""

import logging
from datetime import date, timedelta

from utils.timezone import today_minsk
from typing import Optional, List, Dict, Any

from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Exercise, Workout, WorkoutSet, CurrentWeight, Phase

logger = logging.getLogger(__name__)


async def get_exercises(db: AsyncSession, day: Optional[str] = None) -> List[Dict]:
    q = select(Exercise).where(Exercise.is_active == True)
    if day:
        q = q.where(Exercise.day == day)
    q = q.order_by(Exercise.day, Exercise.order)
    result = await db.execute(q)
    exercises = result.scalars().all()
    return [_exercise_to_dict(e) for e in exercises]


async def get_current_weights(db: AsyncSession) -> Dict[str, Dict]:
    result = await db.execute(
        select(CurrentWeight).options(selectinload(CurrentWeight.exercise))
    )
    weights = result.scalars().all()
    return {w.exercise_id: _weight_to_dict(w) for w in weights}


async def get_workout_history(db: AsyncSession, limit: int = 10) -> List[Dict]:
    result = await db.execute(
        select(Workout)
        .order_by(desc(Workout.date))
        .limit(limit)
    )
    workouts = result.scalars().all()
    return [_workout_to_dict(w) for w in workouts]


async def delete_workout(db: AsyncSession, workout_id: int) -> bool:
    """Удалить тренировку и пересчитать CurrentWeight по оставшимся данным."""
    result = await db.execute(
        select(Workout).options(selectinload(Workout.sets)).where(Workout.id == workout_id)
    )
    workout = result.scalar_one_or_none()
    if not workout:
        return False

    # Запоминаем упражнения из удаляемой тренировки
    affected_exercises = set(s.exercise_id for s in workout.sets)

    await db.delete(workout)
    await db.flush()

    # Пересчитываем CurrentWeight для затронутых упражнений
    for exercise_id in affected_exercises:
        await _recalc_current_weight(db, exercise_id)

    await db.commit()
    logger.info(f"Deleted workout {workout_id}, recalculated weights for {len(affected_exercises)} exercises")
    return True


async def _recalc_current_weight(db: AsyncSession, exercise_id: str):
    """Пересчитать CurrentWeight по последней оставшейся тренировке."""
    # Находим последние подходы этого упражнения
    last_sets_result = await db.execute(
        select(WorkoutSet)
        .join(Workout)
        .where(WorkoutSet.exercise_id == exercise_id)
        .order_by(desc(Workout.date), desc(WorkoutSet.set_number))
        .limit(10)
    )
    last_sets = last_sets_result.scalars().all()

    cw_result = await db.execute(
        select(CurrentWeight).where(CurrentWeight.exercise_id == exercise_id)
    )
    cw = cw_result.scalar_one_or_none()

    if not last_sets:
        # Нет больше данных — сбрасываем
        if cw:
            cw.last_sets = []
            cw.status = None
        return

    # Берём данные из последней тренировки
    last_workout_id = last_sets[0].workout_id
    workout_sets = [s for s in last_sets if s.workout_id == last_workout_id]
    workout_sets.sort(key=lambda x: x.set_number)

    last_weight = workout_sets[-1].weight
    last_reps = [s.reps for s in workout_sets[-4:]]
    last_rpes = [s.rpe for s in workout_sets[-4:] if s.rpe]
    avg_rpe = sum(last_rpes) / len(last_rpes) if last_rpes else 0

    # Определяем статус
    ex_result = await db.execute(
        select(Exercise).where(Exercise.exercise_id == exercise_id)
    )
    exercise = ex_result.scalar_one_or_none()

    status = "in_progress"
    if exercise and avg_rpe > 0:
        all_reps_ok = all(r >= exercise.reps_min for r in last_reps)
        rpe_ok = avg_rpe <= 8
        if all_reps_ok and rpe_ok and len(last_reps) >= exercise.default_sets:
            status = "ready"

    target_reps = f"{exercise.reps_min}-{exercise.reps_max}" if exercise else ""

    if cw:
        cw.weight = last_weight
        cw.target_reps = target_reps
        cw.last_sets = last_reps
        cw.status = status
    else:
        cw = CurrentWeight(
            exercise_id=exercise_id,
            weight=last_weight,
            target_reps=target_reps,
            last_sets=last_reps,
            status=status,
        )
        db.add(cw)


async def get_last_workout(db: AsyncSession) -> Optional[Dict]:
    result = await db.execute(
        select(Workout).order_by(desc(Workout.date)).limit(1)
    )
    w = result.scalar_one_or_none()
    return _workout_to_dict(w) if w else None


async def determine_next_day(db: AsyncSession) -> str:
    """Определить следующий день тренировки (A или B)."""
    last = await get_last_workout(db)
    if not last:
        return "A"
    return "B" if last["day_type"] == "A" else "A"


async def get_current_week_and_phase(db: AsyncSession) -> Dict:
    """Текущая неделя и фаза программы."""
    result = await db.execute(
        select(Workout).order_by(Workout.date).limit(1)
    )
    first = result.scalar_one_or_none()
    if not first:
        phase_result = await db.execute(select(Phase).order_by(Phase.sort_order).limit(1))
        phase = phase_result.scalar_one_or_none()
        return {
            "current_week": 1,
            "phase_name": phase.name if phase else "Знакомство",
            "rpe_min": phase.rpe_min if phase else 5,
            "rpe_max": phase.rpe_max if phase else 6,
        }

    weeks_elapsed = (today_minsk() - first.date).days // 7 + 1

    # Определяем фазу по неделям
    phase_result = await db.execute(select(Phase).order_by(Phase.sort_order))
    phases = list(phase_result.scalars().all())
    current_phase = phases[-1] if phases else None
    accumulated = 0
    for ph in phases:
        if "-" in ph.weeks:
            start, end = map(int, ph.weeks.split("-"))
            ph_weeks = end - start + 1
        else:
            ph_weeks = int(ph.weeks)
        if weeks_elapsed <= accumulated + ph_weeks:
            current_phase = ph
            break
        accumulated += ph_weeks

    return {
        "current_week": weeks_elapsed,
        "phase_name": current_phase.name if current_phase else "—",
        "rpe_min": current_phase.rpe_min if current_phase else 6,
        "rpe_max": current_phase.rpe_max if current_phase else 8,
        "sets_modifier": current_phase.sets_modifier if current_phase else 1.0,
    }


async def get_exercise_progress(db: AsyncSession, exercise_id: str) -> Dict:
    """Прогресс упражнения: история весов."""
    result = await db.execute(
        select(WorkoutSet, Workout.date, Workout.day_type)
        .join(Workout, WorkoutSet.workout_id == Workout.id)
        .where(WorkoutSet.exercise_id == exercise_id)
        .order_by(desc(Workout.date), WorkoutSet.set_number)
        .limit(30)
    )
    rows = result.all()

    if not rows:
        return {
            "exercise_id": exercise_id,
            "current_weight": 0,
            "target_reps": "",
            "status": "",
            "trend": "no_data",
            "history_by_workout": [],
        }

    # Агрегируем по тренировкам
    by_workout: Dict[int, Dict] = {}
    for ws, w_date, w_day_type in rows:
        if ws.workout_id not in by_workout:
            by_workout[ws.workout_id] = {
                "date": w_date.isoformat(),
                "day_type": w_day_type,
                "sets": [],
            }
        by_workout[ws.workout_id]["sets"].append({
            "set_number": ws.set_number,
            "weight": ws.weight,
            "reps": ws.reps,
            "rpe": ws.rpe,
        })

    # Тренд: последние 3 тренировки
    workout_ids = list(by_workout.keys())
    recent = workout_ids[:3]
    trend = "stable"
    if len(recent) >= 2:
        last_w = max(s["weight"] for s in by_workout[recent[0]]["sets"])
        prev_w = max(s["weight"] for s in by_workout[recent[1]]["sets"])
        if last_w > prev_w:
            trend = "up"
        elif last_w < prev_w:
            trend = "down"

    cw_result = await db.execute(
        select(CurrentWeight).where(CurrentWeight.exercise_id == exercise_id)
    )
    cw = cw_result.scalar_one_or_none()

    return {
        "exercise_id": exercise_id,
        "current_weight": cw.weight if cw else 0,
        "target_reps": cw.target_reps if cw else "",
        "status": cw.status if cw else "",
        "trend": trend,
        "history_by_workout": [
            by_workout[wid] for wid in workout_ids[:10]
        ],
    }


async def update_current_weight(
    db: AsyncSession,
    exercise_id: str,
    new_weight: float,
    target_reps: Optional[str] = None,
    last_sets: Optional[List] = None,
    status: Optional[str] = None,
) -> CurrentWeight:
    result = await db.execute(
        select(CurrentWeight).where(CurrentWeight.exercise_id == exercise_id)
    )
    cw = result.scalar_one_or_none()
    if cw:
        cw.weight = new_weight
        if target_reps:
            cw.target_reps = target_reps
        if last_sets is not None:
            cw.last_sets = last_sets
        if status:
            cw.status = status
    else:
        cw = CurrentWeight(
            exercise_id=exercise_id,
            weight=new_weight,
            target_reps=target_reps,
            last_sets=last_sets,
            status=status,
        )
        db.add(cw)
    await db.commit()
    return cw


def _exercise_to_dict(e: Exercise) -> Dict:
    return {
        "exercise_id": e.exercise_id,
        "name": e.name,
        "day": e.day,
        "order": e.order,
        "category": e.category or "",
        "weight_step": e.weight_step,
        "reps_min": e.reps_min,
        "reps_max": e.reps_max,
        "rest_seconds": e.rest_seconds,
        "default_sets": e.default_sets,
        "notes": e.notes or "",
    }


def _weight_to_dict(w: CurrentWeight) -> Dict:
    return {
        "exercise_id": w.exercise_id,
        "current_weight": w.weight,
        "target_reps": w.target_reps or "",
        "last_sets": w.last_sets or [],
        "status": w.status or "",
    }


async def create_workout(
    db: AsyncSession,
    day_type: str,
    week: int,
    phase: str,
    energy_before: int,
    sleep_hours: float,
    sleep_quality: int,
    back_pain: int,
    emotional_wave: str,
) -> Dict:
    """Создать новую тренировку."""
    workout = Workout(
        date=today_minsk(),
        day_type=day_type,
        week=week,
        phase=phase,
        energy_before=energy_before,
        sleep_hours=sleep_hours,
        sleep_quality=sleep_quality,
        back_pain=back_pain,
        emotional_wave=emotional_wave,
    )
    db.add(workout)
    await db.commit()
    await db.refresh(workout)
    logger.info(f"Created workout #{workout.id} day={day_type}")
    return _workout_to_dict(workout)


async def get_workout_by_id(db: AsyncSession, workout_id: int) -> Optional[Dict]:
    """Получить тренировку с подходами."""
    result = await db.execute(
        select(Workout)
        .options(selectinload(Workout.sets))
        .where(Workout.id == workout_id)
    )
    w = result.scalar_one_or_none()
    if not w:
        return None
    d = _workout_to_dict(w)
    # Загружаем имена упражнений
    exercise_ids = list(set(s.exercise_id for s in w.sets))
    ex_result = await db.execute(
        select(Exercise).where(Exercise.exercise_id.in_(exercise_ids))
    )
    ex_map = {e.exercise_id: e for e in ex_result.scalars().all()}

    d["sets"] = [
        {
            "id": s.id,
            "exercise_id": s.exercise_id,
            "exercise_name": ex_map[s.exercise_id].name if s.exercise_id in ex_map else s.exercise_id,
            "set_number": s.set_number,
            "weight": s.weight,
            "reps": s.reps,
            "rpe": s.rpe,
            "notes": s.notes or "",
        }
        for s in sorted(w.sets, key=lambda x: (
            ex_map[x.exercise_id].order if x.exercise_id in ex_map else 999,
            x.set_number
        ))
    ]
    return d


async def add_workout_set(
    db: AsyncSession,
    workout_id: int,
    exercise_id: str,
    set_number: int,
    weight: float,
    reps: int,
    rpe: Optional[int] = None,
    notes: Optional[str] = None,
) -> Dict:
    """Добавить подход к тренировке."""
    ws = WorkoutSet(
        workout_id=workout_id,
        exercise_id=exercise_id,
        set_number=set_number,
        weight=weight,
        reps=reps,
        rpe=rpe,
        notes=notes,
    )
    db.add(ws)
    await db.commit()
    await db.refresh(ws)
    logger.info(f"Added set #{ws.id} to workout #{workout_id}: {exercise_id} {weight}x{reps}")
    return {
        "id": ws.id,
        "exercise_id": ws.exercise_id,
        "set_number": ws.set_number,
        "weight": ws.weight,
        "reps": ws.reps,
        "rpe": ws.rpe,
        "notes": ws.notes or "",
    }


async def complete_workout(
    db: AsyncSession,
    workout_id: int,
    energy_after: int,
    notes: Optional[str] = None,
) -> Optional[Dict]:
    """Завершить тренировку: energy_after + обновить текущие веса."""
    result = await db.execute(
        select(Workout)
        .options(selectinload(Workout.sets))
        .where(Workout.id == workout_id)
    )
    w = result.scalar_one_or_none()
    if not w:
        return None

    w.energy_after = energy_after
    if notes:
        w.notes = notes

    # Обновляем текущие веса по результатам тренировки
    sets_by_exercise: Dict[str, List[WorkoutSet]] = {}
    for s in w.sets:
        sets_by_exercise.setdefault(s.exercise_id, []).append(s)

    progress_updates = []
    for exercise_id, sets in sets_by_exercise.items():
        sets_sorted = sorted(sets, key=lambda x: x.set_number)
        last_weight = sets_sorted[-1].weight
        last_reps = [s.reps for s in sets_sorted[-4:]]
        last_rpes = [s.rpe for s in sets_sorted[-4:] if s.rpe]
        avg_rpe = sum(last_rpes) / len(last_rpes) if last_rpes else 0

        # Проверяем прогресс: все подходы RPE <= 8 и reps >= target
        ex_result = await db.execute(
            select(Exercise).where(Exercise.exercise_id == exercise_id)
        )
        exercise = ex_result.scalar_one_or_none()

        status = "in_progress"
        if exercise and avg_rpe > 0:
            all_reps_ok = all(r >= exercise.reps_min for r in last_reps)
            rpe_ok = avg_rpe <= 8
            if all_reps_ok and rpe_ok and len(last_reps) >= exercise.default_sets:
                status = "ready"

        target_reps = f"{exercise.reps_min}-{exercise.reps_max}" if exercise else ""
        await update_current_weight(
            db, exercise_id, last_weight, target_reps,
            last_sets=last_reps, status=status,
        )
        progress_updates.append({
            "exercise_id": exercise_id,
            "weight": last_weight,
            "avg_rpe": round(avg_rpe, 1),
            "status": status,
            "weight_step": exercise.weight_step if exercise else 2.5,
        })

    await db.commit()

    d = _workout_to_dict(w)
    d["progress_updates"] = progress_updates
    return d


def _workout_to_dict(w: Workout) -> Dict:
    return {
        "id": w.id,
        "date": w.date.isoformat(),
        "day_type": w.day_type,
        "week": w.week,
        "phase": w.phase or "",
        "energy_before": w.energy_before,
        "energy_after": w.energy_after,
        "sleep_hours": w.sleep_hours,
        "sleep_quality": w.sleep_quality or "",
        "back_pain": w.back_pain or "",
        "emotional_wave": w.emotional_wave or "",
        "notes": w.notes or "",
    }

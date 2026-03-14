"""Workout CRUD operations (PostgreSQL)."""

import logging
from datetime import date, timedelta
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

    weeks_elapsed = (date.today() - first.date).days // 7 + 1

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
    # Последние 10 подходов по данному упражнению
    result = await db.execute(
        select(WorkoutSet)
        .join(Workout, WorkoutSet.workout_id == Workout.id)
        .where(WorkoutSet.exercise_id == exercise_id)
        .order_by(desc(Workout.date), WorkoutSet.set_number)
        .limit(30)
    )
    sets = list(result.scalars().all())

    if not sets:
        return {"exercise_id": exercise_id, "sets": [], "trend": "no_data"}

    # Получаем даты тренировок
    workout_ids_list = list({s.workout_id for s in sets})
    workout_dates: Dict[int, str] = {}
    if workout_ids_list:
        w_result = await db.execute(
            select(Workout).where(Workout.id.in_(workout_ids_list))
        )
        for w in w_result.scalars().all():
            workout_dates[w.id] = w.date.isoformat()

    # Агрегируем по тренировкам
    by_workout: Dict[int, List] = {}
    for s in sets:
        if s.workout_id not in by_workout:
            by_workout[s.workout_id] = []
        by_workout[s.workout_id].append({"weight": s.weight, "reps": s.reps, "rpe": s.rpe})

    # Тренд: последние 3 тренировки
    workout_ids = list(by_workout.keys())
    recent = workout_ids[:3]
    trend = "stable"
    if len(recent) >= 2:
        last_w = max(s["weight"] for s in by_workout[recent[0]])
        prev_w = max(s["weight"] for s in by_workout[recent[1]])
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
            {"workout_id": wid, "date": workout_dates.get(wid, ""), "sets": by_workout[wid]}
            for wid in workout_ids[:10]
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


async def create_workout(
    db: AsyncSession,
    day_type: str,
    energy_before: int,
    sleep_hours: Optional[float] = None,
    sleep_quality: Optional[int] = None,
    back_pain: Optional[int] = None,
    emotional_wave: Optional[str] = None,
) -> Workout:
    """Создать новую тренировку."""
    phase_info = await get_current_week_and_phase(db)
    workout = Workout(
        date=date.today(),
        day_type=day_type,
        week=phase_info.get("current_week"),
        phase=phase_info.get("phase_name"),
        energy_before=energy_before,
        sleep_hours=sleep_hours,
        sleep_quality=sleep_quality,
        back_pain=back_pain,
        emotional_wave=emotional_wave,
    )
    db.add(workout)
    await db.commit()
    await db.refresh(workout)
    return workout


async def complete_workout(
    db: AsyncSession,
    workout_id: int,
    energy_after: int,
    notes: Optional[str] = None,
) -> Optional[Workout]:
    """Завершить тренировку."""
    result = await db.execute(select(Workout).where(Workout.id == workout_id))
    workout = result.scalar_one_or_none()
    if not workout:
        return None
    workout.energy_after = energy_after
    workout.notes = notes
    await db.commit()
    await db.refresh(workout)
    return workout


async def add_workout_set(
    db: AsyncSession,
    workout_id: int,
    exercise_id: str,
    set_number: int,
    weight: float,
    reps: int,
    rpe: Optional[int] = None,
    notes: Optional[str] = None,
) -> WorkoutSet:
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
    return ws


async def get_workout_with_sets(db: AsyncSession, workout_id: int) -> Optional[Dict]:
    """Получить тренировку с подходами."""
    result = await db.execute(
        select(Workout)
        .options(selectinload(Workout.sets))
        .where(Workout.id == workout_id)
    )
    workout = result.scalar_one_or_none()
    if not workout:
        return None

    # Получим имена упражнений
    exercise_ids = list({s.exercise_id for s in workout.sets})
    ex_names: Dict[str, str] = {}
    if exercise_ids:
        ex_result = await db.execute(
            select(Exercise).where(Exercise.exercise_id.in_(exercise_ids))
        )
        for ex in ex_result.scalars().all():
            ex_names[ex.exercise_id] = ex.name

    return {
        **_workout_to_dict(workout),
        "sleep_quality": workout.sleep_quality,
        "sets": [
            {
                "id": s.id,
                "exercise_id": s.exercise_id,
                "exercise_name": ex_names.get(s.exercise_id, s.exercise_id),
                "set_number": s.set_number,
                "weight": s.weight,
                "reps": s.reps,
                "rpe": s.rpe,
            }
            for s in sorted(workout.sets, key=lambda x: (x.exercise_id, x.set_number))
        ],
    }


async def get_workouts_for_month(db: AsyncSession, month: int, year: int) -> List[Dict]:
    """Тренировки за месяц для календаря."""
    from sqlalchemy import extract as sa_extract
    result = await db.execute(
        select(Workout)
        .where(
            sa_extract("month", Workout.date) == month,
            sa_extract("year", Workout.date) == year,
        )
        .order_by(Workout.date)
    )
    workouts = result.scalars().all()
    return [
        {"date": w.date.isoformat(), "day_type": w.day_type, "id": w.id}
        for w in workouts
    ]


async def get_workout_comparison(db: AsyncSession, workout_id: int) -> Dict:
    """Сравнить тренировку с предыдущей такого же типа."""
    current = await get_workout_with_sets(db, workout_id)
    if not current:
        return {"current": None, "previous": None}

    # Найти предыдущую тренировку того же типа
    result = await db.execute(
        select(Workout)
        .where(
            Workout.day_type == current["day_type"],
            Workout.id < workout_id,
        )
        .order_by(desc(Workout.id))
        .limit(1)
    )
    prev_workout = result.scalar_one_or_none()
    previous = await get_workout_with_sets(db, prev_workout.id) if prev_workout else None

    return {"current": current, "previous": previous}


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
    }


def _weight_to_dict(w: CurrentWeight) -> Dict:
    return {
        "exercise_id": w.exercise_id,
        "current_weight": w.weight,
        "target_reps": w.target_reps or "",
        "last_sets": w.last_sets or [],
        "status": w.status or "",
    }


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
        "back_pain": w.back_pain,
        "emotional_wave": w.emotional_wave or "",
        "notes": w.notes or "",
    }

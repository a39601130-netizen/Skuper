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
        "sleep_quality": w.sleep_quality or "",
        "back_pain": w.back_pain or "",
        "emotional_wave": w.emotional_wave or "",
        "notes": w.notes or "",
    }

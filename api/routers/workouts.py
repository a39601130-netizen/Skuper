"""API роутер: тренировки (PostgreSQL)."""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from db.database import get_db
from db.services.workout import (
    get_current_weights, get_workout_history,
    determine_next_day, get_current_week_and_phase, get_exercises,
    create_workout, complete_workout, add_workout_set,
    get_workout_with_sets, get_workouts_for_month, get_workout_comparison,
)

router = APIRouter(prefix="/api/workouts", tags=["workouts"])


class WorkoutCreateRequest(BaseModel):
    day_type: str
    energy_before: int
    sleep_hours: Optional[float] = None
    sleep_quality: Optional[int] = None
    back_pain: Optional[int] = None
    emotional_wave: Optional[str] = None


class WorkoutCompleteRequest(BaseModel):
    energy_after: int
    notes: Optional[str] = None


class WorkoutSetRequest(BaseModel):
    exercise_id: str
    set_number: int
    weight: float
    reps: int
    rpe: Optional[int] = None
    notes: Optional[str] = None


@router.get("/history")
async def workout_history(
    limit: int = Query(default=10, ge=1, le=50),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_workout_history(db, limit=limit)


@router.get("/next")
async def next_workout(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    next_day = await determine_next_day(db)
    phase = await get_current_week_and_phase(db)
    exercises = await get_exercises(db, day=next_day)
    weights = await get_current_weights(db)
    for ex in exercises:
        eid = ex["exercise_id"]
        w = weights.get(eid, {})
        ex["current_weight"] = w.get("current_weight", 0)
        ex["target_reps"] = w.get("target_reps", "")
        ex["status"] = w.get("status", "")
    return {"next_day": next_day, "phase": phase, "exercises": exercises}


@router.get("/weights")
async def current_weights(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    exercises = await get_exercises(db)
    weights = await get_current_weights(db)
    return [
        {
            **ex,
            "current_weight": weights.get(ex["exercise_id"], {}).get("current_weight", 0),
            "target_reps": weights.get(ex["exercise_id"], {}).get("target_reps", ""),
            "status": weights.get(ex["exercise_id"], {}).get("status", ""),
        }
        for ex in exercises
    ]


@router.get("/calendar")
async def workout_calendar(
    month: int = Query(ge=1, le=12),
    year: int = Query(ge=2020),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_workouts_for_month(db, month=month, year=year)


@router.post("")
async def create_workout_endpoint(
    data: WorkoutCreateRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workout = await create_workout(
        db,
        day_type=data.day_type,
        energy_before=data.energy_before,
        sleep_hours=data.sleep_hours,
        sleep_quality=data.sleep_quality,
        back_pain=data.back_pain,
        emotional_wave=data.emotional_wave,
    )
    return await get_workout_with_sets(db, workout.id)


@router.get("/{workout_id}")
async def get_workout_endpoint(
    workout_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workout = await get_workout_with_sets(db, workout_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout


@router.put("/{workout_id}/complete")
async def complete_workout_endpoint(
    workout_id: int,
    data: WorkoutCompleteRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workout = await complete_workout(
        db, workout_id=workout_id,
        energy_after=data.energy_after, notes=data.notes,
    )
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return await get_workout_with_sets(db, workout_id)


@router.post("/{workout_id}/sets")
async def add_set_endpoint(
    workout_id: int,
    data: WorkoutSetRequest,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    ws = await add_workout_set(
        db,
        workout_id=workout_id,
        exercise_id=data.exercise_id,
        set_number=data.set_number,
        weight=data.weight,
        reps=data.reps,
        rpe=data.rpe,
        notes=data.notes,
    )
    return {"status": "ok", "id": ws.id}


@router.get("/{workout_id}/compare")
async def compare_workout(
    workout_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_workout_comparison(db, workout_id)

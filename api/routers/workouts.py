"""API роутер: тренировки (PostgreSQL)."""

from typing import Optional, List
from pydantic import BaseModel, Field

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from db.database import get_db
from db.services.workout import (
    get_current_weights, get_workout_history,
    determine_next_day, get_current_week_and_phase, get_exercises,
    create_workout, get_workout_by_id, add_workout_set, complete_workout,
    get_exercise_progress, delete_workout,
)

router = APIRouter(prefix="/api/workouts", tags=["workouts"])


# --- Pydantic schemas ---

class WorkoutCreate(BaseModel):
    day_type: str = Field(..., pattern="^[AB]$")
    week: int = Field(..., ge=1)
    phase: str
    energy_before: int = Field(..., ge=1, le=10)
    sleep_hours: float = Field(..., ge=0, le=24)
    sleep_quality: int = Field(..., ge=1, le=10)
    back_pain: int = Field(..., ge=1, le=10)
    emotional_wave: str


class SetCreate(BaseModel):
    exercise_id: str
    set_number: int = Field(..., ge=1)
    weight: float = Field(..., ge=0)
    reps: int = Field(..., ge=1)
    rpe: Optional[int] = Field(None, ge=1, le=10)
    notes: Optional[str] = None


class WorkoutComplete(BaseModel):
    energy_after: int = Field(..., ge=1, le=10)
    notes: Optional[str] = None


# --- Endpoints ---

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
    all_exercises = await get_exercises(db, day=next_day)
    exercises = [ex for ex in all_exercises if ex.get("order", 0) < 100]
    weights = await get_current_weights(db)

    # Добавляем историю последних подходов к каждому упражнению
    for ex in exercises:
        eid = ex["exercise_id"]
        w = weights.get(eid, {})
        ex["current_weight"] = w.get("current_weight", 0)
        ex["target_reps"] = w.get("target_reps", "")
        ex["status"] = w.get("status", "")
        ex["last_sets"] = w.get("last_sets", [])

        # Добавляем параметры из модели Exercise
        progress = await get_exercise_progress(db, eid)
        ex["history"] = progress.get("history_by_workout", [])[:3]

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


@router.post("")
async def create_workout_endpoint(
    data: WorkoutCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await create_workout(
        db,
        day_type=data.day_type,
        week=data.week,
        phase=data.phase,
        energy_before=data.energy_before,
        sleep_hours=data.sleep_hours,
        sleep_quality=data.sleep_quality,
        back_pain=data.back_pain,
        emotional_wave=data.emotional_wave,
    )
    return result


@router.delete("/{workout_id}")
async def delete_workout_endpoint(
    workout_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    deleted = await delete_workout(db, workout_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Тренировка не найдена")
    return {"status": "ok"}


@router.get("/{workout_id}")
async def get_workout(
    workout_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await get_workout_by_id(db, workout_id)
    if not result:
        raise HTTPException(status_code=404, detail="Тренировка не найдена")
    return result


@router.post("/{workout_id}/sets")
async def add_set(
    workout_id: int,
    data: SetCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    workout = await get_workout_by_id(db, workout_id)
    if not workout:
        raise HTTPException(status_code=404, detail="Тренировка не найдена")

    result = await add_workout_set(
        db,
        workout_id=workout_id,
        exercise_id=data.exercise_id,
        set_number=data.set_number,
        weight=data.weight,
        reps=data.reps,
        rpe=data.rpe,
        notes=data.notes,
    )
    return result


@router.put("/{workout_id}/complete")
async def complete_workout_endpoint(
    workout_id: int,
    data: WorkoutComplete,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await complete_workout(
        db,
        workout_id=workout_id,
        energy_after=data.energy_after,
        notes=data.notes,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Тренировка не найдена")
    return result

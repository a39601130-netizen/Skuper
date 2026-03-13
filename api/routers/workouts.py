"""API роутер: тренировки (PostgreSQL)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from db.database import get_db
from db.services.workout import (
    get_current_weights, get_workout_history,
    determine_next_day, get_current_week_and_phase, get_exercises,
)

router = APIRouter(prefix="/api/workouts", tags=["workouts"])


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

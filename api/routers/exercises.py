"""API роутер: упражнения (PostgreSQL)."""

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from db.database import get_db
from db.services.workout import get_exercises, get_exercise_by_id, get_exercise_progress, update_current_weight, get_current_weights

router = APIRouter(prefix="/api/exercises", tags=["exercises"])


class WeightUpdate(BaseModel):
    weight: float


@router.get("")
async def list_exercises(
    day: Optional[str] = Query(default=None),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_exercises(db, day=day)


@router.get("/{exercise_id}/alternative")
async def get_alternative(
    exercise_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Возвращает альтернативное упражнение (exercise_id + '_alt') с текущим весом."""
    from fastapi import HTTPException
    alt_id = exercise_id + "_alt"
    ex = await get_exercise_by_id(db, alt_id)
    if not ex:
        raise HTTPException(status_code=404, detail="Alternative not found")
    weights = await get_current_weights(db)
    w = weights.get(alt_id, {})
    ex["current_weight"] = w.get("current_weight", 0)
    ex["target_reps"] = w.get("target_reps", "")
    ex["status"] = w.get("status", "")
    ex["last_sets"] = w.get("last_sets", [])
    ex["history"] = []
    return ex


@router.get("/{exercise_id}/progress")
async def exercise_progress(
    exercise_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_exercise_progress(db, exercise_id)


@router.put("/{exercise_id}/weight")
async def update_weight(
    exercise_id: str,
    data: WeightUpdate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    await update_current_weight(db, exercise_id=exercise_id, new_weight=data.weight)
    return {"status": "ok"}

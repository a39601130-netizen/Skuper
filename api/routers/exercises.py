"""API роутер: упражнения (PostgreSQL)."""

from fastapi import APIRouter, Depends, Query
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from db.database import get_db
from db.services.workout import get_exercises, get_exercise_progress

router = APIRouter(prefix="/api/exercises", tags=["exercises"])


@router.get("")
async def list_exercises(
    day: Optional[str] = Query(default=None),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_exercises(db, day=day)


@router.get("/{exercise_id}/progress")
async def exercise_progress(
    exercise_id: str,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_exercise_progress(db, exercise_id)

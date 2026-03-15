"""API роутер: статистика (PostgreSQL)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from db.database import get_db
from db.services.finance import get_monthly_summary, get_income_by_days, get_weekly_summary, get_daily_spending

router = APIRouter(prefix="/api/stats", tags=["stats"])


@router.get("/monthly")
async def monthly_summary(
    month: int = Query(default=None, ge=1, le=12),
    year: int = Query(default=None, ge=2020, le=2100),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_monthly_summary(db, month=month, year=year)


@router.get("/income")
async def income_stats(
    month: int = Query(default=None, ge=1, le=12),
    year: int = Query(default=None, ge=2020, le=2100),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_income_by_days(db, month=month, year=year)


@router.get("/weekly")
async def weekly_summary(
    days_back: int = Query(default=7, ge=1, le=30),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_weekly_summary(db, days_back=days_back)


@router.get("/daily-spending")
async def daily_spending(
    month: int = Query(default=None, ge=1, le=12),
    year: int = Query(default=None, ge=2020, le=2100),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_daily_spending(db, month=month, year=year)

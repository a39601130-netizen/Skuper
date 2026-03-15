"""API роутер: категории и справочники (PostgreSQL)."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from db.database import get_db
from db.services.finance import get_categories, get_accounts, get_category_spending

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("")
async def list_categories(
    month: int = Query(default=None, ge=1, le=12),
    year: int = Query(default=None, ge=2020, le=2100),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cats = await get_categories(db)
    spending = await get_category_spending(db, month=month, year=year)
    return [
        {
            "name": c.name,
            "type": c.type,
            "emoji": c.emoji or "📦",
            "budget": c.budget_limit,
            "spent": spending.get(c.name, 0.0),
            "remaining": max(0.0, c.budget_limit - spending.get(c.name, 0.0)) if c.budget_limit > 0 else 0.0,
            "progress": spending.get(c.name, 0.0) / c.budget_limit if c.budget_limit > 0 else 0.0,
        }
        for c in cats
    ]


@router.get("/references")
async def get_references(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    accounts = await get_accounts(db)
    expense_cats = await get_categories(db, type_filter="Расход")
    income_cats = await get_categories(db, type_filter="Доход")
    return {
        "types": ["Расход", "Доход", "Перевод", "Обмен валюты"],
        "accounts": [a.name for a in accounts],
        "categories": [c.name for c in expense_cats],
        "income_categories": [c.name for c in income_cats],
    }

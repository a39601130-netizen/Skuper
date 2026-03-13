"""API роутер: категории и справочники (PostgreSQL)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from db.database import get_db
from db.services.finance import get_categories, get_accounts

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("")
async def list_categories(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    cats = await get_categories(db)
    return [
        {
            "name": c.name,
            "type": c.type,
            "emoji": c.emoji or "📦",
            "budget": c.budget_limit,
            "spent": 0.0,
            "remaining": c.budget_limit,
            "progress": 0.0,
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

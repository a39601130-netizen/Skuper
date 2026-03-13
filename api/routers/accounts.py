"""API роутер: счета (PostgreSQL)."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from db.database import get_db
from db.services.finance import get_accounts

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("")
async def list_accounts(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    accounts = await get_accounts(db)
    return [
        {
            "name": a.name,
            "currency": a.currency,
            "current": a.balance,
            "initial": a.initial_balance,
            "emoji": a.emoji or "💳",
        }
        for a in accounts
    ]

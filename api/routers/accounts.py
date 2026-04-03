"""API роутер: счета (PostgreSQL)."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from db.database import get_db
from db.services.finance import get_accounts, update_account_balance

router = APIRouter(prefix="/api/accounts", tags=["accounts"])


@router.get("")
async def list_accounts(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    accounts = await get_accounts(db)
    return [
        {
            "id": a.id,
            "name": a.name,
            "currency": a.currency,
            "current": a.balance,
            "initial": a.initial_balance,
            "emoji": a.emoji or "💳",
        }
        for a in accounts
    ]


class AccountBalanceUpdate(BaseModel):
    balance: float


@router.put("/{account_id}")
async def update_balance(
    account_id: int,
    body: AccountBalanceUpdate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    account = await update_account_balance(db, account_id, body.balance)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {
        "id": account.id,
        "name": account.name,
        "currency": account.currency,
        "current": account.balance,
        "initial": account.initial_balance,
        "emoji": account.emoji or "💳",
    }

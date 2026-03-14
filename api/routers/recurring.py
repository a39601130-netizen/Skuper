"""API роутер: повторяющиеся транзакции."""

from datetime import date
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from db.database import get_db
from db.services.recurring import (
    get_recurring_transactions, create_recurring_transaction,
    delete_recurring_transaction, apply_recurring_transaction,
)

router = APIRouter(prefix="/api/recurring", tags=["recurring"])


class RecurringCreate(BaseModel):
    name: str
    type: str
    account: str
    category: Optional[str] = None
    amount: float
    currency: str = "BYN"
    frequency: str  # daily / weekly / monthly
    next_date: date


@router.get("")
async def list_recurring(
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_recurring_transactions(db)


@router.post("")
async def create_recurring(
    data: RecurringCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        rt = await create_recurring_transaction(
            db,
            name=data.name,
            type=data.type,
            account_name=data.account,
            category_name=data.category,
            amount=data.amount,
            currency=data.currency,
            frequency=data.frequency,
            next_date=data.next_date,
        )
        return rt
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{rt_id}")
async def remove_recurring(
    rt_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    success = await delete_recurring_transaction(db, rt_id)
    if not success:
        raise HTTPException(status_code=404, detail="Not found")
    return {"status": "ok"}


@router.post("/{rt_id}/apply")
async def apply_recurring(
    rt_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    try:
        tx_id = await apply_recurring_transaction(db, rt_id)
        if tx_id is None:
            raise HTTPException(status_code=404, detail="Not found")
        return {"status": "ok", "transaction_id": tx_id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

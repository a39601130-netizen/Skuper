"""API роутер: транзакции (PostgreSQL)."""

from datetime import date
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from db.database import get_db
from db.services.finance import add_transaction, get_recent_transactions, delete_transaction

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


class TransactionCreate(BaseModel):
    date: Optional[date] = None
    type: str
    account: str
    category: Optional[str] = None
    amount: float
    to_account: Optional[str] = None
    comment: Optional[str] = None
    hours: Optional[float] = None
    exchange_rate: Optional[float] = None
    amount_to: Optional[float] = None
    currency: str = "BYN"


@router.get("")
async def list_transactions(
    limit: int = Query(default=20, ge=1, le=100),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_recent_transactions(db, limit=limit)


@router.post("")
async def create_transaction(
    data: TransactionCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tx_date = data.date or date.today()
    try:
        tx = await add_transaction(
            db,
            trans_date=tx_date,
            trans_type=data.type,
            account_name=data.account,
            amount=data.amount,
            category_name=data.category,
            to_account_name=data.to_account,
            comment=data.comment,
            hours=data.hours,
            exchange_rate=data.exchange_rate,
            amount_to=data.amount_to,
            currency=data.currency,
        )
        return {"status": "ok", "id": tx.id}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{tx_id}")
async def remove_transaction(
    tx_id: int,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    success = await delete_transaction(db, tx_id)
    if not success:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return {"status": "ok"}

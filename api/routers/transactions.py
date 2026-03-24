"""API роутер: транзакции (PostgreSQL)."""

import asyncio
import logging
from datetime import date

from utils.timezone import today_minsk
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, BeforeValidator, field_validator, model_validator
from sqlalchemy.ext.asyncio import AsyncSession

from api.deps import get_current_user
from db.database import get_db
from db.services.finance import add_transaction, get_recent_transactions, delete_transaction

logger = logging.getLogger(__name__)


def _sync_tx_to_sheets(tx_data: dict):
    """Background helper: sync transaction to Sheets."""
    try:
        from services.sync import sync_transaction_to_sheets
        sync_transaction_to_sheets(**tx_data)
    except Exception as e:
        logger.error(f"Background sheets sync failed: {e}")


def _delete_tx_from_sheets(tx_id: int):
    """Background helper: delete transaction from Sheets."""
    try:
        from services.sync import delete_transaction_from_sheets
        delete_transaction_from_sheets(tx_id)
    except Exception as e:
        logger.error(f"Background sheets delete failed: {e}")

router = APIRouter(prefix="/api/transactions", tags=["transactions"])

VALID_TYPES = {"Расход", "Доход", "Перевод", "Обмен валюты"}


def _parse_optional_date(v):
    if v is None:
        return None
    if isinstance(v, str):
        return date.fromisoformat(v)
    return v


OptionalDate = Annotated[Optional[date], BeforeValidator(_parse_optional_date)]


class TransactionCreate(BaseModel):
    date: OptionalDate = None
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

    @field_validator("amount")
    @classmethod
    def amount_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError("Сумма должна быть больше 0")
        return v

    @field_validator("type")
    @classmethod
    def type_valid(cls, v: str) -> str:
        if v not in VALID_TYPES:
            raise ValueError(f"Тип должен быть одним из: {', '.join(VALID_TYPES)}")
        return v

    @field_validator("date")
    @classmethod
    def date_not_future(cls, v: Optional[date]) -> Optional[date]:
        if v and v > today_minsk():
            raise ValueError("Дата не может быть в будущем")
        return v

    @model_validator(mode='after')
    def validate_transfer_and_exchange(self):
        if self.type in ("Перевод", "Обмен валюты") and not self.to_account:
            raise ValueError("Для перевода/обмена нужно указать счёт назначения")
        if self.type == "Обмен валюты":
            if not self.exchange_rate:
                raise ValueError("Для обмена валюты нужен курс")
            if not self.amount_to:
                raise ValueError("Для обмена валюты нужна сумма зачисления")
        return self


@router.get("")
async def list_transactions(
    limit: int = Query(default=20, ge=1, le=100),
    date_from: Optional[date] = Query(default=None),
    date_to: Optional[date] = Query(default=None),
    category: Optional[str] = Query(default=None),
    type: Optional[str] = Query(default=None),
    account: Optional[str] = Query(default=None),
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    return await get_recent_transactions(
        db, limit=limit,
        date_from=date_from, date_to=date_to,
        category=category, trans_type=type, account_name=account,
    )


@router.post("")
async def create_transaction(
    data: TransactionCreate,
    user: dict = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tx_date = data.date or today_minsk()
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
        # Background sync to Google Sheets (collect data while in session)
        tx_data = {
            "tx_id": tx.id,
            "tx_date": tx.date,
            "tx_type": tx.type,
            "account_name": data.account,
            "category_name": data.category or "",
            "amount": tx.amount,
            "to_account_name": data.to_account or "",
            "comment": tx.comment or "",
            "hours": tx.hours,
            "exchange_rate": tx.exchange_rate,
            "amount_to": tx.amount_to,
            "currency": tx.currency or "BYN",
        }
        asyncio.get_running_loop().run_in_executor(
            None, _sync_tx_to_sheets, tx_data
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
    # Background delete from Google Sheets
    asyncio.get_running_loop().run_in_executor(
        None, _delete_tx_from_sheets, tx_id
    )
    return {"status": "ok"}

"""Recurring transactions CRUD (PostgreSQL)."""

import calendar
from datetime import date, timedelta
from typing import Optional, List, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import RecurringTransaction, Account, Category
from db.services.finance import add_transaction, get_account_by_name, get_category_by_name


async def get_recurring_transactions(db: AsyncSession) -> List[Dict[str, Any]]:
    result = await db.execute(
        select(RecurringTransaction)
        .options(
            selectinload(RecurringTransaction.account),
            selectinload(RecurringTransaction.category),
        )
        .where(RecurringTransaction.is_active == True)
        .order_by(RecurringTransaction.next_date)
    )
    rts = result.scalars().all()
    return [_rt_to_dict(rt) for rt in rts]


async def create_recurring_transaction(
    db: AsyncSession,
    name: str,
    type: str,
    account_name: str,
    amount: float,
    frequency: str,
    next_date: date,
    category_name: Optional[str] = None,
    currency: str = "BYN",
) -> Dict[str, Any]:
    account = await get_account_by_name(db, account_name)
    if not account:
        raise ValueError(f"Account not found: {account_name}")

    category_id = None
    if category_name:
        cat_type = "Доход" if type == "Доход" else "Расход"
        cat = await get_category_by_name(db, category_name, cat_type)
        if cat:
            category_id = cat.id

    rt = RecurringTransaction(
        name=name,
        type=type,
        account_id=account.id,
        category_id=category_id,
        amount=amount,
        currency=currency,
        frequency=frequency,
        next_date=next_date,
    )
    db.add(rt)
    await db.commit()
    await db.refresh(rt, ["account", "category"])
    return _rt_to_dict(rt)


async def delete_recurring_transaction(db: AsyncSession, rt_id: int) -> bool:
    result = await db.execute(
        select(RecurringTransaction).where(RecurringTransaction.id == rt_id)
    )
    rt = result.scalar_one_or_none()
    if not rt:
        return False
    rt.is_active = False
    await db.commit()
    return True


async def apply_recurring_transaction(db: AsyncSession, rt_id: int) -> Optional[int]:
    result = await db.execute(
        select(RecurringTransaction)
        .options(
            selectinload(RecurringTransaction.account),
            selectinload(RecurringTransaction.category),
        )
        .where(RecurringTransaction.id == rt_id, RecurringTransaction.is_active == True)
    )
    rt = result.scalar_one_or_none()
    if not rt:
        return None

    tx = await add_transaction(
        db,
        trans_date=date.today(),
        trans_type=rt.type,
        account_name=rt.account.name,
        amount=rt.amount,
        category_name=rt.category.name if rt.category else None,
        currency=rt.currency,
    )

    # Обновить next_date
    if rt.frequency == "daily":
        rt.next_date = rt.next_date + timedelta(days=1)
    elif rt.frequency == "weekly":
        rt.next_date = rt.next_date + timedelta(weeks=1)
    elif rt.frequency == "monthly":
        month = rt.next_date.month % 12 + 1
        year = rt.next_date.year + (1 if rt.next_date.month == 12 else 0)
        max_day = calendar.monthrange(year, month)[1]
        day = min(rt.next_date.day, max_day)
        rt.next_date = date(year, month, day)

    await db.commit()
    return tx.id


def _rt_to_dict(rt: RecurringTransaction) -> Dict[str, Any]:
    return {
        "id": rt.id,
        "name": rt.name,
        "type": rt.type,
        "account": rt.account.name if rt.account else "",
        "category": rt.category.name if rt.category else "",
        "amount": rt.amount,
        "currency": rt.currency,
        "frequency": rt.frequency,
        "next_date": rt.next_date.isoformat(),
        "is_active": rt.is_active,
    }

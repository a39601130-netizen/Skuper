"""Finance CRUD operations (PostgreSQL)."""

import logging
from datetime import date, datetime
from typing import Optional, List, Dict, Any

from sqlalchemy import select, func, and_, extract
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from db.models import Account, Category, Transaction
import config

logger = logging.getLogger(__name__)


async def get_accounts(db: AsyncSession) -> List[Account]:
    result = await db.execute(
        select(Account).where(Account.is_active == True).order_by(Account.sort_order)
    )
    return list(result.scalars().all())


async def get_categories(db: AsyncSession, type_filter: Optional[str] = None) -> List[Category]:
    q = select(Category).where(Category.is_active == True)
    if type_filter:
        q = q.where(Category.type == type_filter)
    q = q.order_by(Category.sort_order)
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_account_by_name(db: AsyncSession, name: str) -> Optional[Account]:
    result = await db.execute(select(Account).where(Account.name == name))
    return result.scalar_one_or_none()


async def get_category_by_name(db: AsyncSession, name: str, type: str) -> Optional[Category]:
    result = await db.execute(
        select(Category).where(Category.name == name, Category.type == type)
    )
    return result.scalar_one_or_none()


async def add_transaction(
    db: AsyncSession,
    trans_date: date,
    trans_type: str,
    account_name: str,
    amount: float,
    category_name: Optional[str] = None,
    to_account_name: Optional[str] = None,
    comment: Optional[str] = None,
    hours: Optional[float] = None,
    exchange_rate: Optional[float] = None,
    amount_to: Optional[float] = None,
    currency: str = "BYN",
) -> Transaction:
    """Add a transaction and update account balances."""
    account = await get_account_by_name(db, account_name)
    if not account:
        raise ValueError(f"Account not found: {account_name}")

    category_id = None
    if category_name:
        cat_type = "Доход" if trans_type == "Доход" else "Расход"
        category = await get_category_by_name(db, category_name, cat_type)
        if category:
            category_id = category.id

    to_account_id = None
    if to_account_name:
        to_acc = await get_account_by_name(db, to_account_name)
        if to_acc:
            to_account_id = to_acc.id

    tx = Transaction(
        date=trans_date,
        type=trans_type,
        account_id=account.id,
        category_id=category_id,
        amount=amount,
        to_account_id=to_account_id,
        comment=comment,
        hours=hours,
        exchange_rate=exchange_rate,
        amount_to=amount_to,
        currency=currency,
    )
    db.add(tx)

    # Обновляем балансы
    byn_amount = amount_to if (currency != "BYN" and amount_to) else amount
    if trans_type == "Расход":
        account.balance -= byn_amount
    elif trans_type == "Доход":
        account.balance += byn_amount
    elif trans_type == "Перевод":
        account.balance -= amount
        if to_account_id:
            result = await db.execute(select(Account).where(Account.id == to_account_id))
            to_acc = result.scalar_one_or_none()
            if to_acc:
                to_acc.balance += amount

    await db.commit()
    await db.refresh(tx)
    return tx


async def get_recent_transactions(
    db: AsyncSession,
    limit: int = 20,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    category: Optional[str] = None,
    trans_type: Optional[str] = None,
    account_name: Optional[str] = None,
) -> List[Dict[str, Any]]:
    query = (
        select(Transaction)
        .options(
            selectinload(Transaction.account),
            selectinload(Transaction.category),
            selectinload(Transaction.to_account),
        )
    )
    if date_from:
        query = query.where(Transaction.date >= date_from)
    if date_to:
        query = query.where(Transaction.date <= date_to)
    if trans_type:
        query = query.where(Transaction.type == trans_type)
    if category:
        query = query.join(Transaction.category).where(Category.name == category)
    if account_name:
        query = query.join(Transaction.account).where(Account.name == account_name)
    query = query.order_by(Transaction.date.desc(), Transaction.id.desc()).limit(limit)
    result = await db.execute(query)
    txs = result.scalars().all()
    return [_tx_to_dict(tx) for tx in txs]


async def delete_transaction(db: AsyncSession, tx_id: int) -> bool:
    result = await db.execute(select(Transaction).where(Transaction.id == tx_id))
    tx = result.scalar_one_or_none()
    if not tx:
        return False

    # Откатываем баланс
    result = await db.execute(select(Account).where(Account.id == tx.account_id))
    account = result.scalar_one_or_none()
    if account:
        byn_amount = tx.amount_to if (tx.currency != "BYN" and tx.amount_to) else tx.amount
        if tx.type == "Расход":
            account.balance += byn_amount
        elif tx.type == "Доход":
            account.balance -= byn_amount
        elif tx.type == "Перевод" and tx.to_account_id:
            account.balance += tx.amount
            result2 = await db.execute(select(Account).where(Account.id == tx.to_account_id))
            to_acc = result2.scalar_one_or_none()
            if to_acc:
                to_acc.balance -= tx.amount

    await db.delete(tx)
    await db.commit()
    return True


async def get_category_spending(db: AsyncSession) -> Dict[str, float]:
    """Расходы по категориям за текущий месяц. Возвращает {category_name: amount}."""
    today = date.today()
    result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.category))
        .where(
            Transaction.type == "Расход",
            extract("month", Transaction.date) == today.month,
            extract("year", Transaction.date) == today.year,
        )
    )
    txs = result.scalars().all()
    spending: Dict[str, float] = {}
    for tx in txs:
        cat_name = tx.category.name if tx.category else "Другое"
        amount = tx.amount_to if (tx.currency != "BYN" and tx.amount_to) else tx.amount
        spending[cat_name] = spending.get(cat_name, 0.0) + amount
    return spending


async def get_daily_spending(db: AsyncSession) -> List[Dict[str, Any]]:
    """Расходы по дням за текущий месяц. Возвращает [{date, amount}]."""
    today = date.today()
    result = await db.execute(
        select(Transaction)
        .where(
            Transaction.type == "Расход",
            extract("month", Transaction.date) == today.month,
            extract("year", Transaction.date) == today.year,
        )
    )
    txs = result.scalars().all()
    by_day: Dict[str, float] = {}
    for tx in txs:
        day_str = tx.date.strftime("%Y-%m-%d") if tx.date else str(today)
        amount = tx.amount_to if (tx.currency != "BYN" and tx.amount_to) else tx.amount
        by_day[day_str] = by_day.get(day_str, 0.0) + amount
    return [{"date": d, "amount": round(a, 2)} for d, a in sorted(by_day.items())]


async def get_monthly_summary(db: AsyncSession) -> Dict[str, Any]:
    """Месячная сводка: доходы, расходы, балансы, категории."""
    today = date.today()
    month, year = today.month, today.year

    # Все транзакции текущего месяца
    result = await db.execute(
        select(Transaction)
        .options(
            selectinload(Transaction.category),
            selectinload(Transaction.account),
        )
        .where(
            extract("month", Transaction.date) == month,
            extract("year", Transaction.date) == year,
        )
    )
    txs = list(result.scalars().all())

    total_income = 0.0
    total_expense = 0.0
    income_by_category: Dict[str, float] = {}
    expense_by_category: Dict[str, float] = {}

    for tx in txs:
        byn_amount = tx.amount_to if (tx.currency != "BYN" and tx.amount_to) else tx.amount
        if tx.type == "Доход":
            total_income += byn_amount
            cat_name = tx.category.name if tx.category else "Другое"
            income_by_category[cat_name] = income_by_category.get(cat_name, 0.0) + byn_amount
        elif tx.type == "Расход":
            total_expense += byn_amount
            cat_name = tx.category.name if tx.category else "Другое"
            expense_by_category[cat_name] = expense_by_category.get(cat_name, 0.0) + byn_amount

    # Счета
    accounts = await get_accounts(db)
    accounts_data = [
        {
            "name": a.name,
            "currency": a.currency,
            "current": a.balance,
            "initial": a.initial_balance,
            "emoji": a.emoji or config.CATEGORY_EMOJI.get(a.name, "💳"),
        }
        for a in accounts
    ]
    total_on_accounts = sum(a["current"] for a in accounts_data if a["currency"] == "BYN")

    # Категории с прогрессом
    categories = await get_categories(db)
    cats_data = []
    for cat in categories:
        if cat.type == "Расход":
            spent = expense_by_category.get(cat.name, 0.0)
        else:
            spent = income_by_category.get(cat.name, 0.0)

        progress = spent / cat.budget_limit if cat.budget_limit > 0 else 0.0
        cats_data.append({
            "name": cat.name,
            "type": cat.type,
            "emoji": cat.emoji or config.CATEGORY_EMOJI.get(cat.name, "📦"),
            "budget": cat.budget_limit,
            "spent": spent,
            "remaining": max(0.0, cat.budget_limit - spent) if cat.budget_limit > 0 else 0.0,
            "progress": progress,
        })

    over_budget = [c for c in cats_data if c["type"] == "Расход" and c["budget"] > 0 and c["progress"] >= 1]
    near_limit = [c for c in cats_data if c["type"] == "Расход" and c["budget"] > 0 and 0.8 <= c["progress"] < 1]

    return {
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense,
        "total_on_accounts": total_on_accounts,
        "accounts": accounts_data,
        "categories": cats_data,
        "over_budget": over_budget,
        "near_limit": near_limit,
        "month": month,
        "year": year,
    }


async def get_income_by_days(db: AsyncSession) -> Dict[str, Any]:
    """Доходы по дням с детализацией."""
    today = date.today()
    month, year = today.month, today.year

    result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.category))
        .where(
            Transaction.type == "Доход",
            extract("month", Transaction.date) == month,
            extract("year", Transaction.date) == year,
        )
        .order_by(Transaction.date)
    )
    txs = list(result.scalars().all())

    income_by_day: Dict[str, Dict] = {}
    for tx in txs:
        day_key = str(tx.date.day)
        if day_key not in income_by_day:
            income_by_day[day_key] = {
                "day": tx.date.day,
                "date": tx.date.isoformat(),
                "total": 0.0,
                "salary": 0.0,
                "tips": 0.0,
                "other": 0.0,
                "hours": 0.0,
                "transactions": [],
            }
        byn = tx.amount_to if (tx.currency != "BYN" and tx.amount_to) else tx.amount
        income_by_day[day_key]["total"] += byn

        cat_name = tx.category.name if tx.category else ""
        if tx.hours:
            income_by_day[day_key]["hours"] += tx.hours
        if cat_name == "Зарплата":
            income_by_day[day_key]["salary"] += byn
        elif cat_name == "Чаевые":
            income_by_day[day_key]["tips"] += byn
        else:
            income_by_day[day_key]["other"] += byn

        income_by_day[day_key]["transactions"].append({
            "id": tx.id,
            "amount": tx.amount,
            "currency": tx.currency,
            "category": cat_name,
            "comment": tx.comment or "",
            "hours": tx.hours,
        })

    return {
        "month": month,
        "year": year,
        "days": list(income_by_day.values()),
        "total_income": sum(d["total"] for d in income_by_day.values()),
        "total_hours": sum(d["hours"] for d in income_by_day.values()),
        "base_hourly_rate": config.BASE_HOURLY_RATE,
    }


async def get_weekly_summary(db: AsyncSession, days_back: int = 7) -> Dict[str, Any]:
    from datetime import timedelta
    today = date.today()
    from_date = today - timedelta(days=days_back)

    result = await db.execute(
        select(Transaction)
        .options(selectinload(Transaction.category))
        .where(Transaction.date >= from_date, Transaction.date <= today)
    )
    txs = list(result.scalars().all())

    income = sum(
        (tx.amount_to if (tx.currency != "BYN" and tx.amount_to) else tx.amount)
        for tx in txs if tx.type == "Доход"
    )
    expense = sum(
        (tx.amount_to if (tx.currency != "BYN" and tx.amount_to) else tx.amount)
        for tx in txs if tx.type == "Расход"
    )
    by_category: Dict[str, float] = {}
    for tx in txs:
        if tx.type == "Расход":
            cat_name = tx.category.name if tx.category else "Другое"
            by_category[cat_name] = by_category.get(cat_name, 0.0) + (
                tx.amount_to if (tx.currency != "BYN" and tx.amount_to) else tx.amount
            )

    return {
        "from_date": from_date.isoformat(),
        "to_date": today.isoformat(),
        "days_back": days_back,
        "total_income": income,
        "total_expense": expense,
        "balance": income - expense,
        "expense_by_category": by_category,
        "transaction_count": len(txs),
    }


def _tx_to_dict(tx: Transaction) -> Dict[str, Any]:
    tx_date = tx.date
    return {
        "id": tx.id,
        "date": tx_date.isoformat(),
        "day": tx_date.day,
        "full_date": tx_date.strftime("%d.%m.%Y"),
        "type": tx.type,
        "account": tx.account.name if tx.account else "",
        "category": tx.category.name if tx.category else "",
        "amount": tx.amount,
        "to_account": tx.to_account.name if tx.to_account else "",
        "comment": tx.comment or "",
        "hours": tx.hours,
        "exchange_rate": tx.exchange_rate,
        "amount_to": tx.amount_to,
        "currency": tx.currency,
        "created_at": tx.created_at.isoformat() if tx.created_at else "",
    }

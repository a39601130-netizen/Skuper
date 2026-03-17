"""Bidirectional sync service: PostgreSQL <-> Google Sheets."""

import asyncio
import logging
from datetime import date
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import config
from db.database import async_session
from db.models import Account, Category, Transaction
from services.sheets import get_sheets_service, safe_float, safe_int

logger = logging.getLogger(__name__)


def _get_sheets():
    """Get Google Sheets service, return None if unavailable."""
    try:
        return get_sheets_service()
    except Exception as e:
        logger.warning(f"Google Sheets unavailable: {e}")
        return None


# ============================================
# PG → Sheets (after Mini App creates/deletes)
# ============================================

def sync_transaction_to_sheets(
    tx=None,
    *,
    tx_id: int = None,
    tx_date: date = None,
    tx_type: str = "",
    account_name: str = "",
    category_name: str = "",
    amount: float = 0,
    to_account_name: str = "",
    comment: str = "",
    hours: float = None,
    exchange_rate: float = None,
    amount_to: float = None,
    currency: str = "BYN",
) -> bool:
    """
    Write a transaction to Google Sheets.
    Accepts either ORM Transaction object OR explicit kwargs.
    """
    # Extract data from ORM object if provided
    if tx is not None:
        tx_id = tx.id
        tx_date = tx.date
        tx_type = tx.type
        amount = tx.amount
        comment = tx.comment or ""
        hours = tx.hours
        exchange_rate = tx.exchange_rate
        amount_to = tx.amount_to
        currency = tx.currency or "BYN"
        try:
            account_name = tx.account.name if tx.account else ""
        except Exception:
            account_name = ""
        try:
            category_name = tx.category.name if tx.category else ""
        except Exception:
            category_name = ""
        try:
            to_account_name = tx.to_account.name if tx.to_account else ""
        except Exception:
            to_account_name = ""

    sheets = _get_sheets()
    if not sheets:
        return False

    try:
        sheets._ensure_connection()
        sheet = sheets.spreadsheet.worksheet(config.SHEET_TRANSACTIONS)

        # Get current month/year from sheet settings
        settings = sheets.get_current_month_settings()
        sheet_month = settings["month"]
        sheet_year = settings["year"]

        # Only sync if transaction is for the current sheet month
        if tx_date.month != sheet_month or tx_date.year != sheet_year:
            logger.info(
                f"Skip sync: tx date {tx_date} != sheet period {sheet_month}/{sheet_year}"
            )
            return False

        # Row: A=day, B=type, C=account, D=category, E=amount,
        #      F=to_account, G=comment, H=formula, I=hours, J=formula,
        #      K=rate, L=amount_to, M=currency, N=pg_id
        row_data = [
            tx_date.day,
            tx_type,
            account_name,
            category_name,
            amount,
            to_account_name,
            comment,
            "",  # H: will be overwritten by formula
            hours if hours else "",
            "",  # J: formula
            exchange_rate if exchange_rate else "",
            amount_to if amount_to else "",
            currency,
            tx_id,  # N: PG transaction ID
        ]

        sheet.append_row(row_data, value_input_option="USER_ENTERED")

        # Add formulas to H and J for the new row
        last_row = len(sheet.get_all_values())
        h_formula = f'=IF(A{last_row}="";"";DATE($E$1;$C$1;A{last_row}))'
        j_formula = f'=IF(I{last_row}="";"";I{last_row}*6,5)'
        sheet.update(f"H{last_row}", [[h_formula]], value_input_option="USER_ENTERED")
        sheet.update(f"J{last_row}", [[j_formula]], value_input_option="USER_ENTERED")

        logger.info(f"Synced tx #{tx_id} to Sheets row {last_row}")
        return True

    except Exception as e:
        logger.error(f"Failed to sync tx #{tx_id} to Sheets: {e}")
        return False


def delete_transaction_from_sheets(tx_id: int) -> bool:
    """Delete a transaction from Sheets by PG ID (column N)."""
    sheets = _get_sheets()
    if not sheets:
        return False

    try:
        sheets._ensure_connection()
        sheet = sheets.spreadsheet.worksheet(config.SHEET_TRANSACTIONS)
        all_vals = sheet.get_all_values()

        # Find row with matching PG ID in column N (index 13)
        for i, row in enumerate(all_vals[3:], start=4):  # Skip headers
            pg_id = row[13] if len(row) > 13 else ""
            if str(pg_id).strip() == str(tx_id):
                sheet.delete_rows(i)
                logger.info(f"Deleted tx #{tx_id} from Sheets row {i}")
                return True

        logger.info(f"Tx #{tx_id} not found in Sheets (may not be synced)")
        return False

    except Exception as e:
        logger.error(f"Failed to delete tx #{tx_id} from Sheets: {e}")
        return False


# ============================================
# Sheets → PG (periodic import)
# ============================================

async def sync_sheets_to_pg() -> dict:
    """
    Import new/changed transactions from Sheets to PG.
    Returns stats: {imported: N, skipped: N, errors: N}
    """
    sheets = _get_sheets()
    if not sheets:
        return {"imported": 0, "skipped": 0, "errors": 0, "error": "Sheets unavailable"}

    stats = {"imported": 0, "skipped": 0, "errors": 0}

    try:
        sheets._ensure_connection()
        sheet = sheets.spreadsheet.worksheet(config.SHEET_TRANSACTIONS)
        all_vals = sheet.get_all_values()

        # Get month/year from settings
        settings = sheets.get_current_month_settings()
        sheet_month = settings["month"]
        sheet_year = settings["year"]

        # Collect existing PG IDs from column N
        existing_pg_ids = set()
        rows_without_pg_id = []

        for i, row in enumerate(all_vals[3:], start=4):
            if not row[0] or not row[0].strip():
                continue  # Empty row

            pg_id = row[13] if len(row) > 13 else ""
            if pg_id and str(pg_id).strip():
                existing_pg_ids.add(str(pg_id).strip())
            else:
                rows_without_pg_id.append((i, row))

        if not rows_without_pg_id:
            logger.info("Sheets→PG sync: no new rows to import")
            return stats

        logger.info(f"Sheets→PG sync: {len(rows_without_pg_id)} rows to check")

        async with async_session() as db:
            # Get account/category maps
            acc_result = await db.execute(select(Account))
            accounts = {a.name: a for a in acc_result.scalars().all()}

            cat_result = await db.execute(select(Category))
            categories = {}
            for c in cat_result.scalars().all():
                categories[(c.name, c.type)] = c

            # Get existing transactions for this month to check for duplicates
            first_day = date(sheet_year, sheet_month, 1)
            import calendar
            last_day = date(
                sheet_year, sheet_month,
                calendar.monthrange(sheet_year, sheet_month)[1]
            )
            existing_result = await db.execute(
                select(Transaction).where(
                    Transaction.date >= first_day,
                    Transaction.date <= last_day,
                )
            )
            existing_txs = list(existing_result.scalars().all())

            # Build a set of (date, type, account_id, amount) for dedup
            existing_keys = set()
            for tx in existing_txs:
                existing_keys.add(
                    (tx.date, tx.type, tx.account_id, round(tx.amount, 2))
                )

            rows_to_update_pg_id = []

            for row_num, row in rows_without_pg_id:
                try:
                    day = safe_int(row[0])
                    if not day or day < 1 or day > 31:
                        stats["skipped"] += 1
                        continue

                    trans_type = row[1].strip() if row[1] else ""
                    if not trans_type:
                        stats["skipped"] += 1
                        continue

                    acc_name = row[2].strip() if row[2] else ""
                    account = accounts.get(acc_name)
                    if not account:
                        logger.warning(f"Row {row_num}: unknown account '{acc_name}'")
                        stats["errors"] += 1
                        continue

                    cat_name = row[3].strip() if len(row) > 3 and row[3] else ""
                    amount = safe_float(row[4])
                    if amount <= 0:
                        stats["skipped"] += 1
                        continue

                    tx_date = date(sheet_year, sheet_month, min(day, 28))
                    try:
                        tx_date = date(sheet_year, sheet_month, day)
                    except ValueError:
                        pass

                    # Check for duplicates
                    key = (tx_date, trans_type, account.id, round(amount, 2))
                    if key in existing_keys:
                        stats["skipped"] += 1
                        continue

                    # Resolve category
                    category_id = None
                    if cat_name:
                        cat_type = "Доход" if trans_type == "Доход" else "Расход"
                        cat = categories.get((cat_name, cat_type))
                        if cat:
                            category_id = cat.id

                    # Resolve to_account
                    to_acc_name = row[5].strip() if len(row) > 5 and row[5] else ""
                    to_account_id = None
                    if to_acc_name:
                        to_acc = accounts.get(to_acc_name)
                        if to_acc:
                            to_account_id = to_acc.id

                    comment = row[6].strip() if len(row) > 6 and row[6] else None
                    hours = safe_float(row[8]) if len(row) > 8 and row[8] else None
                    exchange_rate = safe_float(row[10]) if len(row) > 10 and row[10] else None
                    amount_to = safe_float(row[11]) if len(row) > 11 and row[11] else None
                    currency = row[12].strip() if len(row) > 12 and row[12] else "BYN"

                    tx = Transaction(
                        date=tx_date,
                        type=trans_type,
                        account_id=account.id,
                        category_id=category_id,
                        amount=amount,
                        to_account_id=to_account_id,
                        comment=comment,
                        hours=hours if hours else None,
                        exchange_rate=exchange_rate if exchange_rate else None,
                        amount_to=amount_to if amount_to else None,
                        currency=currency,
                        synced_to_sheets=True,
                    )
                    db.add(tx)
                    await db.flush()  # Get the ID

                    existing_keys.add(key)
                    rows_to_update_pg_id.append((row_num, tx.id))
                    stats["imported"] += 1

                except Exception as e:
                    logger.error(f"Row {row_num} import error: {e}")
                    stats["errors"] += 1

            await db.commit()

        # Write PG IDs back to Sheets column N
        if rows_to_update_pg_id:
            for row_num, pg_id in rows_to_update_pg_id:
                try:
                    sheet.update_cell(row_num, 14, pg_id)  # Column N = 14
                except Exception as e:
                    logger.error(f"Failed to write PG ID to Sheets row {row_num}: {e}")

        logger.info(
            f"Sheets→PG sync done: imported={stats['imported']}, "
            f"skipped={stats['skipped']}, errors={stats['errors']}"
        )
        return stats

    except Exception as e:
        logger.error(f"Sheets→PG sync failed: {e}")
        stats["error"] = str(e)
        return stats


# ============================================
# Full bidirectional sync
# ============================================

async def full_sync() -> dict:
    """
    Run full bidirectional sync:
    1. PG → Sheets: mark unsynced PG transactions, write to Sheets
    2. Sheets → PG: import new Sheets rows to PG
    """
    result = {"pg_to_sheets": 0, "sheets_to_pg": 0, "errors": []}

    sheets = _get_sheets()
    if not sheets:
        result["errors"].append("Sheets unavailable")
        return result

    try:
        # Step 1: PG → Sheets (find transactions not yet in Sheets)
        sheets._ensure_connection()
        sheet = sheets.spreadsheet.worksheet(config.SHEET_TRANSACTIONS)
        all_vals = sheet.get_all_values()
        settings = sheets.get_current_month_settings()
        sheet_month = settings["month"]
        sheet_year = settings["year"]

        # Get PG IDs already in Sheets
        sheets_pg_ids = set()
        for row in all_vals[3:]:
            pg_id = row[13] if len(row) > 13 else ""
            if pg_id and str(pg_id).strip():
                sheets_pg_ids.add(int(pg_id))

        # Get PG transactions for this month
        import calendar
        first_day = date(sheet_year, sheet_month, 1)
        last_day = date(
            sheet_year, sheet_month,
            calendar.monthrange(sheet_year, sheet_month)[1]
        )

        async with async_session() as db:
            pg_result = await db.execute(
                select(Transaction)
                .where(
                    Transaction.date >= first_day,
                    Transaction.date <= last_day,
                )
                .options(
                    selectinload(Transaction.account),
                    selectinload(Transaction.category),
                    selectinload(Transaction.to_account),
                )
            )
            pg_txs = list(pg_result.scalars().all())

        # Find PG transactions not in Sheets
        for tx in pg_txs:
            if tx.id not in sheets_pg_ids:
                success = sync_transaction_to_sheets(
                    tx_id=tx.id,
                    tx_date=tx.date,
                    tx_type=tx.type,
                    account_name=tx.account.name if tx.account else "",
                    category_name=tx.category.name if tx.category else "",
                    amount=tx.amount,
                    to_account_name=tx.to_account.name if tx.to_account else "",
                    comment=tx.comment or "",
                    hours=tx.hours,
                    exchange_rate=tx.exchange_rate,
                    amount_to=tx.amount_to,
                    currency=tx.currency or "BYN",
                )
                if success:
                    result["pg_to_sheets"] += 1

        # Step 2: Sheets → PG
        sheets_result = await sync_sheets_to_pg()
        result["sheets_to_pg"] = sheets_result.get("imported", 0)
        if "error" in sheets_result:
            result["errors"].append(sheets_result["error"])

    except Exception as e:
        logger.error(f"Full sync failed: {e}")
        result["errors"].append(str(e))

    return result


# ============================================
# Background sync task
# ============================================

async def periodic_sync_task(interval_minutes: int = 5):
    """Background task that syncs Sheets → PG periodically."""
    logger.info(f"Periodic sync task started (every {interval_minutes}min)")
    while True:
        await asyncio.sleep(interval_minutes * 60)
        try:
            result = await sync_sheets_to_pg()
            if result.get("imported", 0) > 0:
                logger.info(f"Periodic sync: imported {result['imported']} transactions")
        except Exception as e:
            logger.error(f"Periodic sync error: {e}")

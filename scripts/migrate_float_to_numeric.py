"""
Migration: Float -> Numeric(12,2) for monetary fields.
Run once after deploying the updated models.

Usage: python scripts/migrate_float_to_numeric.py
"""
import asyncio
import logging
from sqlalchemy import text
from db.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MIGRATIONS = [
    # accounts
    "ALTER TABLE accounts ALTER COLUMN balance TYPE NUMERIC(12,2)",
    "ALTER TABLE accounts ALTER COLUMN initial_balance TYPE NUMERIC(12,2)",
    # categories
    "ALTER TABLE categories ALTER COLUMN budget_limit TYPE NUMERIC(12,2)",
    # transactions
    "ALTER TABLE transactions ALTER COLUMN amount TYPE NUMERIC(12,2)",
    "ALTER TABLE transactions ALTER COLUMN exchange_rate TYPE NUMERIC(12,6)",
    "ALTER TABLE transactions ALTER COLUMN amount_to TYPE NUMERIC(12,2)",
    # recurring_transactions
    "ALTER TABLE recurring_transactions ALTER COLUMN amount TYPE NUMERIC(12,2)",
]


async def migrate():
    async with engine.begin() as conn:
        for sql in MIGRATIONS:
            try:
                await conn.execute(text(sql))
                logger.info(f"OK: {sql}")
            except Exception as e:
                logger.warning(f"SKIP: {sql} -- {e}")
    logger.info("Migration complete.")


if __name__ == "__main__":
    asyncio.run(migrate())

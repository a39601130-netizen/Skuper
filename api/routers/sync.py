"""API роутер: синхронизация PG <-> Google Sheets."""

import logging

from fastapi import APIRouter, Depends

from api.deps import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/sync", tags=["sync"])


@router.post("")
async def trigger_sync(user: dict = Depends(get_current_user)):
    """Trigger full bidirectional sync PG <-> Google Sheets."""
    from services.sync import full_sync
    result = await full_sync()
    return result


@router.post("/sheets-to-pg")
async def trigger_sheets_to_pg(user: dict = Depends(get_current_user)):
    """Import new transactions from Google Sheets to PG."""
    from services.sync import sync_sheets_to_pg
    result = await sync_sheets_to_pg()
    return result

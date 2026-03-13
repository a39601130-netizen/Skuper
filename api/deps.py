"""FastAPI dependencies: auth, database session, AI service."""

from fastapi import Header, HTTPException
from config import TELEGRAM_USER_ID
from api.auth import validate_init_data
from services.ai_advisor import get_advisor


def get_current_user(
    x_telegram_init_data: str = Header(default=""),
) -> dict:
    """Validate Telegram initData and return user dict."""
    user_data = validate_init_data(x_telegram_init_data)
    if not user_data:
        raise HTTPException(status_code=401, detail="Invalid init data")

    telegram_id = user_data.get("id")
    if not telegram_id:
        raise HTTPException(status_code=401, detail="No user ID in init data")

    if TELEGRAM_USER_ID and str(telegram_id) != str(TELEGRAM_USER_ID):
        raise HTTPException(status_code=403, detail="Access denied")

    return user_data


def get_ai():
    return get_advisor()

"""Telegram Mini App initData validation (HMAC-SHA256)."""

import hashlib
import hmac
import json
import logging
import time
from urllib.parse import parse_qs, unquote

from config import TELEGRAM_BOT_TOKEN

AUTH_EXPIRE_SECONDS = 7200  # 2 hours

logger = logging.getLogger(__name__)


def validate_init_data(init_data: str) -> dict | None:
    """Validate Telegram Mini App initData. Returns user data dict or None."""
    if not TELEGRAM_BOT_TOKEN or not init_data:
        logger.warning("Auth failed: token=%s, init_data_len=%d",
                       bool(TELEGRAM_BOT_TOKEN), len(init_data) if init_data else 0)
        return None

    try:
        parsed = parse_qs(init_data, keep_blank_values=True)
        received_hash = parsed.get("hash", [None])[0]
        if not received_hash:
            logger.warning("Auth failed: no hash in init_data")
            return None

        pairs = []
        for key, values in parsed.items():
            if key == "hash":
                continue
            pairs.append(f"{key}={unquote(values[0])}")
        pairs.sort()
        data_check_string = "\n".join(pairs)

        secret_key = hmac.new(
            b"WebAppData", TELEGRAM_BOT_TOKEN.encode(), hashlib.sha256
        ).digest()

        calculated_hash = hmac.new(
            secret_key, data_check_string.encode(), hashlib.sha256
        ).hexdigest()

        if not hmac.compare_digest(calculated_hash, received_hash):
            logger.warning("Auth failed: hash mismatch. Keys in init_data: %s",
                           list(parsed.keys()))
            return None

        auth_date = parsed.get("auth_date", [None])[0]
        if auth_date and (time.time() - int(auth_date)) > AUTH_EXPIRE_SECONDS:
            logger.warning("Auth failed: expired auth_date=%s", auth_date)
            return None

        user_str = parsed.get("user", [None])[0]
        if user_str:
            return json.loads(unquote(user_str))

        logger.warning("Auth failed: no user in init_data")
        return None
    except Exception as e:
        logger.exception("Auth failed with exception: %s", e)
        return None

"""
Вспомогательные функции для работы с Telegram API
"""
from telegram.error import BadRequest


async def safe_edit_message(query, text: str, **kwargs):
    """Редактирует сообщение, игнорируя ошибку 'message is not modified'"""
    try:
        await query.edit_message_text(text, **kwargs)
    except BadRequest as e:
        if "message is not modified" not in str(e).lower():
            raise

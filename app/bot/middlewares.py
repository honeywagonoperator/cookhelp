import logging
import traceback

from aiogram import BaseMiddleware
from aiogram.types import Message, Update

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data: dict):
        if event.message:
            user = event.message.from_user
            logger.info(
                "Message from %s (%s): %s",
                user.full_name,
                user.id,
                event.message.text or "[non-text]",
            )
        return await handler(event, data)


class ErrorHandlingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Update, data: dict):
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(
                "Unhandled error: %s\n%s",
                e,
                traceback.format_exc(),
            )
            if event.message:
                await event.message.answer(
                    "❌ Произошла ошибка. Пожалуйста, попробуйте ещё раз.",
                )
            raise

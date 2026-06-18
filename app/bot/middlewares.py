import logging
import traceback

from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery

logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        user = event.from_user
        logger.info(
            "Message from %s (%s): %s",
            user.full_name,
            user.id,
            event.text or "[non-text]",
        )
        return await handler(event, data)


class ErrorHandlingMiddleware(BaseMiddleware):
    async def __call__(self, handler, event: Message, data: dict):
        try:
            return await handler(event, data)
        except Exception as e:
            logger.error(
                "Unhandled error: %s\n%s",
                e,
                traceback.format_exc(),
            )
            await event.answer(
                "❌ Произошла ошибка. Пожалуйста, попробуйте ещё раз.",
            )

import logging

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery, Message

from app.bot.keyboards import main_menu

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
    async def __call__(self, handler, event: Message | CallbackQuery, data: dict):
        try:
            return await handler(event, data)
        except Exception as e:
            user = event.from_user
            logger.exception("Unhandled error from user %s (%s): %s", user.full_name, user.id, e)

            text = "❌ Произошла ошибка. Пожалуйста, попробуйте ещё раз."
            if isinstance(event, CallbackQuery):
                await event.answer(text, show_alert=True)
            else:
                await event.answer(text, reply_markup=main_menu)

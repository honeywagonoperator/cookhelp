import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.core.config import settings

from .handlers import start, create_recipe, search, free_input, recipe_actions
from .middlewares import LoggingMiddleware, ErrorHandlingMiddleware

logger = logging.getLogger(__name__)

bot = Bot(
    token=settings.bot_token,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)

dp = Dispatcher()
dp.include_router(start.router)
dp.include_router(create_recipe.router)
dp.include_router(search.router)
dp.include_router(free_input.router)
dp.include_router(recipe_actions.router)

dp.message.middleware(LoggingMiddleware())
dp.message.middleware(ErrorHandlingMiddleware())


async def start_bot() -> None:
    if settings.bot_use_webhook:
        webhook_url = f"{settings.bot_webhook_url}/webhook"
        await bot.set_webhook(webhook_url)
        logger.info("Webhook set to %s", webhook_url)
    else:
        await bot.delete_webhook(drop_pending_updates=True)
        logger.info("Starting polling")


async def stop_bot() -> None:
    if settings.bot_use_webhook:
        await bot.delete_webhook()
    await bot.session.close()
    logger.info("Bot stopped")

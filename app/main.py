import asyncio
import logging
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.database.connection import close_db, init_db

logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting application...")
    try:
        await init_db()
        logger.info("Database initialized")

        from app.bot import bot, dp, start_bot, stop_bot

        await start_bot()
        logger.info("Bot started")

        polling_task = None
        if not settings.bot_use_webhook:
            polling_task = asyncio.create_task(dp.start_polling(bot))
            logger.info("Polling started")

        yield
    except Exception as e:
        logger.exception("Failed to start application: %s", e)
        yield
        return

    if polling_task:
        polling_task.cancel()
        try:
            await polling_task
        except asyncio.CancelledError:
            pass

    await stop_bot()
    logger.info("Bot stopped")
    await close_db()
    logger.info("Database connections closed")


app = FastAPI(
    title="CookHelp API",
    description="Personal recipe management Telegram bot with AI",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health")
async def health_check() -> JSONResponse:
    return JSONResponse({"status": "ok"})


@app.get("/health/db")
async def db_health_check() -> JSONResponse:
    from app.database.connection import engine
    from sqlalchemy import text

    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return JSONResponse({"status": "ok", "database": "connected"})
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return JSONResponse(
            {"status": "error", "database": "disconnected", "error": str(e)},
            status_code=503,
        )


@app.get("/health/ai")
async def ai_health_check() -> JSONResponse:
    try:
        from app.ai.client import get_ai_client
        client = get_ai_client()
        await client.create_embedding("test")
        return JSONResponse({"status": "ok", "ai": "connected"})
    except Exception as e:
        logger.exception("AI health check failed")
        return JSONResponse(
            {"status": "error", "ai": "disconnected", "error": str(e)},
            status_code=503,
        )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.environment == "development",
    )

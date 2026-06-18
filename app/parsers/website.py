import asyncio
import logging
from typing import Any

import trafilatura

from app.ai.service import AIService, get_ai_service
from app.database.connection import async_session_maker
from app.repositories.recipe import RecipeRepository
from app.services.recipe import RecipeService

logger = logging.getLogger(__name__)


class WebsiteParser:
    async def get_content(self, url: str) -> str:
        downloaded = await asyncio.to_thread(trafilatura.fetch_url, url)
        if not downloaded:
            raise ValueError(f"Failed to fetch URL: {url}")

        text = await asyncio.to_thread(
            trafilatura.extract,
            downloaded,
            include_links=False,
            include_images=False,
            include_tables=False,
            output_format="txt",
        )

        if not text or len(text.strip()) < 50:
            raise ValueError(f"Could not extract meaningful content from {url}")

        logger.info("Content extracted from URL", extra={"url": url, "length": len(text)})
        return text


async def process_url_recipe(url: str) -> dict[str, Any]:
    parser = WebsiteParser()
    ai = get_ai_service()
    raw_text = await parser.get_content(url)

    recipe_create = await ai.extract_recipe(raw_text)
    recipe_dict = recipe_create.model_dump()
    normalized = await ai.normalize_recipe(recipe_dict)

    async with async_session_maker() as session:
        repository = RecipeRepository(session)
        service = RecipeService(repository, ai)
        recipe = await service.create_recipe(normalized)
        await session.commit()

    logger.info("Recipe saved from URL", extra={"recipe_id": str(recipe.id), "title": recipe.title})

    return {
        "success": True,
        "recipe": recipe,
        "message": f"Рецепт «{recipe.title}» успешно добавлен!",
    }

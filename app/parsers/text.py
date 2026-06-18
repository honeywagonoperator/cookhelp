import logging
from typing import Any

from app.ai.service import get_ai_service
from app.repositories.recipe import RecipeRepository
from app.schemas.recipe import RecipeCreate
from app.services.recipe import RecipeService

logger = logging.getLogger(__name__)


class TextRecipeParser:
    def __init__(self, recipe_service: RecipeService):
        self.recipe_service = recipe_service
        self.ai_service = get_ai_service()

    async def parse_and_save(self, text: str, user_id: int) -> dict[str, Any]:
        logger.info("Parsing recipe from text", extra={"user_id": user_id, "text_length": len(text)})

        recipe_create = await self.ai_service.extract_recipe(text)
        logger.info("Recipe extracted", extra={"title": recipe_create.title})

        recipe_dict = recipe_create.model_dump()
        normalized = await self.ai_service.normalize_recipe(recipe_dict)
        logger.info("Recipe normalized", extra={"title": normalized.title})

        recipe = await self.recipe_service.create_recipe(normalized)
        logger.info("Recipe saved", extra={"recipe_id": str(recipe.id), "title": recipe.title})

        return {
            "success": True,
            "recipe": recipe,
            "message": f"Рецепт «{recipe.title}» успешно сохранён!",
        }

    async def parse_only(self, text: str) -> RecipeCreate:
        recipe_create = await self.ai_service.extract_recipe(text)
        normalized = await self.ai_service.normalize_recipe(recipe_create.model_dump())
        return normalized


async def process_text_recipe(text: str) -> dict[str, Any]:
    from app.ai.service import AIService
    from app.database.connection import async_session_maker

    ai_service = AIService()
    async with async_session_maker() as session:
        repository = RecipeRepository(session)
        service = RecipeService(repository, ai_service)
        parser = TextRecipeParser(service)
        result = await parser.parse_and_save(text, 0)
        await session.commit()
        return result

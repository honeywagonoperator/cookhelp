import logging
from typing import Sequence

from app.ai.service import AIService
from app.repositories.recipe import RecipeRepository
from app.schemas.recipe import RecipeResponse

logger = logging.getLogger(__name__)


class SearchService:
    def __init__(self, repository: RecipeRepository, ai_service: AIService):
        self.repository = repository
        self.ai_service = ai_service

    async def search(self, query: str, limit: int = 10) -> list[RecipeResponse]:
        embedding = await self.ai_service.generate_embedding(query)
        recipes = await self.repository.search_by_embedding(embedding, limit)

        if not recipes:
            return []

        return [self._to_response(r) for r in recipes]

    def _to_response(self, recipe) -> RecipeResponse:
        return RecipeResponse(
            id=recipe.id,
            title=recipe.title,
            description=recipe.description,
            ingredients=recipe.ingredients,
            steps=recipe.steps,
            tags=recipe.tags,
            source=recipe.source,
            embedding=recipe.embedding,
            created_at=recipe.created_at.isoformat(),
            updated_at=recipe.updated_at.isoformat(),
        )

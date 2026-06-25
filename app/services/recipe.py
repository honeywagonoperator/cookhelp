import logging
from math import ceil
from typing import Sequence
from uuid import UUID

from app.ai.service import AIService, get_ai_service
from app.models.recipe import Recipe
from app.repositories.recipe import RecipeRepository
from app.schemas.recipe import (
    PaginatedRecipes,
    RecipeCreate,
    RecipeResponse,
    RecipeUpdate,
)
from app.services.mapper import RecipeMapper

logger = logging.getLogger(__name__)


class RecipeService:
    def __init__(self, repository: RecipeRepository, ai_service: AIService | None = None):
        self.repository = repository
        self.ai_service = ai_service

    async def create_recipe(self, data: RecipeCreate) -> RecipeResponse:
        recipe_dict = data.model_dump()

        if self.ai_service:
            tags = await self.ai_service.generate_tags(recipe_dict)
            if tags:
                data.tags = tags
                recipe_dict["tags"] = tags

            embedding = await self.ai_service.generate_embedding_for_recipe(recipe_dict)
            data.embedding = embedding

        recipe = await self.repository.create(
            title=data.title,
            description=data.description,
            ingredients=data.ingredients,
            steps=data.steps,
            tags=data.tags,
            source=data.source.model_dump(),
            embedding=data.embedding,
        )
        return RecipeMapper.to_response(recipe)

    async def get_recipe(self, recipe_id: UUID) -> RecipeResponse | None:
        recipe = await self.repository.get_by_id(recipe_id)
        if not recipe:
            return None
        return RecipeMapper.to_response(recipe)

    async def list_recipes(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedRecipes:
        offset = (page - 1) * page_size
        recipes = await self.repository.get_all(limit=page_size, offset=offset)
        total = await self.repository.count()

        return PaginatedRecipes(
            items=[RecipeMapper.to_response(r) for r in recipes],
            total=total,
            page=page,
            page_size=page_size,
            total_pages=ceil(total / page_size) if total > 0 else 0,
        )

    async def update_recipe(
        self,
        recipe_id: UUID,
        data: RecipeUpdate,
    ) -> RecipeResponse | None:
        update_data = data.model_dump(exclude_unset=True)
        source = update_data.pop("source", None)
        if source:
            update_data["source"] = source.model_dump()

        if self.ai_service and update_data:
            recipe_dict = update_data.copy()
            embedding = await self.ai_service.generate_embedding_for_recipe(recipe_dict)
            update_data["embedding"] = embedding

            tags = await self.ai_service.generate_tags(recipe_dict)
            if tags:
                update_data["tags"] = tags

        recipe = await self.repository.update(recipe_id, **update_data)
        if not recipe:
            return None
        return RecipeMapper.to_response(recipe)

    async def delete_recipe(self, recipe_id: UUID) -> bool:
        return await self.repository.delete(recipe_id)

    async def search_by_embedding(
        self,
        embedding: list[float],
        limit: int = 10,
    ) -> list[RecipeResponse]:
        recipes = await self.repository.search_by_embedding(embedding, limit)
        return [RecipeMapper.to_response(r) for r in recipes]

    async def search(self, query: str, limit: int = 10) -> list[RecipeResponse]:
        ai = self.ai_service or get_ai_service()
        embedding = await ai.generate_embedding(query)
        return await self.search_by_embedding(embedding, limit)

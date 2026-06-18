from typing import Sequence
from uuid import UUID
from math import ceil

from app.repositories.recipe import RecipeRepository
from app.schemas.recipe import (
    RecipeCreate,
    RecipeUpdate,
    RecipeResponse,
    PaginatedRecipes,
)
from app.models.recipe import Recipe


class RecipeService:
    def __init__(self, repository: RecipeRepository):
        self.repository = repository

    async def create_recipe(self, data: RecipeCreate) -> RecipeResponse:
        recipe = await self.repository.create(
            title=data.title,
            description=data.description,
            ingredients=data.ingredients,
            steps=data.steps,
            tags=data.tags,
            source=data.source.model_dump(),
            embedding=data.embedding,
        )
        return self._to_response(recipe)

    async def get_recipe(self, recipe_id: UUID) -> RecipeResponse | None:
        recipe = await self.repository.get_by_id(recipe_id)
        if not recipe:
            return None
        return self._to_response(recipe)

    async def list_recipes(
        self,
        page: int = 1,
        page_size: int = 20,
    ) -> PaginatedRecipes:
        offset = (page - 1) * page_size
        recipes = await self.repository.get_all(limit=page_size, offset=offset)
        total = await self.repository.count()

        return PaginatedRecipes(
            items=[self._to_response(r) for r in recipes],
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

        recipe = await self.repository.update(recipe_id, **update_data)
        if not recipe:
            return None
        return self._to_response(recipe)

    async def delete_recipe(self, recipe_id: UUID) -> bool:
        return await self.repository.delete(recipe_id)

    async def search_by_embedding(
        self,
        embedding: list[float],
        limit: int = 10,
    ) -> list[RecipeResponse]:
        recipes = await self.repository.search_by_embedding(embedding, limit)
        return [self._to_response(r) for r in recipes]

    def _to_response(self, recipe: Recipe) -> RecipeResponse:
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
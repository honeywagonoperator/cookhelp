from typing import Sequence
from uuid import UUID

from pgvector.sqlalchemy import Vector
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.dialects.postgresql import JSONB

from app.models.recipe import Recipe


class RecipeRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(
        self,
        title: str,
        description: str | None,
        ingredients: list[str],
        steps: list[str],
        tags: list[str],
        source: dict,
        embedding: list[float] | None = None,
    ) -> Recipe:
        recipe = Recipe(
            title=title,
            description=description,
            ingredients=ingredients,
            steps=steps,
            tags=tags,
            source=source,
            embedding=embedding,
        )
        self.session.add(recipe)
        await self.session.flush()
        await self.session.refresh(recipe)
        return recipe

    async def get_by_id(self, recipe_id: UUID) -> Recipe | None:
        result = await self.session.execute(
            select(Recipe).where(Recipe.id == recipe_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, limit: int = 50, offset: int = 0) -> Sequence[Recipe]:
        result = await self.session.execute(
            select(Recipe)
            .order_by(Recipe.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    async def update(
        self,
        recipe_id: UUID,
        title: str | None = None,
        description: str | None = None,
        ingredients: list[str] | None = None,
        steps: list[str] | None = None,
        tags: list[str] | None = None,
        source: dict | None = None,
        embedding: list[float] | None = None,
    ) -> Recipe | None:
        recipe = await self.get_by_id(recipe_id)
        if not recipe:
            return None

        if title is not None:
            recipe.title = title
        if description is not None:
            recipe.description = description
        if ingredients is not None:
            recipe.ingredients = ingredients
        if steps is not None:
            recipe.steps = steps
        if tags is not None:
            recipe.tags = tags
        if source is not None:
            recipe.source = source
        if embedding is not None:
            recipe.embedding = embedding

        await self.session.flush()
        await self.session.refresh(recipe)
        return recipe

    async def delete(self, recipe_id: UUID) -> bool:
        recipe = await self.get_by_id(recipe_id)
        if not recipe:
            return False
        await self.session.delete(recipe)
        await self.session.flush()
        return True

    async def search_by_embedding(
        self,
        embedding: list[float],
        limit: int = 10,
    ) -> Sequence[Recipe]:
        result = await self.session.execute(
            select(Recipe)
            .where(Recipe.embedding.is_not(None))
            .order_by(Recipe.embedding.cosine_distance(embedding))
            .limit(limit)
        )
        return result.scalars().all()

    async def count(self) -> int:
        result = await self.session.execute(select(func.count(Recipe.id)))
        return result.scalar_one()
from unittest.mock import AsyncMock
from uuid import UUID

import pytest

from app.schemas.recipe import (
    PaginatedRecipes,
    RecipeCreate,
    RecipeUpdate,
)
from app.services.recipe import RecipeService


@pytest.fixture
def recipe_service(mock_repository: AsyncMock) -> RecipeService:
    return RecipeService(mock_repository)


class TestRecipeService:
    async def test_create_recipe(
        self,
        recipe_service: RecipeService,
        mock_repository: AsyncMock,
        sample_recipe_create: RecipeCreate,
    ):
        mock_repository.create.return_value = _mock_recipe(sample_recipe_create)

        result = await recipe_service.create_recipe(sample_recipe_create)

        assert result.title == "Борщ"
        mock_repository.create.assert_awaited_once()

    async def test_create_recipe_with_ai(
        self,
        mock_repository: AsyncMock,
        sample_recipe_create: RecipeCreate,
        mock_ai_client: AsyncMock,
    ):
        mock_repository.create.return_value = _mock_recipe(sample_recipe_create)
        service = RecipeService(mock_repository, mock_ai_client)

        result = await service.create_recipe(sample_recipe_create)

        assert result.title == "Борщ"
        mock_repository.create.assert_awaited_once()

    async def test_get_recipe_found(
        self,
        recipe_service: RecipeService,
        mock_repository: AsyncMock,
        sample_recipe_id: UUID,
        sample_recipe_create: RecipeCreate,
    ):
        mock_repository.get_by_id.return_value = _mock_recipe(sample_recipe_create, sample_recipe_id)

        result = await recipe_service.get_recipe(sample_recipe_id)

        assert result is not None
        assert result.id == sample_recipe_id
        assert result.title == "Борщ"

    async def test_get_recipe_not_found(
        self,
        recipe_service: RecipeService,
        mock_repository: AsyncMock,
        sample_recipe_id: UUID,
    ):
        mock_repository.get_by_id.return_value = None

        result = await recipe_service.get_recipe(sample_recipe_id)

        assert result is None

    async def test_list_recipes(
        self,
        recipe_service: RecipeService,
        mock_repository: AsyncMock,
        sample_recipe_create: RecipeCreate,
    ):
        mock_recipes = [_mock_recipe(sample_recipe_create) for _ in range(3)]
        mock_repository.get_all.return_value = mock_recipes
        mock_repository.count.return_value = 10

        result = await recipe_service.list_recipes(page=1, page_size=3)

        assert isinstance(result, PaginatedRecipes)
        assert len(result.items) == 3
        assert result.total == 10
        assert result.total_pages == 4
        assert result.page == 1

    async def test_list_recipes_empty(
        self,
        recipe_service: RecipeService,
        mock_repository: AsyncMock,
    ):
        mock_repository.get_all.return_value = []
        mock_repository.count.return_value = 0

        result = await recipe_service.list_recipes()

        assert len(result.items) == 0
        assert result.total_pages == 0

    async def test_update_recipe(
        self,
        recipe_service: RecipeService,
        mock_repository: AsyncMock,
        sample_recipe_id: UUID,
        sample_recipe_create: RecipeCreate,
    ):
        updated = _mock_recipe(sample_recipe_create, sample_recipe_id)
        updated.title = "Борщ (обновлённый)"
        mock_repository.update.return_value = updated

        result = await recipe_service.update_recipe(
            sample_recipe_id,
            RecipeUpdate(title="Борщ (обновлённый)"),
        )

        assert result is not None
        assert result.title == "Борщ (обновлённый)"

    async def test_update_recipe_not_found(
        self,
        recipe_service: RecipeService,
        mock_repository: AsyncMock,
        sample_recipe_id: UUID,
    ):
        mock_repository.update.return_value = None

        result = await recipe_service.update_recipe(
            sample_recipe_id,
            RecipeUpdate(title="Новый"),
        )

        assert result is None

    async def test_delete_recipe(
        self,
        recipe_service: RecipeService,
        mock_repository: AsyncMock,
        sample_recipe_id: UUID,
    ):
        mock_repository.delete.return_value = True

        result = await recipe_service.delete_recipe(sample_recipe_id)

        assert result is True
        mock_repository.delete.assert_awaited_once_with(sample_recipe_id)

    async def test_delete_recipe_not_found(
        self,
        recipe_service: RecipeService,
        mock_repository: AsyncMock,
        sample_recipe_id: UUID,
    ):
        mock_repository.delete.return_value = False

        result = await recipe_service.delete_recipe(sample_recipe_id)

        assert result is False

    async def test_search_by_embedding(
        self,
        recipe_service: RecipeService,
        mock_repository: AsyncMock,
        sample_recipe_create: RecipeCreate,
    ):
        mock_repository.search_by_embedding.return_value = [
            _mock_recipe(sample_recipe_create) for _ in range(2)
        ]

        result = await recipe_service.search_by_embedding([0.1] * 128, limit=2)

        assert len(result) == 2
        mock_repository.search_by_embedding.assert_awaited_once()


def _mock_recipe(create_data: RecipeCreate, recipe_id: UUID | None = None) -> AsyncMock:
    from uuid import uuid4
    recipe = AsyncMock()
    recipe.id = recipe_id or uuid4()
    recipe.title = create_data.title
    recipe.description = create_data.description
    recipe.ingredients = create_data.ingredients
    recipe.steps = create_data.steps
    recipe.tags = create_data.tags
    recipe.source = create_data.source.model_dump()
    recipe.embedding = create_data.embedding
    from datetime import datetime
    recipe.created_at = datetime.now()
    recipe.updated_at = datetime.now()
    return recipe

from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.schemas.recipe import RecipeResponse
from app.services.recipe import RecipeService


@pytest.fixture
def recipe_service(mock_repository: AsyncMock) -> RecipeService:
    ai_service = MagicMock()
    ai_service.generate_embedding = AsyncMock(return_value=[0.1] * 2048)
    return RecipeService(mock_repository, ai_service)


class TestRecipeSearch:
    async def test_search_found(
        self,
        recipe_service: RecipeService,
        mock_repository: AsyncMock,
    ):
        mock_recipe = create_mock_recipe()
        mock_repository.search_by_embedding.return_value = [mock_recipe]

        result = await recipe_service.search("борщ")

        assert len(result) == 1
        assert isinstance(result[0], RecipeResponse)
        assert result[0].title == "Борщ"

    async def test_search_empty(
        self,
        recipe_service: RecipeService,
        mock_repository: AsyncMock,
    ):
        mock_repository.search_by_embedding.return_value = []

        result = await recipe_service.search("несуществующий рецепт")

        assert result == []

    async def test_search_embedding_shape(
        self,
        recipe_service: RecipeService,
        mock_repository: AsyncMock,
    ):
        await recipe_service.search("суп", limit=5)
        mock_repository.search_by_embedding.assert_called_once()
        args = mock_repository.search_by_embedding.call_args[0]
        assert len(args[0]) == 2048
        assert args[1] == 5


def create_mock_recipe() -> MagicMock:
    from datetime import datetime

    mock = MagicMock()
    mock.id = uuid4()
    mock.title = "Борщ"
    mock.description = "Суп"
    mock.ingredients = ["свекла"]
    mock.steps = ["сварить"]
    mock.tags = ["суп"]
    mock.source = {"type": "text"}
    mock.embedding = [0.1] * 2048
    mock.created_at = datetime.now()
    mock.updated_at = datetime.now()
    return mock

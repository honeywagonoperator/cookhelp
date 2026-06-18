from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.schemas.recipe import RecipeResponse
from app.services.search import SearchService


@pytest.fixture
def search_service(mock_repository: AsyncMock, mock_ai_client: AsyncMock) -> SearchService:
    ai_service = MagicMock()
    ai_service.generate_embedding = AsyncMock(return_value=[0.1] * 128)
    return SearchService(mock_repository, ai_service)


class TestSearchService:
    async def test_search_found(
        self,
        search_service: SearchService,
        mock_repository: AsyncMock,
    ):
        mock_recipe = MagicMock()
        mock_recipe.id = uuid4()
        mock_recipe.title = "Борщ"
        mock_recipe.description = "Суп"
        mock_recipe.ingredients = ["свекла"]
        mock_recipe.steps = ["сварить"]
        mock_recipe.tags = ["суп"]
        mock_recipe.source = {"type": "text"}
        mock_recipe.embedding = [0.1] * 128
        from datetime import datetime
        mock_recipe.created_at = datetime.now()
        mock_recipe.updated_at = datetime.now()

        mock_repository.search_by_embedding.return_value = [mock_recipe]

        result = await search_service.search("борщ")

        assert len(result) == 1
        assert isinstance(result[0], RecipeResponse)
        assert result[0].title == "Борщ"

    async def test_search_empty(
        self,
        search_service: SearchService,
        mock_repository: AsyncMock,
    ):
        mock_repository.search_by_embedding.return_value = []

        result = await search_service.search("несуществующий рецепт")

        assert result == []

    async def test_search_embedding_shape(
        self,
        search_service: SearchService,
        mock_repository: AsyncMock,
    ):
        result = await search_service.search("суп", limit=5)
        mock_repository.search_by_embedding.assert_called_once()
        args = mock_repository.search_by_embedding.call_args[0]
        assert len(args[0]) == 128
        assert args[1] == 5

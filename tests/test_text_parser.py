from unittest.mock import AsyncMock, MagicMock

import pytest

from app.parsers.text import TextRecipeParser


class TestTextRecipeParser:
    @pytest.fixture
    def mock_recipe_service(self) -> AsyncMock:
        service = AsyncMock()
        service.create_recipe = AsyncMock(return_value=MagicMock(
            id="test-id",
            title="Борщ",
        ))
        return service

    @pytest.fixture
    def parser(self, mock_recipe_service: AsyncMock, mock_ai_client: AsyncMock) -> TextRecipeParser:
        return TextRecipeParser(mock_recipe_service)

    async def test_parse_and_save_success(
        self,
        parser: TextRecipeParser,
        mock_recipe_service: AsyncMock,
    ):
        result = await parser.parse_and_save("рецепт борща", user_id=123)

        assert result["success"] is True
        assert "Борщ" in result["message"]
        mock_recipe_service.create_recipe.assert_awaited_once()

    async def test_parse_and_save_failure(
        self,
        parser: TextRecipeParser,
        mock_recipe_service: AsyncMock,
        mock_ai_client,
    ):
        from unittest.mock import PropertyMock

        mock_recipe_service.create_recipe = AsyncMock(side_effect=ValueError("DB error"))
        parser.recipe_service = mock_recipe_service

        with pytest.raises(ValueError):
            await parser.parse_and_save("рецепт", user_id=1)

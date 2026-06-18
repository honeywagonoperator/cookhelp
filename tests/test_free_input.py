import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.ai.client import AIResponse
from app.schemas.recipe import RecipeSource


@pytest.fixture
def mock_ai_intent_client(mock_ai_client: AsyncMock) -> AsyncMock:
    mock_ai_client.chat_completion = AsyncMock(return_value=AIResponse(
        content=json.dumps({
            "intent": "UNKNOWN",
            "confidence": 0.0,
            "entities": {},
        }),
        tokens_used=10,
        model="test-model",
        finish_reason="stop",
    ))
    return mock_ai_client


class TestFreeInputIntentClassification:
    async def test_classify_add_recipe(self, mock_ai_client: AsyncMock):
        from app.ai.service import AIService
        mock_ai_client.chat_completion.return_value = AIResponse(
            content=json.dumps({
                "intent": "ADD_RECIPE",
                "confidence": 0.95,
                "entities": {},
            }),
            tokens_used=10,
            model="test",
            finish_reason="stop",
        )
        service = AIService()
        result = await service.classify_intent("добавь рецепт борща")
        assert result["intent"] == "ADD_RECIPE"
        assert result["confidence"] > 0.9

    async def test_classify_search(self, mock_ai_client: AsyncMock):
        from app.ai.service import AIService
        mock_ai_client.chat_completion.return_value = AIResponse(
            content=json.dumps({
                "intent": "SEARCH_RECIPE",
                "confidence": 0.92,
                "entities": {"query": "курица с картошкой"},
            }),
            tokens_used=10,
            model="test",
            finish_reason="stop",
        )
        service = AIService()
        result = await service.classify_intent("найди что-то из курицы и картошки")
        assert result["intent"] == "SEARCH_RECIPE"
        assert result["entities"]["query"] == "курица с картошкой"

    async def test_classify_list(self, mock_ai_client: AsyncMock):
        from app.ai.service import AIService
        mock_ai_client.chat_completion.return_value = AIResponse(
            content=json.dumps({
                "intent": "LIST_RECIPES",
                "confidence": 0.97,
                "entities": {},
            }),
            tokens_used=10,
            model="test",
            finish_reason="stop",
        )
        service = AIService()
        result = await service.classify_intent("покажи мои рецепты")
        assert result["intent"] == "LIST_RECIPES"

    async def test_classify_edit(self, mock_ai_client: AsyncMock):
        from app.ai.service import AIService
        mock_ai_client.chat_completion.return_value = AIResponse(
            content=json.dumps({
                "intent": "EDIT_RECIPE",
                "confidence": 0.88,
                "entities": {"instruction": "сделай менее острым"},
            }),
            tokens_used=10,
            model="test",
            finish_reason="stop",
        )
        service = AIService()
        result = await service.classify_intent("сделай рецепт менее острым")
        assert result["intent"] == "EDIT_RECIPE"

    async def test_classify_help(self, mock_ai_client: AsyncMock):
        from app.ai.service import AIService
        mock_ai_client.chat_completion.return_value = AIResponse(
            content=json.dumps({
                "intent": "HELP",
                "confidence": 0.99,
                "entities": {},
            }),
            tokens_used=10,
            model="test",
            finish_reason="stop",
        )
        service = AIService()
        result = await service.classify_intent("помощь")
        assert result["intent"] == "HELP"

    async def test_classify_unknown(self, mock_ai_client: AsyncMock):
        from app.ai.service import AIService
        mock_ai_client.chat_completion.return_value = AIResponse(
            content=json.dumps({
                "intent": "UNKNOWN",
                "confidence": 0.4,
                "entities": {},
            }),
            tokens_used=10,
            model="test",
            finish_reason="stop",
        )
        service = AIService()
        result = await service.classify_intent("привет")
        assert result["intent"] == "UNKNOWN"


class TestFreeInputRoutingLogic:
    @pytest.fixture
    def patch_parsers(self):
        with (
            patch("app.bot.handlers.free_input.process_text_recipe") as mock_text,
            patch("app.bot.handlers.free_input.process_url_recipe") as mock_url,
            patch("app.bot.handlers.free_input.SearchService") as mock_search,
            patch("app.bot.handlers.free_input.async_session_maker") as mock_session,
            patch("app.bot.handlers.free_input.AIService") as mock_ai,
        ):
            mock_ai_instance = AsyncMock()
            mock_ai.return_value = mock_ai_instance

            mock_session.return_value.__aenter__.return_value = AsyncMock()
            mock_repo = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_repo

            mock_search_instance = AsyncMock()
            mock_search.return_value = mock_search_instance

            yield {
                "text_parser": mock_text,
                "url_parser": mock_url,
                "search_service": mock_search_instance,
                "ai_service": mock_ai_instance,
            }

    @pytest.fixture
    def patch_list(self):
        from app.bot.handlers import recipe_actions
        with patch.object(recipe_actions, "_show_recipe_page") as mock:
            yield mock

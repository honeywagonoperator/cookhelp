import json
from unittest.mock import AsyncMock

import pytest

from app.ai.client import AIResponse


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

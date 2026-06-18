import json
from unittest.mock import AsyncMock

import pytest

from app.ai.client import AIResponse
from app.ai.service import AIService


@pytest.fixture
def ai_service(mock_ai_client: AsyncMock) -> AIService:
    return AIService()


class TestAIService:
    async def test_extract_recipe(self, ai_service: AIService, mock_ai_client: AsyncMock):
        mock_ai_client.chat_completion.return_value = AIResponse(
            content=json.dumps({
                "title": "Борщ",
                "description": "Суп",
                "ingredients": ["свекла"],
                "steps": ["сварить"],
                "tags": ["суп"],
            }),
            tokens_used=50,
            model="test",
            finish_reason="stop",
        )
        result = await ai_service.extract_recipe("рецепт борща")
        assert result.title == "Борщ"
        assert result.source.type == "text"

    async def test_extract_recipe_invalid_json(self, ai_service: AIService, mock_ai_client: AsyncMock):
        mock_ai_client.chat_completion.return_value = AIResponse(
            content="not json",
            tokens_used=5,
            model="test",
            finish_reason="stop",
        )
        with pytest.raises(json.JSONDecodeError):
            await ai_service.extract_recipe("some text")

    async def test_normalize_recipe(self, ai_service: AIService, mock_ai_client: AsyncMock):
        mock_ai_client.chat_completion.return_value = AIResponse(
            content=json.dumps({
                "title": "Борщ",
                "description": "Нормализованный",
                "ingredients": ["свекла"],
                "steps": ["сварить"],
                "tags": ["суп"],
            }),
            tokens_used=30,
            model="test",
            finish_reason="stop",
        )
        result = await ai_service.normalize_recipe({"title": "борщ"})
        assert result.title == "Борщ"

    async def test_classify_intent(self, ai_service: AIService, mock_ai_client: AsyncMock):
        mock_ai_client.chat_completion.return_value = AIResponse(
            content=json.dumps({"intent": "ADD_RECIPE", "confidence": 0.95}),
            tokens_used=20,
            model="test",
            finish_reason="stop",
        )
        result = await ai_service.classify_intent("добавь рецепт борща")
        assert result["intent"] == "ADD_RECIPE"

    async def test_edit_recipe(self, ai_service: AIService, mock_ai_client: AsyncMock):
        mock_ai_client.chat_completion.return_value = AIResponse(
            content=json.dumps({
                "title": "Борщ (острый)",
                "description": "Острый суп",
                "ingredients": ["свекла", "перец чили"],
                "steps": ["сварить", "добавить перец"],
                "tags": ["суп", "острый"],
            }),
            tokens_used=40,
            model="test",
            finish_reason="stop",
        )
        result = await ai_service.edit_recipe(
            {"title": "Борщ", "ingredients": ["свекла"], "steps": ["сварить"]},
            "сделай острым",
        )
        assert "острый" in result["title"].lower()

    async def test_rerank_search_results(self, ai_service: AIService, mock_ai_client: AsyncMock):
        mock_ai_client.chat_completion.return_value = AIResponse(
            content='["id-1", "id-2"]',
            tokens_used=30,
            model="test",
            finish_reason="stop",
        )
        result = await ai_service.rerank_search_results(
            "суп",
            [{"id": "id-1", "title": "Борщ"}, {"id": "id-2", "title": "Щи"}],
        )
        assert result == ["id-1", "id-2"]

    async def test_rerank_search_results_empty(self, ai_service: AIService):
        result = await ai_service.rerank_search_results("суп", [])
        assert result == []

    async def test_generate_tags(self, ai_service: AIService, mock_ai_client: AsyncMock):
        mock_ai_client.chat_completion.return_value = AIResponse(
            content=json.dumps({"tags": ["суп", "русская"]}),
            tokens_used=15,
            model="test",
            finish_reason="stop",
        )
        result = await ai_service.generate_tags({"title": "Борщ"})
        assert result == ["суп", "русская"]

    async def test_generate_tags_fallback(self, ai_service: AIService, mock_ai_client: AsyncMock):
        mock_ai_client.chat_completion.return_value = AIResponse(
            content="invalid",
            tokens_used=5,
            model="test",
            finish_reason="stop",
        )
        result = await ai_service.generate_tags({"title": "Борщ"})
        assert result == []

    async def test_generate_embedding(self, ai_service: AIService, mock_ai_client: AsyncMock):
        mock_ai_client.create_embedding.return_value = [0.1] * 128
        result = await ai_service.generate_embedding("test text")
        assert len(result) == 128

    async def test_generate_embedding_for_recipe(self, ai_service: AIService, mock_ai_client: AsyncMock):
        mock_ai_client.create_embedding.return_value = [0.5] * 128
        result = await ai_service.generate_embedding_for_recipe({
            "title": "Борщ",
            "description": "Суп",
            "ingredients": ["свекла"],
            "tags": ["суп"],
        })
        assert len(result) == 128

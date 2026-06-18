from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock
from uuid import UUID, uuid4

import pytest
from faker import Faker

from app.ai.client import AIResponse
from app.schemas.recipe import RecipeCreate, RecipeResponse, RecipeSource

fake = Faker("ru_RU")


@pytest.fixture(autouse=True)
def override_settings(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("BOT_TOKEN", "test:token")
    monkeypatch.setenv("ENVIRONMENT", "test")
    monkeypatch.setenv("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:9999/test")
    from app.core.config import settings
    settings.environment = "test"


@pytest.fixture
def mock_ai_client(monkeypatch: pytest.MonkeyPatch) -> AsyncMock:
    client = AsyncMock()
    client.chat_completion = AsyncMock(return_value=AIResponse(
        content='{"title": "Test", "ingredients": ["a"], "steps": ["b"], "tags": ["test"]}',
        tokens_used=10,
        model="test-model",
        finish_reason="stop",
    ))
    client.create_embedding = AsyncMock(return_value=[0.1] * 128)

    import app.ai.service as ai_service_module
    import app.ai.client as ai_client_module
    monkeypatch.setattr(ai_client_module, "get_ai_client", lambda: client)
    monkeypatch.setattr(ai_service_module, "get_ai_client", lambda: client)

    return client


@pytest.fixture
def mock_repository() -> AsyncMock:
    repo = AsyncMock()
    repo.create = AsyncMock()
    repo.get_by_id = AsyncMock()
    repo.get_all = AsyncMock()
    repo.update = AsyncMock()
    repo.delete = AsyncMock()
    repo.count = AsyncMock(return_value=0)
    repo.search_by_embedding = AsyncMock()
    return repo


@pytest.fixture
def sample_recipe_id() -> UUID:
    return uuid4()


@pytest.fixture
def sample_recipe_create() -> RecipeCreate:
    return RecipeCreate(
        title="Борщ",
        description="Классический русский суп",
        ingredients=["свекла", "капуста", "картофель", "морковь"],
        steps=["Нарезать овощи", "Сварить бульон", "Добавить овощи"],
        tags=["суп", "русская кухня"],
        source=RecipeSource(type="text"),
    )


@pytest.fixture
def sample_recipe_response(sample_recipe_id: UUID) -> RecipeResponse:
    return RecipeResponse(
        id=sample_recipe_id,
        title="Борщ",
        description="Классический русский суп",
        ingredients=["свекла", "капуста", "картофель", "морковь"],
        steps=["Нарезать овощи", "Сварить бульон", "Добавить овощи"],
        tags=["суп", "русская кухня"],
        source={"type": "text"},
        embedding=[0.1] * 128,
        created_at="2026-06-19T10:00:00",
        updated_at="2026-06-19T10:00:00",
    )


@pytest.fixture
def sample_recipe_dict() -> dict:
    return {
        "title": "Борщ",
        "description": "Классический русский суп",
        "ingredients": ["свекла", "капуста", "картофель", "морковь"],
        "steps": ["Нарезать овощи", "Сварить бульон", "Добавить овощи"],
        "tags": ["суп", "русская кухня"],
        "source": {"type": "text"},
    }

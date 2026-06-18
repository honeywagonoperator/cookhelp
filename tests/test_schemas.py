import uuid

import pytest
from pydantic import ValidationError

from app.schemas.recipe import (
    PaginatedRecipes,
    RecipeCreate,
    RecipeResponse,
    RecipeSource,
    RecipeUpdate,
)


class TestRecipeSource:
    def test_valid_text(self):
        s = RecipeSource(type="text")
        assert s.type == "text"
        assert s.url is None

    def test_valid_website(self):
        s = RecipeSource(type="website", url="https://example.com")
        assert s.type == "website"
        assert s.url == "https://example.com"

    def test_invalid_type(self):
        with pytest.raises(ValidationError):
            RecipeSource(type="youtube")

    def test_invalid_type_number(self):
        with pytest.raises(ValidationError):
            RecipeSource(type=123)  # type: ignore


class TestRecipeCreate:
    def test_minimal_valid(self):
        r = RecipeCreate(
            title="Борщ",
            ingredients=["свекла"],
            steps=["сварить"],
            source=RecipeSource(type="text"),
        )
        assert r.title == "Борщ"
        assert r.tags == []

    def test_full_valid(self):
        r = RecipeCreate(
            title="Борщ",
            description="Классический суп",
            ingredients=["свекла", "капуста"],
            steps=["нарезать", "сварить"],
            tags=["суп"],
            source=RecipeSource(type="website", url="https://example.com"),
            embedding=[0.1, 0.2, 0.3],
        )
        assert r.embedding == [0.1, 0.2, 0.3]

    def test_empty_title(self):
        with pytest.raises(ValidationError):
            RecipeCreate(
                title="",
                ingredients=["a"],
                steps=["b"],
                source=RecipeSource(type="text"),
            )

    def test_title_too_long(self):
        with pytest.raises(ValidationError):
            RecipeCreate(
                title="x" * 501,
                ingredients=["a"],
                steps=["b"],
                source=RecipeSource(type="text"),
            )

    def test_empty_ingredients(self):
        with pytest.raises(ValidationError):
            RecipeCreate(
                title="Test",
                ingredients=[],
                steps=["b"],
                source=RecipeSource(type="text"),
            )

    def test_empty_steps(self):
        with pytest.raises(ValidationError):
            RecipeCreate(
                title="Test",
                ingredients=["a"],
                steps=[],
                source=RecipeSource(type="text"),
            )

    def test_model_dump(self, sample_recipe_create: RecipeCreate):
        data = sample_recipe_create.model_dump()
        assert data["title"] == "Борщ"
        assert isinstance(data["ingredients"], list)
        assert isinstance(data["source"], dict)


class TestRecipeUpdate:
    def test_empty_update(self):
        u = RecipeUpdate()
        assert u.title is None
        assert u.ingredients is None

    def test_partial_update(self):
        u = RecipeUpdate(title="Новый борщ")
        assert u.title == "Новый борщ"
        assert u.description is None

    def test_model_dump_exclude_unset(self):
        u = RecipeUpdate(title="Обновление", tags=["новое"])
        data = u.model_dump(exclude_unset=True)
        assert "title" in data
        assert "tags" in data
        assert "description" not in data

    def test_invalid_title(self):
        with pytest.raises(ValidationError):
            RecipeUpdate(title="")


class TestRecipeResponse:
    def test_valid(self, sample_recipe_id: uuid.UUID):
        r = RecipeResponse(
            id=sample_recipe_id,
            title="Борщ",
            description=None,
            ingredients=["a"],
            steps=["b"],
            tags=[],
            source={"type": "text"},
            created_at="2026-06-19T10:00:00",
            updated_at="2026-06-19T10:00:00",
        )
        assert r.title == "Борщ"
        assert r.embedding is None


class TestPaginatedRecipes:
    def test_valid(self, sample_recipe_response: RecipeResponse):
        p = PaginatedRecipes(
            items=[sample_recipe_response],
            total=1,
            page=1,
            page_size=5,
            total_pages=1,
        )
        assert len(p.items) == 1
        assert p.total == 1

    def test_empty(self):
        p = PaginatedRecipes(items=[], total=0, page=1, page_size=5, total_pages=0)
        assert len(p.items) == 0

    def test_multi_page(self, sample_recipe_response: RecipeResponse):
        items = [sample_recipe_response] * 15
        p = PaginatedRecipes(items=items, total=50, page=2, page_size=15, total_pages=4)
        assert p.total_pages == 4

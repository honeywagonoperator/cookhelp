from typing import Any
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict


class RecipeSource(BaseModel):
    type: str = Field(..., pattern="^(text|website|youtube)$")
    url: str | None = None


class RecipeCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: str | None = None
    ingredients: list[str] = Field(..., min_length=1)
    steps: list[str] = Field(..., min_length=1)
    tags: list[str] = Field(default_factory=list)
    source: RecipeSource
    embedding: list[float] | None = None


class RecipeUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=500)
    description: str | None = None
    ingredients: list[str] | None = None
    steps: list[str] | None = None
    tags: list[str] | None = None
    source: RecipeSource | None = None
    embedding: list[float] | None = None


class RecipeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    description: str | None
    ingredients: list[str]
    steps: list[str]
    tags: list[str]
    source: dict[str, Any]
    embedding: list[float] | None = None
    created_at: str
    updated_at: str


class PaginatedRecipes(BaseModel):
    items: list[RecipeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
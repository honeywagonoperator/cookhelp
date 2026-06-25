from uuid import UUID

from app.models.recipe import Recipe
from app.schemas.recipe import RecipeResponse


class RecipeMapper:
    @staticmethod
    def to_response(recipe: Recipe) -> RecipeResponse:
        return RecipeResponse(
            id=recipe.id,
            title=recipe.title,
            description=recipe.description,
            ingredients=recipe.ingredients,
            steps=recipe.steps,
            tags=recipe.tags,
            source=recipe.source,
            embedding=recipe.embedding,
            created_at=recipe.created_at.isoformat(),
            updated_at=recipe.updated_at.isoformat(),
        )

from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.models.recipe import Recipe
from app.schemas.recipe import RecipeResponse


def format_recipe_card(recipe: Recipe | RecipeResponse) -> str:
    parts = [
        f"🍽 <b>{recipe.title}</b>",
        recipe.description or "",
        "<b>Ингредиенты:</b>",
        "\n".join(f"• {i}" for i in recipe.ingredients),
        "",
    ]
    if recipe.steps:
        parts.append("<b>Шаги:</b>")
        for i, step in enumerate(recipe.steps):
            parts.append(f"{i + 1}. {step}")
        parts.append("")
    parts.append(f"<b>Тэги:</b> {', '.join(recipe.tags) if recipe.tags else '—'}")
    return "\n".join(filter(None, parts))


def build_recipe_keyboard(recipe_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👁 Шаги", callback_data=f"steps:{recipe_id}"),
            InlineKeyboardButton(text="✏️ Правка", callback_data=f"edit:{recipe_id}"),
        ],
        [
            InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete:{recipe_id}"),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")],
    ])


def build_steps_keyboard(recipe_id: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit:{recipe_id}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"delete:{recipe_id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"recipe:{recipe_id}")],
    ])


def build_search_keyboard(
    results: list[RecipeResponse],
    limit: int = 10,
) -> InlineKeyboardMarkup:
    buttons = []
    for i, r in enumerate(results[:limit]):
        buttons.append([InlineKeyboardButton(
            text=f"{i + 1}. {r.title}",
            callback_data=f"recipe:{r.id}",
        )])
    return InlineKeyboardMarkup(inline_keyboard=buttons)

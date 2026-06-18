import logging

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    ReplyKeyboardRemove,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.bot.keyboards import main_menu
from app.bot.states import EditRecipeStates
from app.database.connection import async_session_maker
from app.repositories.recipe import RecipeRepository
from app.services.recipe import RecipeService

logger = logging.getLogger(__name__)

router = Router()


@router.callback_query(F.data.startswith("recipe:"))
async def show_recipe(callback: CallbackQuery) -> None:
    recipe_id = callback.data.split(":")[1]

    async with async_session_maker() as session:
        repository = RecipeRepository(session)
        service = RecipeService(repository)
        recipe = await service.get_recipe(recipe_id)

    if not recipe:
        await callback.message.edit_text("❌ Рецепт не найден.")
        return

    text = (
        f"🍽 <b>{recipe.title}</b>\n\n"
        f"{recipe.description or ''}\n\n"
        f"<b>Ингредиенты:</b>\n" + "\n".join(f"• {i}" for i in recipe.ingredients) + "\n\n"
        f"<b>Тэги:</b> {', '.join(recipe.tags) if recipe.tags else '—'}"
    )

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👁 Показать шаги", callback_data=f"steps:{recipe.id}"),
            InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit:{recipe.id}"),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")],
    ])

    await callback.message.edit_text(text, reply_markup=buttons)
    await callback.answer()


@router.callback_query(F.data.startswith("steps:"))
async def show_steps(callback: CallbackQuery) -> None:
    recipe_id = callback.data.split(":")[1]

    async with async_session_maker() as session:
        repository = RecipeRepository(session)
        service = RecipeService(repository)
        recipe = await service.get_recipe(recipe_id)

    if not recipe:
        await callback.message.edit_text("❌ Рецепт не найден.")
        return

    steps_text = "\n\n".join(
        f"<b>Шаг {i + 1}.</b> {step}" for i, step in enumerate(recipe.steps)
    )

    text = f"🍽 <b>{recipe.title}</b> — пошаговый рецепт\n\n{steps_text}"

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"edit:{recipe.id}")],
        [InlineKeyboardButton(text="🔙 Назад", callback_data=f"recipe:{recipe.id}")],
    ])

    await callback.message.edit_text(text, reply_markup=buttons)
    await callback.answer()


@router.callback_query(F.data.startswith("edit:"))
async def edit_recipe_start(callback: CallbackQuery, state: FSMContext) -> None:
    recipe_id = callback.data.split(":")[1]
    await state.update_data(recipe_id=recipe_id)
    await state.set_state(EditRecipeStates.waiting_for_instruction)

    await callback.message.edit_text(
        "✏️ <b>Редактирование рецепта</b>\n\n"
        "Напишите, что изменить:\n\n"
        "Например:\n"
        "• Сделай менее острым\n"
        "• Замени курицу на индейку\n"
        "• Сделай вегетарианскую версию\n"
        "• Сократи время приготовления",
    )
    await callback.answer()


@router.message(StateFilter(EditRecipeStates.waiting_for_instruction))
async def edit_recipe_apply(message: Message, state: FSMContext) -> None:
    instruction = message.text
    if not instruction:
        await message.answer("Пожалуйста, напишите, что изменить.")
        return

    data = await state.get_data()
    recipe_id = data.get("recipe_id")

    await message.answer("⏳ Редактирую рецепт...")

    try:
        from app.ai.service import AIService

        ai_service = AIService()

        async with async_session_maker() as session:
            repository = RecipeRepository(session)
            service = RecipeService(repository, ai_service)
            recipe = await service.get_recipe(recipe_id)

            if not recipe:
                await message.answer("❌ Рецепт не найден.", reply_markup=main_menu)
                return

            recipe_dict = recipe.model_dump()
            edited = await ai_service.edit_recipe(recipe_dict, instruction)
            normalized = await ai_service.normalize_recipe(edited)

            from app.schemas.recipe import RecipeUpdate

            update_data = RecipeUpdate(
                title=normalized.title,
                description=normalized.description,
                ingredients=normalized.ingredients,
                steps=normalized.steps,
                tags=normalized.tags,
            )
            updated = await service.update_recipe(recipe_id, update_data)
            await session.commit()

            if updated:
                await message.answer(
                    f"✅ Рецепт «{updated.title}» обновлён!",
                    reply_markup=main_menu,
                )
            else:
                await message.answer("❌ Не удалось обновить рецепт.", reply_markup=main_menu)

    except Exception as e:
        logger.error(f"Edit error: {e}")
        await message.answer(
            "❌ Ошибка при редактировании. Попробуйте ещё раз.",
            reply_markup=main_menu,
        )
    finally:
        await state.clear()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        "👋 Главное меню",
        reply_markup=main_menu,
    )
    await callback.answer()

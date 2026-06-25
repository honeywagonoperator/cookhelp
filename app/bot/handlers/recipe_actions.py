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

from app.bot.helpers import build_recipe_keyboard, build_steps_keyboard, format_recipe_card
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

    text = format_recipe_card(recipe)
    buttons = build_recipe_keyboard(str(recipe.id))

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

    buttons = build_steps_keyboard(str(recipe.id))

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
        from app.ai.service import get_ai_service

        ai_service = get_ai_service()

        async with async_session_maker() as session:
            repository = RecipeRepository(session)
            service = RecipeService(repository, ai_service)
            recipe = await service.get_recipe(recipe_id)

            if not recipe:
                await message.answer("❌ Рецепт не найден.", reply_markup=main_menu)
                return

            import json
            recipe_dict = json.loads(recipe.model_dump_json())
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
        logger.exception("Edit error: %s", e)
        await message.answer(
            "❌ Ошибка при редактировании. Попробуйте ещё раз.",
            reply_markup=main_menu,
        )
    finally:
        await state.clear()


@router.callback_query(F.data == "back_to_menu")
async def back_to_menu(callback: CallbackQuery) -> None:
    await callback.message.delete()
    await callback.message.answer(
        "👋 Главное меню",
        reply_markup=main_menu,
    )
    await callback.answer()


@router.message(F.text == "Мои рецепты")
async def list_recipes(message: Message) -> None:
    await _show_recipe_page(message, page=1)


@router.callback_query(F.data.startswith("list:"))
async def list_recipes_page(callback: CallbackQuery) -> None:
    page = int(callback.data.split(":")[1])
    await _show_recipe_page(callback.message, page=page, edit=True)
    await callback.answer()


async def _show_recipe_page(target, page: int, edit: bool = False) -> None:
    page_size = 5

    async with async_session_maker() as session:
        repository = RecipeRepository(session)
        service = RecipeService(repository)
        paginated = await service.list_recipes(page=page, page_size=page_size)

    if not paginated.items:
        text = "📭 У вас пока нет рецептов.\n\nНажмите «Создать рецепт» чтобы добавить первый!"
        if edit:
            await target.delete()
            await target.answer(text, reply_markup=main_menu)
        else:
            await target.answer(text, reply_markup=main_menu)
        return

    text = f"📋 <b>Мои рецепты</b> (страница {page}/{paginated.total_pages})\n\n"
    buttons = []

    for r in paginated.items:
        text += f"• {r.title}\n"
        buttons.append([InlineKeyboardButton(
            text=f"📖 {r.title}",
            callback_data=f"recipe:{r.id}",
        )])

    nav_buttons = []
    if page > 1:
        nav_buttons.append(InlineKeyboardButton(text="⬅️ Назад", callback_data=f"list:{page - 1}"))
    if page < paginated.total_pages:
        nav_buttons.append(InlineKeyboardButton(text="Вперёд ➡️", callback_data=f"list:{page + 1}"))

    if nav_buttons:
        buttons.append(nav_buttons)

    markup = InlineKeyboardMarkup(inline_keyboard=buttons)

    if edit:
        await target.edit_text(text, reply_markup=markup)
    else:
        await target.answer(text, reply_markup=markup)


@router.callback_query(F.data.startswith("delete_confirm:"))
async def delete_recipe_confirm(callback: CallbackQuery) -> None:
    recipe_id = callback.data.split(":")[1]

    async with async_session_maker() as session:
        repository = RecipeRepository(session)
        service = RecipeService(repository)
        deleted = await service.delete_recipe(recipe_id)
        await session.commit()

    if deleted:
        await callback.message.edit_text("🗑 Рецепт удалён.")
        await _show_recipe_page(callback.message, page=1, edit=True)
    else:
        await callback.message.edit_text("❌ Рецепт не найден.")
    await callback.answer()


@router.callback_query(F.data.startswith("delete:"))
async def delete_recipe_prompt(callback: CallbackQuery) -> None:
    recipe_id = callback.data.split(":")[1]

    async with async_session_maker() as session:
        repository = RecipeRepository(session)
        service = RecipeService(repository)
        recipe = await service.get_recipe(recipe_id)

    if not recipe:
        await callback.message.edit_text("❌ Рецепт не найден.")
        await callback.answer()
        return

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да, удалить", callback_data=f"delete_confirm:{recipe_id}"),
            InlineKeyboardButton(text="❌ Нет", callback_data=f"recipe:{recipe_id}"),
        ],
    ])

    await callback.message.edit_text(
        f"🗑 Удалить рецепт «{recipe.title}»?\n\nЭто действие нельзя отменить.",
        reply_markup=buttons,
    )
    await callback.answer()

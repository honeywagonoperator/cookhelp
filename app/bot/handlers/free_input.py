import logging

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, ReplyKeyboardRemove

from app.bot.helpers import build_search_keyboard, format_recipe_card
from app.bot.keyboards import main_menu
from app.bot.states import FreeInputStates, EditRecipeStates
from app.database.connection import async_session_maker
from app.repositories.recipe import RecipeRepository
from app.services.recipe import RecipeService

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text == "Свободный ввод")
async def free_input_start(message: Message, state: FSMContext) -> None:
    await state.set_state(FreeInputStates.waiting_for_input)
    await message.answer(
        "Напишите ваш запрос естественным языком.\n\n"
        "Например:\n"
        "• Добавь рецепт пасты карбонара\n"
        "• Найди что-нибудь из курицы и картошки\n"
        "• Покажи последние рецепты\n"
        "• Измени последний рецепт",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(StateFilter(FreeInputStates.waiting_for_input))
async def free_input_handle(message: Message, state: FSMContext) -> None:
    text = message.text
    if not text:
        await message.answer("Пожалуйста, напишите ваш запрос.")
        return

    progress = await message.answer("⏳ Анализирую ваш запрос...")
    await state.clear()

    try:
        from app.ai.service import get_ai_service

        ai_service = get_ai_service()
        intent_data = await ai_service.classify_intent(text)
        intent = intent_data.get("intent", "UNKNOWN")
        confidence = intent_data.get("confidence", 0)
        entities = intent_data.get("entities", {})
        logger.info("Free input intent", extra={"intent": intent, "confidence": confidence})

        if confidence < 0.3:
            await progress.delete()
            await message.answer(
                "🤔 Не совсем понял ваш запрос. Попробуйте:\n"
                "• Добавить рецепт текстом или ссылкой\n"
                "• Найти рецепт по названию или ингредиентам\n"
                "• Показать мои рецепты",
                reply_markup=main_menu,
            )
            return

        if intent == "ADD_RECIPE":
            await _handle_add_recipe(message, progress, text)
        elif intent == "SEARCH_RECIPE":
            await _handle_search(message, progress, entities.get("query") or text)
        elif intent == "SHOW_RECIPE":
            await _handle_show_recipe(message, progress, entities.get("query") or text)
        elif intent == "EDIT_RECIPE":
            await _handle_edit_recipe(message, state, progress, entities.get("instruction") or text)
        elif intent == "LIST_RECIPES":
            await _handle_list_recipes(message, progress)
        elif intent == "HELP":
            await _handle_help(message, progress)
        else:
            await progress.delete()
            await message.answer(
                "🤔 Не совсем понял ваш запрос. Попробуйте:\n"
                "• Добавить рецепт текстом или ссылкой\n"
                "• Найти рецепт по названию или ингредиентам\n"
                "• Показать мои рецепты",
                reply_markup=main_menu,
            )
    except Exception as e:
        logger.exception("Free input error: %s", e)
        await progress.delete()
        await message.answer(
            "❌ Ошибка при обработке запроса. Попробуйте ещё раз.",
            reply_markup=main_menu,
        )


async def _handle_add_recipe(message: Message, progress: Message, text: str) -> None:
    if text.startswith("http"):
        await progress.edit_text("⏳ Извлекаю рецепт с сайта...")
        from app.parsers.website import process_url_recipe
        result = await process_url_recipe(text)
    else:
        await progress.edit_text("⏳ Обрабатываю текст рецепта...")
        from app.parsers.text import process_text_recipe
        result = await process_text_recipe(text)

    if result.get("success"):
        recipe = result["recipe"]
        await message.answer(
            f"✅ <b>{recipe.title}</b>\n\n{result['message']}",
            reply_markup=main_menu,
        )
    else:
        await message.answer(
            f"❌ {result.get('message', 'Не удалось обработать запрос.')}",
            reply_markup=main_menu,
        )
    await progress.delete()


async def _handle_search(message: Message, progress: Message, query: str) -> None:
    await progress.edit_text(f"🔍 Ищу: «{query}»...")

    from app.ai.service import get_ai_service
    ai_service = get_ai_service()
    async with async_session_maker() as session:
        repository = RecipeRepository(session)
        service = RecipeService(repository, ai_service)
        results = await service.search(query)

    if not results:
        await progress.delete()
        await message.answer(
            "😕 Ничего не найдено. Попробуйте другой запрос.",
            reply_markup=main_menu,
        )
        return

    await progress.edit_text("📋 <b>Результаты поиска:</b>")
    await message.answer(
        "⬆️ Результаты выше. Выберите рецепт для просмотра.",
        reply_markup=build_search_keyboard(results),
    )


async def _handle_show_recipe(message: Message, progress: Message, query: str) -> None:
    await progress.edit_text(f"🔍 Ищу рецепт «{query}»...")

    from app.ai.service import get_ai_service
    ai_service = get_ai_service()
    async with async_session_maker() as session:
        repository = RecipeRepository(session)
        service = RecipeService(repository, ai_service)
        results = await service.search(query)

    if not results:
        await progress.delete()
        await message.answer(
            f"😕 Рецепт «{query}» не найден. Попробуйте другой запрос.",
            reply_markup=main_menu,
        )
        return

    recipe = results[0]
    text = format_recipe_card(recipe)

    buttons = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👁 Шаги", callback_data=f"steps:{recipe.id}"),
            InlineKeyboardButton(text="✏️ Правка", callback_data=f"edit:{recipe.id}"),
        ],
        [InlineKeyboardButton(text="🔙 Назад", callback_data="back_to_menu")],
    ])

    await progress.delete()
    await message.answer(text, reply_markup=buttons)


async def _handle_edit_recipe(message: Message, state: FSMContext, progress: Message, instruction: str) -> None:
    await progress.edit_text("🔍 Ищу рецепт для редактирования...")

    from app.ai.service import get_ai_service
    ai_service = get_ai_service()
    async with async_session_maker() as session:
        repository = RecipeRepository(session)
        all_recipes = await repository.get_all(limit=50)

    if not all_recipes:
        await progress.delete()
        await message.answer(
            "📭 Нет рецептов для редактирования. Сначала добавьте рецепт.",
            reply_markup=main_menu,
        )
        return

    async with async_session_maker() as session:
        repository = RecipeRepository(session)
        service = RecipeService(repository, ai_service)
        results = await service.search(instruction)

    if not results:
        last = all_recipes[-1]
        await state.update_data(recipe_id=str(last.id))
        await state.set_state(EditRecipeStates.waiting_for_instruction)
        await progress.edit_text(
            f"✏️ Выбран последний рецепт: «{last.title}».\n\n"
            "Напишите, что изменить:\n"
            "• Сделай менее острым\n"
            "• Замени курицу на индейку",
        )
        return

    recipe = results[0]
    await state.update_data(recipe_id=str(recipe.id))
    await state.set_state(EditRecipeStates.waiting_for_instruction)
    await progress.edit_text(
        f"✏️ Выбран рецепт: «{recipe.title}».\n\n"
        "Напишите, что изменить:\n"
        "• Сделай менее острым\n"
        "• Замени курицу на индейку",
    )


async def _handle_list_recipes(message: Message, progress: Message) -> None:
    await progress.delete()

    async with async_session_maker() as session:
        repository = RecipeRepository(session)
        recipes = await repository.get_all(limit=20)
        total = await repository.count()

    if not recipes:
        await message.answer(
            "📭 У вас пока нет рецептов.\n\nНажмите «Создать рецепт» чтобы добавить первый!",
            reply_markup=main_menu,
        )
        return

    text = f"📋 <b>Мои рецепты</b> ({total})\n\n"
    buttons = []

    for r in recipes:
        text += f"• {r.title}\n"
        buttons.append([InlineKeyboardButton(
            text=f"📖 {r.title}",
            callback_data=f"recipe:{r.id}",
        )])

    await message.answer(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
    )


async def _handle_help(message: Message, progress: Message) -> None:
    help_text = (
        "🍳 <b>CookHelp — Помощь</b>\n\n"
        "<b>Создать рецепт</b>\n"
        "Отправьте текст рецепта или ссылку на сайт.\n\n"
        "<b>Найти рецепт</b>\n"
        "Поиск по названию, ингредиентам или описанию.\n\n"
        "<b>Мои рецепты</b>\n"
        "Список всех рецептов с возможностью удалить.\n\n"
        "<b>Свободный ввод</b>\n"
        "Любой запрос естественным языком — бот сам определит, что нужно.\n\n"
        "<b>Примеры:</b>\n"
        "• Добавь рецепт борща\n"
        "• Найди что-то из курицы\n"
        "• Покажи мои рецепты\n"
        "• Сделай рецепт менее острым"
    )
    await progress.delete()
    await message.answer(help_text, reply_markup=main_menu)

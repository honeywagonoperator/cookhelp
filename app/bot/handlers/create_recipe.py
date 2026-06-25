import logging

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from app.bot.keyboards import main_menu
from app.bot.states import CreateRecipeStates
from app.parsers.exceptions import URLFetchError, URLParseError
from app.parsers.text import process_text_recipe
from app.parsers.website import process_url_recipe

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text == "Создать рецепт")
async def create_recipe_start(message: Message, state: FSMContext) -> None:
    await state.set_state(CreateRecipeStates.waiting_for_input)
    await message.answer(
        "Отправьте:\n\n"
        "• текст рецепта\n"
        "• ссылку на сайт с рецептом",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(StateFilter(CreateRecipeStates.waiting_for_input))
async def create_recipe_input(message: Message, state: FSMContext) -> None:
    try:
        if message.text and message.text.startswith("http"):
            await message.answer("⏳ Извлекаю рецепт с сайта...")
            result = await process_url_recipe(message.text)
        elif message.text:
            await message.answer("⏳ Обрабатываю текст рецепта...")
            result = await process_text_recipe(message.text)
        else:
            await message.answer("Пожалуйста, отправьте текст или ссылку.")
            return

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
    except (URLFetchError, URLParseError) as e:
        logger.warning("URL processing error: %s", e)
        await message.answer(
            f"❌ Не удалось получить рецепт с сайта.\n\n"
            f"Проверьте ссылку или попробуйте ввести рецепт текстом.",
            reply_markup=main_menu,
        )
    except Exception as e:
        logger.exception("Error processing recipe input: %s", e)
        await message.answer(
            "❌ Произошла ошибка при обработке. Попробуйте ещё раз.",
            reply_markup=main_menu,
        )
    finally:
        await state.clear()

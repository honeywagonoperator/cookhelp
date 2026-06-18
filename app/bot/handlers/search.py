import logging

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message, ReplyKeyboardRemove

from app.bot.keyboards import main_menu
from app.bot.states import SearchStates
from app.database.connection import async_session_maker
from app.repositories.recipe import RecipeRepository
from app.services.search import SearchService

logger = logging.getLogger(__name__)

router = Router()


@router.message(F.text == "Найти рецепт")
async def search_start(message: Message, state: FSMContext) -> None:
    await state.set_state(SearchStates.waiting_for_query)
    await message.answer(
        "Введите запрос:\n\n"
        "Например:\n"
        "• Что приготовить из курицы?\n"
        "• Быстрый ужин\n"
        "• Азиатская кухня\n"
        "• Без мяса\n"
        "• Название блюда",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(StateFilter(SearchStates.waiting_for_query))
async def search_query(message: Message, state: FSMContext) -> None:
    query = message.text
    if not query:
        await message.answer("Пожалуйста, введите текстовый запрос.")
        return

    await message.answer(f"🔍 Ищу рецепты по запросу: \"{query}\"...")

    try:
        from app.ai.service import AIService

        ai_service = AIService()
        async with async_session_maker() as session:
            repository = RecipeRepository(session)
            search_service = SearchService(repository, ai_service)
            results = await search_service.search(query)

        if not results:
            await message.answer(
                "😕 Ничего не найдено. Попробуйте другой запрос.",
                reply_markup=main_menu,
            )
            return

        buttons = []
        for i, r in enumerate(results[:10]):
            buttons.append([InlineKeyboardButton(
                text=f"{i + 1}. {r.title}",
                callback_data=f"recipe:{r.id}",
            )])

        await message.answer(
            "📋 <b>Результаты поиска:</b>",
            reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        )

    except Exception as e:
        logger.error(f"Search error: {e}")
        await message.answer(
            "❌ Ошибка при поиске. Попробуйте ещё раз.",
            reply_markup=main_menu,
        )
    finally:
        await state.clear()

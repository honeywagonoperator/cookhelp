from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from app.bot.keyboards import main_menu
from app.bot.states import SearchStates

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

    await message.answer(
        f"🔍 Ищу рецепты по запросу: \"{query}\"...",
        reply_markup=main_menu,
    )
    await state.clear()

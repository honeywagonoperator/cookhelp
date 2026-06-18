from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from app.bot.keyboards import main_menu
from app.bot.states import FreeInputStates

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

    await message.answer(
        "⏳ Анализирую ваш запрос...",
        reply_markup=main_menu,
    )
    await state.clear()

from aiogram import Router, F
from aiogram.filters import StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

from app.bot.keyboards import main_menu
from app.bot.states import CreateRecipeStates

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
    if message.text and message.text.startswith("http"):
        await message.answer(
            "⏳ Обрабатываю ссылку...",
            reply_markup=main_menu,
        )
    elif message.text:
        await message.answer(
            "⏳ Обрабатываю текст рецепта...",
            reply_markup=main_menu,
        )
    else:
        await message.answer(
            "Пожалуйста, отправьте текст или ссылку.",
        )
        return

    await state.clear()

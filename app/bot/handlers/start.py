from aiogram import Router
from aiogram.filters import Command, CommandStart
from aiogram.types import Message

from app.bot.keyboards import main_menu

router = Router()


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    await message.answer(
        "👋 Добро пожаловать в CookHelp!\n\n"
        "Я помогу вам хранить и искать рецепты. "
        "Выберите действие в меню ниже.",
        reply_markup=main_menu,
    )


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(
        "📖 <b>Справка CookHelp</b>\n\n"
        "• <b>Создать рецепт</b> — добавить рецепт из текста или ссылки на сайт\n"
        "• <b>Найти рецепт</b> — поиск по сохранённым рецептам\n"
        "• <b>Свободный ввод</b> — общение с AI на естественном языке\n\n"
        "Примеры запросов:\n"
        "• Что приготовить из курицы?\n"
        "• Найди быстрый ужин\n"
        "• Замени курицу на индейку\n"
        "• Покажи мои азиатские рецепты",
        reply_markup=main_menu,
    )

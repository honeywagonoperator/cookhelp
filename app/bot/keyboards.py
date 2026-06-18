from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Создать рецепт")],
        [KeyboardButton(text="Найти рецепт")],
        [KeyboardButton(text="Свободный ввод")],
        [KeyboardButton(text="Помощь")],
    ],
    resize_keyboard=True,
    input_field_placeholder="Выберите действие",
)

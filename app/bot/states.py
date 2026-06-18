from aiogram.fsm.state import State, StatesGroup


class CreateRecipeStates(StatesGroup):
    waiting_for_input = State()


class SearchStates(StatesGroup):
    waiting_for_query = State()


class FreeInputStates(StatesGroup):
    waiting_for_input = State()

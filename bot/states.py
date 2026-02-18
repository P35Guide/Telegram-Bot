from aiogram.fsm.state import State, StatesGroup


class BotState(StatesGroup):
    selecting_language = State()
    selecting_radius = State()

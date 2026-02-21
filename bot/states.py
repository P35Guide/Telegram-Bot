from aiogram.fsm.state import State, StatesGroup


class BotState(StatesGroup):
    selecting_language = State()
    selecting_radius = State()
    selecting_included_types = State()
    selecting_excluded_types = State()
    selecting_max_result_count = State()
    entering_coordinates = State()

from aiogram.fsm.state import State, StatesGroup


class BotState(StatesGroup):
    selecting_language = State()
    selecting_radius = State()
    selecting_included_types = State()
    selecting_excluded_types = State()
    selecting_max_result_count = State()
    entering_coordinates = State()
    browsing_places = State()
    choosing_location_type = State()
    entering_city_name = State()

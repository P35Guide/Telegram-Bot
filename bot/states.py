from aiogram.fsm.state import State, StatesGroup

class AddPlace(StatesGroup):
    wait_for_title = State()
    wait_for_discription = State()
    wait_for_shor_adress = State()
    wait_for_foto = State()

class BotState(StatesGroup):
    selecting_language = State()
    selecting_radius = State()
    selecting_included_types = State()
    selecting_excluded_types = State()
    selecting_max_result_count = State()
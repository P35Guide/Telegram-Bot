from aiogram.fsm.state import State, StatesGroup

class AddressState(StatesGroup):
	waiting_for_address = State()
from aiogram.fsm.state import State, StatesGroup


class RegistrationStates(StatesGroup):
    """States for user registration flow."""
    waiting_for_name = State()
    waiting_for_phone = State()
    

class TaskStates(StatesGroup):
    """States for contest tasks flow."""
    checking_subscription = State()
    waiting_for_photo = State()
    ready_for_result = State()

from aiogram.filters.state import State, StatesGroup


class ChooseDateStates(StatesGroup):
    choose_new_date = State()
    chose_service = State()
    choose_existing_date = State()
    waiting_for_history_input = State()
    update_date = State()
    buffer_input = State()
    buffer_delete = State()
    buffer_for_change = State()
    calculation = State()
    info_state = State()
    phone = State()
    name = State()


class AdminStates(StatesGroup):
    admin = State()
    get_records_id = State()
    new_date = State()
    on_delete = State()

from aiogram import Router, Bot
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from filter import DateFilter, ServiceFilter, DateFilterCorr
from aiogram.filters.state import StateFilter
from aiogram.enums import ParseMode
import db
import states
import re

router = Router()

ADMINID_GLOBAL = 366934724


@router.message(Command("start"))
async def start_handler(msg: Message, state: FSMContext):
    await db.start_db(msg.from_user.id)
    adm_rls = await db.admin_check(msg.from_user.id)
    if adm_rls == True:
        await msg.answer("Вітаємо в адмін панелі Poggers Cars. Список доступних команд:'\n/records - список всіх "
                         "записів\n/new_date - додати нову вільну дату\n/users - вивести список всіх "
                         "користувачів\n/usr_cancel - відмінити чийсь запис")
        await state.set_state(states.AdminStates.admin)
    else:
        await msg.answer("Привіт! Вітаємо в Poggers Cars!\n /name - додати ім'я\n/phone - додати свій контактний "
                         "номер телефону")


@router.message(Command("services"))
async def services_handler(msg: Message):
    services_data = await db.show_service()
    await msg.answer(services_data)


@router.message(Command("free"))
async def date_list(msg: Message, state: FSMContext):
    dates = await db.select_date()
    await msg.answer(f"Виберіть вільну дату та введіть її як відповідь щоб записатися \n {dates}",
                     parse_mode=ParseMode.MARKDOWN_V2)
    await state.set_state(states.ChooseDateStates.choose_new_date)


@router.message(
    DateFilter(date_is_correct=True),
    states.ChooseDateStates.choose_new_date
)
async def date_selection(msg: Message, state: FSMContext):
    chosen_date = await db.choose_date(msg.from_user.id, msg.text)
    list_of_service = await db.show_service()
    app_id = await db.get_appointmentId(msg.text)
    await msg.answer(f"Ви записалися на {chosen_date}.\nТепер виберіть послугу яка вам потрібна: \n" + list_of_service)
    await state.update_data(appid=app_id)
    await state.set_state(states.ChooseDateStates.chose_service)


@router.message(states.ChooseDateStates.chose_service,
                ServiceFilter(service_correct=True)
                )
async def add_service(msg: Message, state: FSMContext, bot: Bot):
    service_id = await db.get_service_id(msg.text)
    if service_id:
        state_data = await state.get_data()
        appid = state_data.get("appid")
        date = await db.date_by_appid(appid)
        user_id = await db.get_user_id(msg.from_user.id)
        await db.update_on_create(int(user_id), int(appid), int(service_id))
        await msg.answer("Запис додано. Дякую за звернення!")
        await bot.send_chat_action(ADMINID_GLOBAL, "typing")  # Використовуйте "typing"
        await bot.send_message(ADMINID_GLOBAL, f"Додано новий запис на {date}")
        await state.clear()
    else:
        await msg.answer("Введіть коректну назву сервісу")

@router.message(Command("history"))
async def history(msg: Message, state: FSMContext):
    history_data = await db.get_history(msg.from_user.id)
    await msg.answer(
        f"Ваші записи: \n" + history_data + "\n Виберіть одну з наступних дій:\n/change щоб змінити дату "
                                            "запису\n/delete щоб видалити запис"
                                            "\n/info щоб вивести повну інформації про запис",
        parse_mode=ParseMode.MARKDOWN_V2)
    await state.set_state(states.ChooseDateStates.waiting_for_history_input)


@router.message(Command("change"), states.ChooseDateStates.waiting_for_history_input)
async def change_buffer(msg: Message, state: FSMContext):
    await msg.answer("Надішліть дату з Вашого списку на яку ви записані")
    await state.set_state(states.ChooseDateStates.buffer_for_change)


@router.message(DateFilter(date_is_correct=True), states.ChooseDateStates.buffer_for_change)
async def input_buffer(msg: Message, state: FSMContext):
    dates = await db.select_date()
    await msg.answer("Запис знайдено, введіть нову дату\n" + dates, parse_mode=ParseMode.MARKDOWN_V2)
    await state.update_data(date=msg.text)
    await state.set_state(states.ChooseDateStates.buffer_input)


@router.message(DateFilter(date_is_correct=True),
                states.ChooseDateStates.buffer_input)
async def date_update_records(msg: Message, state: FSMContext):
    """buffer for info"""
    state_data = await state.get_data()
    date = state_data.get("date")
    new_date = msg.text
    await db.update_date(msg.from_user.id, date, new_date)
    await msg.answer("Ваша нова дата " + new_date)
    await state.clear()


@router.message(Command("delete"), states.ChooseDateStates.waiting_for_history_input)
async def delete_message(msg: Message, state: FSMContext):
    """delete_buffer"""
    await state.set_state(states.ChooseDateStates.buffer_delete)
    await msg.answer("Виберіть дату яку хочете видалити")


@router.message(DateFilter(date_is_correct=True), states.ChooseDateStates.buffer_delete)
async def delete_row(msg: Message, state: FSMContext, bot: Bot):
    """deletion"""
    date = msg.text
    res = await db.delete_date(msg.from_user.id, date)
    if res is True:
        await msg.answer("Запис видалено")
        await bot.send_chat_action(ADMINID_GLOBAL, "typing")  # Використовуйте "typing"
        await bot.send_message(ADMINID_GLOBAL, "Звільнилася дата на "+ date)
        await state.clear()
    else:
        await msg.answer("Помилкова дата, введіть існуючу зі свого списку")


@router.message(Command("calc"))
async def calculation(msg: Message, state: FSMContext):
    """Calc set state"""
    services_data = await db.show_service()
    await msg.answer("Напишіть сервіси які вас цікавлять через кому: \n" + services_data)
    await state.set_state(states.ChooseDateStates.calculation)


@router.message(states.ChooseDateStates.calculation)
async def calculation(msg: Message, state: FSMContext):
    """Calculation"""
    list_of_objects = re.split(r'\s*,\s*', msg.text)
    result = await db.calculate_services(list_of_objects)
    await msg.answer("Загальна сумма = " + str(result))
    await state.clear()


@router.message(Command("info"), states.ChooseDateStates.waiting_for_history_input)
async def info_buffer(msg: Message, state: FSMContext):
    """buffer for info"""
    await state.set_state(states.ChooseDateStates.info_state)
    await msg.answer("Виберіть дату за яку хочете отримати інформацію")


@router.message(DateFilter(date_is_correct=True), states.ChooseDateStates.info_state)
async def info_print(msg: Message, state: FSMContext):
    result = await db.info_out(msg.from_user.id, msg.text)
    await msg.answer(result)
    await state.clear()


@router.message(Command("phone"))
async def phone_buffer(msg: Message, state: FSMContext):
    await msg.answer("Введіть номер телефону")
    await state.set_state(states.ChooseDateStates.phone)


@router.message(states.ChooseDateStates.phone)
async def add_phone(msg: Message, state: FSMContext):
    await db.add_phone(msg.from_user.id, msg.text)
    await msg.answer("Номер додано до вашого облікового запису")
    await state.clear()


@router.message(Command("name"))
async def name_buffer(msg: Message, state: FSMContext):
    await msg.answer("Як до Вас звертатися?")
    await state.set_state(states.ChooseDateStates.name)


@router.message(states.ChooseDateStates.name)
async def add_name(msg: Message, state: FSMContext):
    await db.add_name(msg.from_user.id, msg.text)
    await msg.answer(f"Дякуємо за звернення, {msg.text}!")
    await state.clear()


@router.message(Command("new_date"), states.AdminStates.admin)
async def add_new_date(msg: Message, state: FSMContext):
    await msg.answer("Введіть нову дату та час який хочете додати в форматі YYYY-MM-DD HH:MM")
    await state.set_state(states.AdminStates.new_date)


@router.message(DateFilterCorr(date_is_correct=True), states.AdminStates.new_date)
async def insert_new_date(msg: Message, state: FSMContext):
    await db.insert_new_date(msg.text)
    await msg.answer("Дату додано до списку")
    await state.clear()


@router.message(Command("records"), StateFilter(*[states.AdminStates.admin, states.AdminStates.new_date]))
async def get_records(msg: Message):
    history = await db.get_all_records()
    await msg.answer("Всі записи\n" + history)


@router.message(Command("send_test"))
async def send(msg: Message, bot: Bot):
    user_id = 245677373
    await bot.send_chat_action(user_id, "typing")  # Використовуйте "typing"
    await bot.send_message(user_id, "SussyBaka")


@router.message(Command("users"), StateFilter(*[states.AdminStates.admin, states.AdminStates.new_date]))
async def get_alll_users(msg: Message):
    user_list = await db.get_all_users()
    await msg.answer("Список користувачів\n" + user_list)


@router.message(Command("usr_cancel"), StateFilter(*[states.AdminStates.admin, states.AdminStates.new_date]))
async def cancel_buffer(msg: Message, state: FSMContext):
    await msg.answer("Введіть ID запису, який хочете відмінити")
    await state.set_state(states.AdminStates.on_delete)


@router.message(states.AdminStates.on_delete)
async def cancel_record(msg: Message, state: FSMContext, bot: Bot):
    tgid = await db.get_tgid_by_recordsid(msg.text)
    record_id = await db.update_record_canceld(msg.text)
    if record_id is True:
        await msg.answer("Запис видалено успішно")
        await bot.send_chat_action(tgid, "typing")  # Використовуйте "typing"
        await bot.send_message(tgid, "Ваш запис видалено адміністратором")
    if record_id is False:
        await msg.answer("Запису не існує")
    await state.set_state(states.AdminStates.admin)

@router.message(Command("exit"), StateFilter(*[states.AdminStates.admin, states.AdminStates.new_date,states.AdminStates.get_records_id, states.AdminStates.on_delete]))
async def exit_admin(msg: Message, state: FSMContext):
    await msg.answer("Вихід з режиму адміністратора")
    await state.clear()
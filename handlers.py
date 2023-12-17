from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
import db

router = Router()

@router.message(Command("start"))
async def start_handler(msg: Message):
    await db.cmd_start_db(msg.from_user.id)
    await msg.answer("Привіт! Вітаємо в Poggers Cars!")

@router.message(Command("show"))
async def show_handler(msg: Message):
    await msg.answer("Вільні записи на")


@router.message(Command("services"))
async def services_handler(msg: Message):
    services_data = await db.cmd_show_service()
    await msg.answer(services_data)


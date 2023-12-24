import asyncio
import logging
import db

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

import config
from handlers import router


async def on_startup(_):
    await db.db_start()
    print("db launched")


async def main():
    bot = Bot(token=config.BOT_TOKEN, parse_mode=None)
    dp = Dispatcher(storage=MemoryStorage(), bot=bot)
    dp.include_router(router)

    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types(), on_startup=on_startup)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(main())

from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware, Bot
from aiogram.dispatcher.flags import get_flag
from aiogram.types import Message
from collections import defaultdict
from cachetools import TTLCache


class ThrottlingMiddleware(BaseMiddleware):
    caches = defaultdict(lambda: TTLCache(maxsize=10_000, ttl=2))

    def __init__(self, bot: Bot):
        self.bot = bot
        super().__init__()

    async def __call__(
        self,
        handler: Callable[[Message, Dict[str, Any]], Awaitable[Any]],
        event: Message,
        data: Dict[str, Any],
    ) -> Any:
        throttling_key = get_flag(data, "throttling_key")
        if await self.delete_if_throttled(throttling_key, event):
            return
        return await handler(event, data)

    async def delete_if_throttled(self, throttling_key, event):
        if throttling_key is not None and event.chat.id in self.caches[throttling_key]:
            await self.bot.delete_message(
                chat_id=event.chat.id, message_id=event.message_id
            )
            return True
        else:
            self.caches[throttling_key][event.chat.id] = None
            return False

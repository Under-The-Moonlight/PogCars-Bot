from typing import Union, Dict, Any
from datetime import datetime, timedelta
from aiogram.filters import BaseFilter
from aiogram.types import Message
import re
from aiogram import types
from datetime import datetime
import db


class DateFilter(BaseFilter):
    def __init__(self, date_is_correct: bool):
        self.date_is_correct = date_is_correct

    async def __call__(self, obj: Message) -> bool:  # [3]
        pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}"
        match = re.match(pattern, obj.text)
        if match:
            try:
                # Перетворення тексту в часовий об'єкт
                message_time = datetime.strptime(match.group(), '%Y-%m-%d %H:%M')
                # Порівняння з поточним часом
                return message_time > datetime.now()
            except ValueError:
                # У разі невалідного часу
                return False
        return False


class ServiceFilter(BaseFilter):
    def __init__(self, service_correct: bool):
        self.service_correct = service_correct

    async def __call__(self, obj: Message) -> bool:
        trans = obj.text
        match = await db.get_service_name(trans)
        if match is not None:
            return True
        else:
            return False


class DateFilter(BaseFilter):
    def __init__(self, date_is_correct: bool):
        self.date_is_correct = date_is_correct

    async def __call__(self, obj: Message) -> bool:  # [3]
        pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}"
        match = re.match(pattern, obj.text)
        if match:
            try:
                # Перетворення тексту в часовий об'єкт
                message_time = datetime.strptime(match.group(), '%Y-%m-%d %H:%M')
                # Порівняння з поточним часом
                return message_time > datetime.now()
            except ValueError:
                # У разі невалідного часу
                return False
        return False


class DateFilterCorr(BaseFilter):
    def __init__(self, date_is_correct: bool):
        self.date_is_correct = date_is_correct

    async def __call__(self, obj: Message) -> bool:
        pattern = r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}"
        return bool(re.match(pattern, obj.text))

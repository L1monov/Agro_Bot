from aiogram.filters import Filter
from aiogram.types import CallbackQuery


class ContainsSubstringFilter(Filter):
    def __init__(self, substring: str):
        self.substring = substring

    async def __call__(self, query: CallbackQuery) -> bool:
        return self.substring in query.data
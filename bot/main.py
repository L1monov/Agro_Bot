
import asyncio
import logging
from datetime import datetime

from aiogram import Bot, Dispatcher, BaseMiddleware, types
from aiogram.fsm.storage.memory import MemoryStorage

from config import BOT_TOKEN
from data.database import AsyncDataBase
from handlers import main_handler, main_commands, admin_handlers
from callbacks import callbacks
from payments import payments_handlers

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

db = AsyncDataBase()


class LoggingMiddleware(BaseMiddleware):
    """Логирование входящих сообщений от пользователей."""
    async def __call__(self, handler, event, data):
        if isinstance(event, types.Message):
            text = event.text or ''
            await db.log_message(
                message_id=event.message_id,
                user_id=event.from_user.id,
                text=text,
                sender='user',
                timestamp=event.date or datetime.utcnow()
            )
        return await handler(event, data)


class LoggingBot(Bot):
    """Бот с логированием исходящих сообщений в БД."""
    async def send_message(self, chat_id, text, **kwargs):
        # Отправляем сообщение и логируем его в БД
        msg = await super().send_message(chat_id, text, **kwargs)
        await db.log_message(
            message_id=msg.message_id,
            user_id=msg.chat.id,
            text=msg.text or '',
            sender='bot',
            timestamp=msg.date or datetime.utcnow()
        )
        return msg

    async def answer(self, *args, **kwargs):  # type: ignore
        # Логика для message.answer
        return await self.send_message(*args, **kwargs)

    async def reply(self, *args, **kwargs):  # type: ignore
        # Логика для message.reply
        return await self.send_message(*args, **kwargs)


async def run_bot():
    """Инициализация и запуск бота."""
    # 1) Инициализация базы данных
    await db.init()

    # 2) Создаем экземпляр бота (монки-патч через методы класса LoggingBot)
    bot = LoggingBot(token=BOT_TOKEN)

    # 3) Настройка диспетчера и FSM-хранилища
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # 4) Регистрируем middleware для входящих сообщений
    dp.message.middleware(LoggingMiddleware())

    # 5) Подключаем роутеры
    dp.include_routers(
        main_handler.router,
        main_commands.router,
        callbacks.router,
        payments_handlers.router,
        admin_handlers.router,
    )

    # 6) Запуск polling и удаление webhook
    await bot.delete_webhook(drop_pending_updates=True)
    logger.info("Bot started polling...")
    await dp.start_polling(bot)


if __name__ == '__main__':
    try:
        asyncio.run(run_bot())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped.")
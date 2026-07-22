import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.client.session.aiohttp import AiohttpSession
from config import BOT_TOKEN
from database import init_db
from handlers import router

logging.basicConfig(level=logging.INFO)


async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="admin", description="⚙️ Админ-панель"),
        BotCommand(command="blacklist", description="👥 Управление чёрным списком"),
    ]
    await bot.set_my_commands(commands)


async def main():
    await init_db()

    session = AiohttpSession(timeout=120)
    bot = Bot(token=BOT_TOKEN, session=session)

    await set_commands(bot)

    dp = Dispatcher()
    dp.include_router(router)

    print('✅ Бот KLAN KAIF запущен!')
    print('📝 Напиши /start в Telegram')

    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
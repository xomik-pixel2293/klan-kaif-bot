import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import asyncio
import logging
import threading
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.client.session.aiohttp import AiohttpSession
from flask import Flask
from config import BOT_TOKEN, ADMIN_IDS
from database import init_db, get_admin_ids

logging.basicConfig(level=logging.INFO)

print("🔍 ADMIN_IDS from env:", os.getenv('ADMIN_IDS'))

web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return "✅ Бот KLAN KAIF работает!", 200

@web_app.route('/ping')
def ping():
    return "pong", 200

def run_web():
    web_app.run(host='0.0.0.0', port=10000, debug=False, use_reloader=False)

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="admin", description="⚙️ Админ-панель"),
        BotCommand(command="blacklist", description="👥 Управление чёрным списком"),
    ]
    await bot.set_my_commands(commands)

async def main():
    await init_db()
    
    # Загружаем админов из БД в глобальный список
    db_admins = await get_admin_ids()
    for admin_id in db_admins:
        if admin_id not in ADMIN_IDS:
            ADMIN_IDS.append(admin_id)
    print(f"👑 Админов загружено: {len(ADMIN_IDS)}")
    
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    print("🌐 Веб-сервер запущен на порту 10000")

    session = AiohttpSession(timeout=120)
    bot = Bot(token=BOT_TOKEN, session=session)

    await set_commands(bot)

    from handlers.scheduler import start_scheduler
    await start_scheduler(bot)

    dp = Dispatcher()
    dp.include_router(router)

    print('✅ Бот KLAN KAIF запущен!')
    print('📝 Напиши /start в Telegram')
    print('🔗 Health check: https://klan-kaif-bot-1.onrender.com')

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

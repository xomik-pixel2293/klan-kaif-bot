import asyncio
import logging
import threading
import os
print("🔍 ADMIN_IDS from env:", os.getenv('ADMIN_IDS'))
from aiogram import Bot, Dispatcher
from aiogram.types import BotCommand
from aiogram.client.session.aiohttp import AiohttpSession
from flask import Flask
from config import BOT_TOKEN
from database import init_db
from handlers import router

logging.basicConfig(level=logging.INFO)

# ============================================================
# 🌐 ВЕБ-СЕРВЕР ДЛЯ RENDER (ЧТОБЫ НЕ ЗАСЫПАЛ)
# ============================================================

web_app = Flask(__name__)

@web_app.route('/')
def health_check():
    return "✅ Бот KLAN KAIF работает!", 200

@web_app.route('/ping')
def ping():
    return "pong", 200

def run_web():
    """Запуск веб-сервера на порту 10000 (ожидает Render)"""
    web_app.run(host='0.0.0.0', port=10000, debug=False, use_reloader=False)

# ============================================================
# 🤖 КОМАНДЫ БОТА
# ============================================================

async def set_commands(bot: Bot):
    commands = [
        BotCommand(command="start", description="🏠 Главное меню"),
        BotCommand(command="admin", description="⚙️ Админ-панель"),
        BotCommand(command="blacklist", description="👥 Управление чёрным списком"),
    ]
    await bot.set_my_commands(commands)

# ============================================================
# 🚀 ЗАПУСК
# ============================================================

async def main():
    # Инициализация базы данных
    await init_db()
    
    # Запуск веб-сервера в отдельном потоке (для Render)
    web_thread = threading.Thread(target=run_web, daemon=True)
    web_thread.start()
    print("🌐 Веб-сервер запущен на порту 10000")

    # Настройка и запуск бота
    session = AiohttpSession(timeout=120)
    bot = Bot(token=BOT_TOKEN, session=session)

    await set_commands(bot)

    dp = Dispatcher()
    dp.include_router(router)

    print('✅ Бот KLAN KAIF запущен!')
    print('📝 Напиши /start в Telegram')
    print(f"🔗 Health check: https://klan-kaif-bot.onrender.com")

    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())

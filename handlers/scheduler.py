import json
from aiogram import Router
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from database import get_old_pending_applications

router = Router()


async def send_reminders(bot):
    apps = await get_old_pending_applications()
    
    if not apps:
        print("🔔 Нет старых заявок для напоминания")
        return
    
    clans_apps = {}
    for app in apps:
        clan_id = app[3]
        if clan_id not in clans_apps:
            clans_apps[clan_id] = {
                'name': app[13],
                'leader_id': app[14],
                'leader_username': app[15],
                'leader_name': app[16],
                'deputy_id': app[17],
                'deputy_username': app[18],
                'deputy_name': app[19],
                'apps': []
            }
        clans_apps[clan_id]['apps'].append(app)
    
    for clan_id, data in clans_apps.items():
        count = len(data['apps'])
        
        text = f"⏰ НАПОМИНАНИЕ!\n\n"
        text += f"📋 В клане {data['name']} {count} заявок ждут решения более 24 часов:\n\n"
        
        for i, app in enumerate(data['apps'][:5], 1):
            answers = json.loads(app[4])
            text += f"{i}. @{app[2]} — {answers.get('name', 'Без имени')}\n"
            text += f"   📅 {app[10]}\n"
        
        if count > 5:
            text += f"\n... и ещё {count - 5} заявок"
        
        text += f"\n\n📌 Перейдите в раздел «Заявки в мой клан» для обработки."
        
        keyboard = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='📋 Перейти к заявкам', callback_data='my_clan_applications')]
        ])
        
        if data['leader_id']:
            try:
                await bot.send_message(data['leader_id'], text, reply_markup=keyboard)
            except Exception as e:
                print(f"Ошибка отправки лидеру {data['leader_id']}: {e}")
        
        if data['deputy_id']:
            try:
                await bot.send_message(data['deputy_id'], text, reply_markup=keyboard)
            except Exception as e:
                print(f"Ошибка отправки заму {data['deputy_id']}: {e}")


async def start_scheduler(bot):
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_reminders,
        CronTrigger(hour=12, minute=0),
        args=[bot],
        id='daily_reminder',
        replace_existing=True
    )
    scheduler.start()
    print("⏰ Планировщик напоминаний запущен! (каждый день в 12:00)")
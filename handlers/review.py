import json
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from database import (
    get_clan_by_user, get_application_by_id,
    get_clan_applications, update_application_status,
    get_clan_link, set_clan_link, get_clan
)
from keyboards import (
    back_button, contact_button, contact_menu, contact_with_link,
    review_buttons, after_apply_buttons
)
from .start import ApplicationForm

router = Router()


# ============================================================
# 📋 ЗАЯВКИ В МОЙ КЛАН (ДЛЯ ЛИДЕРОВ/ЗАМОВ)
# ============================================================

@router.callback_query(F.data == 'my_clan_applications')
async def my_clan_applications(callback: CallbackQuery):
    await callback.answer()
    clan = await get_clan_by_user(callback.from_user.id)
    if not clan:
        return

    clan_id, name = clan[0], clan[1]
    apps = await get_clan_applications(clan_id)

    if not apps:
        await callback.message.edit_text(
            f'📋 ЗАЯВКИ В КЛАН {name}:\n\nПока нет ни одной заявки.',
            reply_markup=back_button('back_to_main')
        )
        return

    status_emoji = {
        'pending': '⏳ На рассмотрении',
        'accepted': '✅ Принято',
        'rejected': '❌ Отклонено',
        'revoked': '⚠️ Отозвано'
    }

    text = f'📋 ЗАЯВКИ В КЛАН {name}:\n\n📌 Нажми на заявку, чтобы принять или отклонить.\n\n'
    
    buttons = []
    for app in apps:
        app_id, user_id, username, clan_id_db, answers_json, photo_old, photo_new, has_photos, chat_id, status, created_at, reviewed_by, reviewed_at, clan_name = app
        answers = json.loads(answers_json)
        
        if isinstance(created_at, datetime):
            date_str = created_at.strftime("%d.%m, %H:%M")
        else:
            date_str = created_at[:16] if created_at else ""
        
        status_text = status_emoji.get(status, status)
        name_display = answers.get('name', 'Без имени')
        
        buttons.append([
            InlineKeyboardButton(
                text=f"#{app_id} — @{username} ({name_display}) — {status_text}",
                callback_data=f"view_app_{app_id}"
            )
        ])
    
    buttons.append([InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_main')])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data.startswith('view_app_'))
async def view_application_detail(callback: CallbackQuery):
    await callback.answer()
    
    app_id = int(callback.data.split('_')[2])
    app = await get_application_by_id(app_id)
    
    if not app:
        await callback.message.answer('❌ Заявка не найдена')
        return
    
    app_id, user_id, username, clan_id, answers_json, photo_old, photo_new, has_photos, chat_id, status, created_at, reviewed_by, reviewed_at, clan_name = app
    answers = json.loads(answers_json)
    
    if isinstance(created_at, datetime):
        date_str = created_at.strftime("%d.%m.%Y, %H:%M")
    else:
        date_str = created_at[:16] if created_at else ""
    
    status_emoji = {
        'pending': '⏳ На рассмотрении',
        'accepted': '✅ Принято',
        'rejected': '❌ Отклонено',
        'revoked': '⚠️ Отозвано'
    }
    
    text = f"📋 ЗАЯВКА #{app_id}\n\n"
    text += f"Кандидат: @{username} (ID: {user_id})\n"
    text += f"Клан: {clan_name}\n"
    text += f"Статус: {status_emoji.get(status, status)}\n"
    text += f"Дата: {date_str}\n"
    text += f"📸 Фото: {has_photos}\n\n"
    text += "📝 АНКЕТА:\n"
    text += f"1. Имя: {answers.get('name', '')}\n"
    text += f"2. Возраст: {answers.get('age', '')}\n"
    text += f"3. Ник: {answers.get('nickname', '')}\n"
    text += f"4. ID: {answers.get('id', '')}\n"
    text += f"5. Часовой пояс (МСК): {answers.get('timezone', '')}\n"
    
    buttons = []
    
    if status == 'pending':
        buttons.append([
            InlineKeyboardButton(text='✅ Принять', callback_data=f'accept_{app_id}'),
            InlineKeyboardButton(text='❌ Отклонить', callback_data=f'reject_{app_id}')
        ])
        buttons.append([InlineKeyboardButton(text='📩 Связаться', callback_data=f'contact_{app_id}')])
    elif status == 'accepted':
        buttons.append([InlineKeyboardButton(text='📩 Связаться', callback_data=f'contact_{app_id}')])
        buttons.append([InlineKeyboardButton(text='⚠️ Уже принята', callback_data='noop')])
    else:
        buttons.append([InlineKeyboardButton(text='⚠️ Заявка обработана', callback_data='noop')])
    
    buttons.append([InlineKeyboardButton(text='🔙 Назад к списку', callback_data='my_clan_applications')])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    
    if photo_old or photo_new:
        await callback.message.delete()
        
        media = []
        if photo_old:
            media.append(InputMediaPhoto(media=photo_old, caption=text))
        if photo_new:
            if photo_old:
                media.append(InputMediaPhoto(media=photo_new))
            else:
                media.append(InputMediaPhoto(media=photo_new, caption=text))
        
        await callback.message.answer_media_group(media=media)
        await callback.message.answer("📌 Действия с заявкой:", reply_markup=keyboard)
    else:
        await callback.message.edit_text(text, reply_markup=keyboard)


@router.callback_query(F.data == 'noop')
async def noop(callback: CallbackQuery):
    await callback.answer('⚠️ Эта заявка уже обработана')


# ============================================================
# ✅ ПРИНЯТЬ ЗАЯВКУ
# ============================================================

@router.callback_query(F.data.startswith('accept_'))
async def accept_application(callback: CallbackQuery):
    await callback.answer()
    app_id = int(callback.data.split('_')[1])
    clan = await get_clan_by_user(callback.from_user.id)
    if not clan:
        await callback.message.answer('⛔ У вас нет прав на это действие')
        return

    await update_application_status(app_id, 'accepted', callback.from_user.id)
    await callback.message.edit_reply_markup(reply_markup=None)

    await callback.message.answer(
        f'🎉 Заявка #{app_id} ПРИНЯТА!\n\n'
        f'Теперь вы можете отправить кандидату ссылку на вступление.',
        reply_markup=contact_button(app_id)
    )

    app = await get_application_by_id(app_id)
    if app:
        try:
            await callback.bot.send_message(
                app[1],
                f'🎉 ПОЗДРАВЛЯЕМ!\nВаша заявка в клан {app[12]} ПРИНЯТА!\n'
                f'Ожидайте сообщение от лидера/зама.'
            )
        except:
            pass


# ============================================================
# ❌ ОТКЛОНИТЬ ЗАЯВКУ
# ============================================================

@router.callback_query(F.data.startswith('reject_'))
async def reject_application(callback: CallbackQuery):
    await callback.answer()
    app_id = int(callback.data.split('_')[1])
    clan = await get_clan_by_user(callback.from_user.id)
    if not clan:
        await callback.message.answer('⛔ У вас нет прав на это действие')
        return

    await update_application_status(app_id, 'rejected', callback.from_user.id)
    await callback.message.edit_reply_markup(reply_markup=None)
    await callback.message.answer('❌ Заявка ОТКЛОНЕНА.')

    app = await get_application_by_id(app_id)
    if app:
        try:
            await callback.bot.send_message(
                app[1],
                f'😔 К сожалению, ваша заявка в клан {app[12]} отклонена.\nВы можете подать заявку в другой клан или попробовать позже.'
            )
        except:
            pass


# ============================================================
# 💬 СВЯЗАТЬСЯ С КАНДИДАТОМ
# ============================================================

@router.callback_query(F.data.startswith('contact_'))
async def contact_application(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    app_id = int(callback.data.split('_')[1])

    clan = await get_clan_by_user(callback.from_user.id)
    if not clan:
        await callback.message.answer('⛔ У вас нет прав на это действие')
        return

    app = await get_application_by_id(app_id)
    if not app:
        await callback.message.answer('❌ Заявка не найдена')
        return

    await state.update_data(contact_app_id=app_id)

    clan_id, clan_name = clan[0], clan[1]

    link = await get_clan_link(clan_id)

    if link:
        await callback.message.answer(
            f'📩 Сообщение кандидату @{app[2]}\n\n'
            f'Текущая ссылка на чат: {link}\n\n'
            f'Что хотите сделать?',
            reply_markup=contact_with_link(app_id, link)
        )
    else:
        await callback.message.answer(
            f'📩 Сообщение кандидату @{app[2]}\n\n'
            f'У клана ещё нет ссылки на чат.\n'
            f'Сначала добавьте её.',
            reply_markup=contact_menu(app_id)
        )


# ============================================================
# 📤 ОТПРАВИТЬ ССЫЛКУ
# ============================================================

@router.callback_query(F.data.startswith('send_link_'))
async def send_link(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    app_id = int(callback.data.split('_')[2])
    
    clan = await get_clan_by_user(callback.from_user.id)
    if not clan:
        await callback.message.answer('⛔ У вас нет прав на это действие')
        return
    
    app = await get_application_by_id(app_id)
    if not app:
        await callback.message.answer('❌ Заявка не найдена')
        return
    
    if len(clan) >= 9:
        clan_id = clan[0]
        clan_name = clan[1]
        leader_id = clan[3]
        leader_username = clan[4]
        leader_name = clan[5]
        deputy_id = clan[6]
        deputy_username = clan[7]
        deputy_name = clan[8]
    else:
        clan_id = clan[0]
        clan_name = clan[1]
        leader_id = clan[2] if len(clan) > 2 else None
        leader_username = clan[3] if len(clan) > 3 else None
        leader_name = clan[4] if len(clan) > 4 else None
        deputy_id = clan[5] if len(clan) > 5 else None
        deputy_username = clan[6] if len(clan) > 6 else None
        deputy_name = clan[7] if len(clan) > 7 else None
    
    link = await get_clan_link(clan_id)
    if not link:
        await callback.message.answer(
            '❌ Ссылка на чат не найдена.\n'
            'Сначала добавьте её через «🔗 Добавить ссылку».'
        )
        return
    
    clan_ids = {
        'KAIF': '51656781871',
        'KAIF ESPORTS': '51600572333',
        'KAIF METRO': '51954255028',
        'NA KAIFE': '51768659282',
        'KAIF TDM': '6409373909',
    }
    clan_id_game = clan_ids.get(clan_name, 'не указан')
    
    if callback.from_user.id == leader_id:
        sender = f"👑 Лидер клана {clan_name} — {leader_name}"
    elif callback.from_user.id == deputy_id:
        sender = f"👤 Зам клана {clan_name} — {deputy_name}"
    else:
        sender = f"Администрация {clan_name}"
    
    message_text = (
        f'🎉 ПОЗДРАВЛЯЕМ!\n\n'
        f'Вы прошли отбор и официально приняты в клан {clan_name}!\n\n'
        f'Добро пожаловать в нашу дружную команду! Мы рады, что ты с нами. Впереди — совместные игры, турниры, тренировки и новые достижения.\n\n'
        f'🔥 Сделай ник с припиской {clan_name.split()[0] if " " in clan_name else clan_name}\n\n'
        f'📌 Ссылка на чат клана: {link}\n\n'
        f'🆔 ID лидера для подачи заявки в игре: {clan_id_game}\n\n'
        f'📩 Отправил: {sender}\n\n'
        f'С уважением, администрация {clan_name} ❤️'
    )
    
    try:
        await callback.bot.send_message(
            app[1],
            message_text
        )
        await callback.message.answer(f'✅ Ссылка отправлена кандидату @{app[2]}!')
    except Exception as e:
        await callback.message.answer(f'❌ Не удалось отправить сообщение. Ошибка: {e}')
    
    await state.clear()


# ============================================================
# ✏️ НАПИСАТЬ СООБЩЕНИЕ (ДЛЯ ЛИДЕРОВ/ЗАМОВ)
# ============================================================

@router.callback_query(F.data.startswith('send_message_'))
async def send_custom_message(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    app_id = int(callback.data.split('_')[2])

    clan = await get_clan_by_user(callback.from_user.id)
    if not clan:
        await callback.message.answer('⛔ У вас нет прав на это действие')
        return

    app = await get_application_by_id(app_id)
    if not app:
        await callback.message.answer('❌ Заявка не найдена')
        return

    await state.update_data(send_app_id=app_id)
    await state.set_state(ApplicationForm.waiting_contact_message)
    await state.update_data(link_action='message')

    await callback.message.edit_text(
        f'✏️ Напишите сообщение для кандидата @{app[2]}:\n\n'
        f'Оно будет отправлено сразу после того, как вы его напишете.\n\n'
        f'Например: "Привет! Приглашаю тебя в клан!"',
        reply_markup=back_button('back_to_main')
    )


# ============================================================
# 🔗 ДОБАВИТЬ ССЫЛКУ
# ============================================================

@router.callback_query(F.data.startswith('add_link_'))
async def add_link(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    app_id = int(callback.data.split('_')[2])

    await state.update_data(contact_app_id=app_id)
    await state.set_state(ApplicationForm.waiting_contact_message)
    await state.update_data(link_action='add')

    await callback.message.edit_text(
        '✏️ Введите ссылку на чат клана:\n'
        'Например: https://t.me/joinchat/xxxxx\n\n'
        'Или отправьте @username чата.',
        reply_markup=back_button('back_to_main')
    )


# ============================================================
# ✏️ ИЗМЕНИТЬ ССЫЛКУ
# ============================================================

@router.callback_query(F.data.startswith('edit_link_'))
async def edit_link(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    app_id = int(callback.data.split('_')[2])

    await state.update_data(contact_app_id=app_id)
    await state.set_state(ApplicationForm.waiting_contact_message)
    await state.update_data(link_action='edit')

    await callback.message.edit_text(
        '✏️ Введите новую ссылку на чат клана:\n'
        'Например: https://t.me/joinchat/xxxxx\n\n'
        'Или отправьте @username чата.',
        reply_markup=back_button('back_to_main')
    )


# ============================================================
# 📨 ПОЛУЧЕНИЕ СООБЩЕНИЯ
# ============================================================

@router.message(ApplicationForm.waiting_contact_message)
async def handle_contact_message(message: Message, state: FSMContext):
    data = await state.get_data()
    app_id = data.get('contact_app_id') or data.get('send_app_id')
    link_action = data.get('link_action')

    if not app_id:
        await message.answer('❌ Ошибка. Попробуйте снова.', reply_markup=main_menu())
        await state.clear()
        return

    app = await get_application_by_id(app_id)
    if not app:
        await message.answer('❌ Заявка не найдена')
        await state.clear()
        return

    if link_action in ['add', 'edit']:
        clan_id = app[3]
        link = message.text.strip()

        print(f"🔍 СОХРАНЯЕМ ССЫЛКУ: clan_id={clan_id}, link={link}")

        await set_clan_link(clan_id, link)

        action_text = 'добавлена' if link_action == 'add' else 'обновлена'
        await message.answer(f'✅ Ссылка на чат клана {action_text}!\n\nТекущая ссылка: {link}')
        await state.clear()
        return

    if link_action == 'message':
        try:
            await message.bot.send_message(
                app[1],
                f'📩 Сообщение от лидера/зама клана {app[12]}:\n\n{message.text}'
            )
            await message.answer(f'✅ Сообщение отправлено кандидату @{app[2]}!')
        except Exception as e:
            await message.answer(f'❌ Не удалось отправить сообщение. Ошибка: {e}')
        
        await state.clear()
        return

    try:
        await message.bot.send_message(
            app[1],
            f'📩 Сообщение от лидера клана {app[12]}:\n\n{message.text}'
        )
        await message.answer(f'✅ Сообщение отправлено кандидату @{app[2]}!')
    except Exception as e:
        await message.answer(f'❌ Не удалось отправить сообщение. Ошибка: {e}')

    await state.clear()


# ============================================================
# 📤 ОТПРАВИТЬ СООБЩЕНИЕ (СТАРЫЙ ОБРАБОТЧИК)
# ============================================================

@router.callback_query(F.data.startswith('send_message_'))
async def send_message(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    app_id = int(callback.data.split('_')[2])

    clan = await get_clan_by_user(callback.from_user.id)
    if not clan:
        await callback.message.answer('⛔ У вас нет прав на это действие')
        return

    app = await get_application_by_id(app_id)
    if not app:
        await callback.message.answer('❌ Заявка не найдена')
        return

    if len(clan) >= 9:
        clan_id = clan[0]
        clan_name = clan[1]
        leader_id = clan[3]
        leader_username = clan[4]
        leader_name = clan[5]
        deputy_id = clan[6]
        deputy_username = clan[7]
        deputy_name = clan[8]
    else:
        clan_id = clan[0]
        clan_name = clan[1]
        leader_id = clan[2] if len(clan) > 2 else None
        leader_username = clan[3] if len(clan) > 3 else None
        leader_name = clan[4] if len(clan) > 4 else None
        deputy_id = clan[5] if len(clan) > 5 else None
        deputy_username = clan[6] if len(clan) > 6 else None
        deputy_name = clan[7] if len(clan) > 7 else None
    
    link = await get_clan_link(clan_id)

    if not link:
        await callback.message.answer('❌ Ссылка на чат не найдена. Сначала добавьте её.')
        return

    clan_ids = {
        'KAIF': '51656781871',
        'KAIF ESPORTS': '51600572333',
        'KAIF METRO': '51954255028',
        'NA KAIFE': '51768659282',
        'KAIF TDM': '6409373909',
    }
    clan_id_game = clan_ids.get(clan_name, 'не указан')

    if callback.from_user.id == leader_id:
        sender = f"👑 Лидер клана {clan_name} — {leader_name}"
    elif callback.from_user.id == deputy_id:
        sender = f"👤 Зам клана {clan_name} — {deputy_name}"
    else:
        sender = f"Администрация {clan_name}"

    message_text = (
        f'🎉 ПОЗДРАВЛЯЕМ!\n\n'
        f'Вы прошли отбор и официально приняты в клан {clan_name}!\n\n'
        f'Добро пожаловать в нашу дружную команду! Мы рады, что ты с нами. Впереди — совместные игры, турниры, тренировки и новые достижения.\n\n'
        f'🔥 Сделай ник с припиской {clan_name.split()[0] if " " in clan_name else clan_name}\n\n'
        f'📌 Ссылка на чат клана: {link}\n\n'
        f'🆔 ID лидера для подачи заявки в игре: {clan_id_game}\n\n'
        f'📩 Отправил: {sender}\n\n'
        f'С уважением, администрация {clan_name} ❤️'
    )

    try:
        await callback.bot.send_message(
            app[1],
            message_text
        )
        await callback.message.answer(f'✅ Сообщение отправлено кандидату @{app[2]}!')
    except Exception as e:
        await callback.message.answer(f'❌ Не удалось отправить сообщение. Ошибка: {e}')

    await state.clear()
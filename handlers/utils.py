import json
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery

from database import get_clans, get_blacklist
from keyboards import back_button

router = Router()


# ============================================================
# ℹ️ О КЛАНАХ
# ============================================================

@router.callback_query(F.data == 'about_clans')
async def about_clans(callback: CallbackQuery):
    await callback.answer()
    clans = await get_clans()
    text = '🏆 KLAN KAIF:\n\n'
    text += '📌 ОБЩИЕ ТРЕБОВАНИЯ ДЛЯ ВСЕХ:\n• Адекватность\n• Актив в беседе и игре\n• Смена ника с припиской KAIF\n• Участие в мероприятиях клана\n• Для новичков — неделя на показ активности\n\n'

    clan_data = {
        1: {'emoji': '🔴', 'name': 'KAIF — основной состав',
            'requirements': ['• Возраст: 18+', '• K/D: 8+', '• Коллекция: 50+', '• Аккаунт: 60+', '• SMS: 150 в неделю',
                             '• Energy: 2500 в неделю', '• Смена ника: 3 дня']},
        2: {'emoji': '🟡', 'name': 'NA KAIFE — академия',
            'requirements': ['• Возраст: 16+', '• K/D: M 6 на 100, W 5 на 100', '• Аккаунт: 50+', '• SMS: 300 в неделю',
                             '• Energy: 1500 в неделю', '• Смена ника: 7 дней']},
        3: {'emoji': '🟢', 'name': 'KAIF METRO',
            'requirements': ['• Возраст: 16+', '• K/D: 1.5+', '• Вынос: 1.5м', '• SMS: 300 в неделю',
                             '• Energy: 2000 в неделю', '• Смена ника: 7 дней']},
        4: {'emoji': '🟣', 'name': 'KAIF ESPORTS — турнирный состав',
            'requirements': ['• Возраст: 16+', '• SMS: 150 в неделю', '• Energy: 2000 в неделю', '• Смена ника: 3 дня',
                             '• Ответственность, дисциплина', '• Опыт турниров и праков']},
        5: {'emoji': '🟠', 'name': 'KAIF TDM',
            'requirements': ['• Возраст: 16+', '• SMS: 300 в неделю',
                             '• Смена ника: 3 дня', '• Адекватность', '• Активность в чате']},
    }

    for clan in clans:
        if len(clan) >= 8:
            clan_id, name, leader_id, leader_username, leader_name, deputy_id, deputy_username, deputy_name = clan[:8]
        else:
            continue
            
        info = clan_data.get(clan_id, {})
        text += f'{info.get("emoji", "🔵")} {info.get("name", name)}\n'
        text += f'   👑 Лидер: {leader_name if leader_name else "❌ не назначен"}\n'
        text += f'   👤 Зам: {deputy_name if deputy_name else "❌ не назначен"}\n'
        text += f'   📋 Требования:\n'
        for req in info.get('requirements', []):
            text += f'   {req}\n'
        text += '\n─────────────────────\n\n'

    await callback.message.edit_text(text, reply_markup=back_button('back_to_main'))


# ============================================================
# 📞 КОНТАКТЫ
# ============================================================

@router.callback_query(F.data == 'contacts')
async def contacts(callback: CallbackQuery):
    await callback.answer()
    text = '📞 КОНТАКТЫ:\n\n👨‍💼 Менеджеры:\n   Xoma (@Xoma9991)\n   Катя (@Vibnot)'
    await callback.message.edit_text(text, reply_markup=back_button('back_to_main'))


# ============================================================
# 📋 КОПИРОВАТЬ ШАБЛОН
# ============================================================

@router.callback_query(F.data == 'copy_template')
async def copy_template(callback: CallbackQuery):
    await callback.answer()

    template = (
        'Имя: \n'
        'Возраст: \n'
        'Ник: \n'
        'ID: \n'
        'Часовой пояс (МСК): '
    )

    await callback.message.answer(template)


# ============================================================
# ⚠️ ЗАГЛУШКА
# ============================================================

@router.callback_query(F.data == 'noop')
async def noop(callback: CallbackQuery):
    await callback.answer('⚠️ Эта заявка уже обработана')


# ============================================================
# 📊 МОИ ЗАЯВКИ
# ============================================================

@router.callback_query(F.data == 'my_applications')
async def my_applications(callback: CallbackQuery):
    await callback.answer()
    apps = await get_user_applications(callback.from_user.id)
    if not apps:
        await callback.message.edit_text(
            '📊 У вас пока нет заявок.\nПодайте анкету через 📝 Подать анкету',
            reply_markup=back_button('back_to_main')
        )
        return

    status_emoji = {
        'pending': '⏳ На рассмотрении',
        'accepted': '✅ Принято',
        'rejected': '❌ Отклонено',
        'revoked': '⚠️ Отозвано'
    }

    text = '📊 ВАШИ ЗАЯВКИ:\n\n'
    buttons = []

    for app in apps:
        app_id, user_id, username, clan_id, answers_json, photo_old, photo_new, has_photos, chat_id, status, created_at, reviewed_by, reviewed_at, clan_name = app

        text += f'{status_emoji.get(status, status)} в клан {clan_name}\n'
        text += f'   От: {created_at[:10]}\n'
        text += f'   📸 {has_photos} фото\n'

        if status == 'pending':
            buttons.append(
                [InlineKeyboardButton(text=f'❌ Отозвать заявку #{app_id}', callback_data=f'revoke_{app_id}')])
        text += '\n'

    text += '💡 Если заявка не рассмотрена, вы можете её отозвать.'
    buttons.append([InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_main')])
    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)

    await callback.message.edit_text(text, reply_markup=keyboard)


# ============================================================
# ❌ ОТОЗВАТЬ ЗАЯВКУ
# ============================================================

@router.callback_query(F.data.startswith('revoke_'))
async def revoke_application_handler(callback: CallbackQuery):
    await callback.answer()
    app_id = int(callback.data.split('_')[1])
    await revoke_application(app_id)
    await callback.message.edit_text('⚠️ Заявка отозвана.', reply_markup=after_apply_buttons())
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from database import get_clans_with_status


# ============================================================
# 📌 ГЛАВНОЕ МЕНЮ
# ============================================================

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📝 Подать анкету', callback_data='apply')],
        [InlineKeyboardButton(text='📊 Мои заявки', callback_data='my_applications')],
        [InlineKeyboardButton(text='ℹ️ О кланах', callback_data='about_clans')],
        [InlineKeyboardButton(text='📞 Контакты', callback_data='contacts')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='exit_test_mode')],
    ])


def leader_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📋 Заявки в мой клан', callback_data='my_clan_applications')],
    ])


# ============================================================
# 🎯 ВЫБОР КЛАНА — ДИНАМИЧЕСКАЯ ВЕРСИЯ
# ============================================================

async def clan_choice():
    """Клавиатура выбора клана (только активные)"""
    try:
        clans = await get_clans_with_status()
    except Exception as e:
        print(f"❌ Ошибка получения кланов: {e}")
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='❌ Ошибка загрузки', callback_data='noop')],
            [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_main')],
        ])
    
    buttons = []
    emojis = {1: '🔴', 2: '🟡', 3: '🟢', 4: '🟣', 5: '🟠'}
    
    for clan_id, name, emoji, is_active in clans:
        if is_active:
            emoji = emojis.get(clan_id, '🔵')
            buttons.append([InlineKeyboardButton(
                text=f'{emoji} {name}',
                callback_data=f'clan_{clan_id}'
            )])
    
    if not buttons:
        buttons.append([InlineKeyboardButton(
            text='❌ Нет доступных кланов',
            callback_data='noop'
        )])
    
    buttons.append([InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_main')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def review_buttons(app_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text='✅ Принять', callback_data=f'accept_{app_id}'),
            InlineKeyboardButton(text='❌ Отклонить', callback_data=f'reject_{app_id}'),
        ],
    ])


def contact_button(app_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📩 Связаться с кандидатом', callback_data=f'contact_{app_id}')],
    ])


def photo_old_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📸 Отправить фото 1', callback_data='send_photo_old')],
    ])


def photo_new_button_with_skip():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📸 Отправить фото 2', callback_data='send_photo_new')],
        [InlineKeyboardButton(text='⏭️ Пропустить', callback_data='skip_photo')],
    ])


def after_apply_buttons():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📊 Мои заявки', callback_data='my_applications')],
        [InlineKeyboardButton(text='🔙 В главное меню', callback_data='back_to_main')],
    ])


def exit_test_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔙 Выйти из тестового режима', callback_data='exit_test_mode')],
    ])


def back_button(callback_data='back_to_main'):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔙 Назад', callback_data=callback_data)]
    ])


# ============================================================
# 👑 АДМИН-ПАНЕЛЬ
# ============================================================

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📊 Статистика', callback_data='admin_stats')],
        [InlineKeyboardButton(text='📤 Экспорт CSV', callback_data='admin_export')],
        [InlineKeyboardButton(text='👥 Чёрный список', callback_data='admin_blacklist')],
        [InlineKeyboardButton(text='👥 Управление руководителями', callback_data='admin_manage_roles')],
        [InlineKeyboardButton(text='🔄 Вкл/Выкл кланы', callback_data='admin_clan_status')],
        [InlineKeyboardButton(text='🏗️ Управление кланами', callback_data='admin_clan_management')],
        [InlineKeyboardButton(text='🧪 Тестовая анкета', callback_data='admin_test_application')],
        [InlineKeyboardButton(text='🗑 Очистить тестовые заявки', callback_data='admin_clear_test')],
        [InlineKeyboardButton(text='🧑‍💻 Стать кандидатом', callback_data='admin_become_candidate')],
        [InlineKeyboardButton(text='🔙 Выйти', callback_data='back_to_main')],
    ])


def manage_roles_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='➕ Назначить лидера', callback_data='role_assign_leader')],
        [InlineKeyboardButton(text='➕ Назначить зама', callback_data='role_assign_deputy')],
        [InlineKeyboardButton(text='🗑 Удалить лидера', callback_data='role_remove_leader')],
        [InlineKeyboardButton(text='🗑 Удалить зама', callback_data='role_remove_deputy')],
        [InlineKeyboardButton(text='📋 Список руководителей', callback_data='role_list')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_admin')],
    ])


def assign_choice_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📋 Выбрать из существующих', callback_data='assign_from_existing')],
        [InlineKeyboardButton(text='✏️ Ввести нового пользователя', callback_data='assign_from_new')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_admin')],
    ])


def select_existing_leader_buttons(leaders, role_type):
    buttons = []
    for leader in leaders:
        emoji = '👑' if leader['role'] == 'Лидер' else '👤'
        buttons.append([InlineKeyboardButton(
            text=f"{leader['name']} (@{leader['username']}) — {emoji} {leader['role']} {leader['clan']}",
            callback_data=f"select_existing_{leader['id']}_{leader['clan_id']}"
        )])
    buttons.append([InlineKeyboardButton(text='✏️ Ввести нового пользователя', callback_data='assign_from_new')])
    buttons.append([InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_admin')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def select_clan_for_role_buttons(clans, role_type, user_id, username, name):
    buttons = []
    emojis = {1: '🔴', 2: '🟡', 3: '🟢', 4: '🟣', 5: '🟠'}
    for clan in clans:
        clan_id, clan_name = clan[0], clan[1]
        emoji = emojis.get(clan_id, '🔵')
        buttons.append([InlineKeyboardButton(
            text=f"{emoji} {clan_name}",
            callback_data=f"assign_to_clan_{role_type}_{clan_id}_{user_id}_{username}_{name}"
        )])
    buttons.append([InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_admin')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def clan_choice_for_roles():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔴 KAIF', callback_data='role_clan_1')],
        [InlineKeyboardButton(text='🟡 NA KAIFE', callback_data='role_clan_2')],
        [InlineKeyboardButton(text='🟢 KAIF METRO', callback_data='role_clan_3')],
        [InlineKeyboardButton(text='🟣 KAIF ESPORTS', callback_data='role_clan_4')],
        [InlineKeyboardButton(text='🟠 TDM', callback_data='role_clan_5')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_admin')],
    ])


def cancel_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='❌ Отмена', callback_data='back_to_admin')],
    ])


def copy_template_button(template):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📋 Скопировать шаблон', callback_data='copy_template')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_main')],
    ])


# ============================================================
# 💬 СВЯЗАТЬСЯ (ССЫЛКИ)
# ============================================================

def contact_menu(app_id):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📤 Отправить ссылку', callback_data=f'send_link_{app_id}')],
        [InlineKeyboardButton(text='✏️ Написать сообщение', callback_data=f'send_message_{app_id}')],
        [InlineKeyboardButton(text='🔗 Добавить ссылку', callback_data=f'add_link_{app_id}')],
        [InlineKeyboardButton(text='✏️ Изменить ссылку', callback_data=f'edit_link_{app_id}')],
        [InlineKeyboardButton(text='🔙 Отмена', callback_data='back_to_main')],
    ])


def contact_with_link(app_id, link):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📤 Отправить ссылку', callback_data=f'send_link_{app_id}')],
        [InlineKeyboardButton(text='✏️ Написать сообщение', callback_data=f'send_message_{app_id}')],
        [InlineKeyboardButton(text='✏️ Изменить ссылку', callback_data=f'edit_link_{app_id}')],
        [InlineKeyboardButton(text='🔙 Отмена', callback_data='back_to_main')],
    ])


# ============================================================
# 🧪 ТЕСТОВАЯ АНКЕТА
# ============================================================

def test_application_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='✏️ Написать тестовую анкету', callback_data='write_test_application')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_admin')],
    ])


async def clan_choice_for_test():
    """Клавиатура выбора клана для тестовой анкеты (только активные)"""
    try:
        clans = await get_clans_with_status()
    except Exception as e:
        print(f"❌ Ошибка получения кланов: {e}")
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='❌ Ошибка загрузки', callback_data='noop')],
            [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_test')],
        ])
    
    buttons = []
    emojis = {1: '🔴', 2: '🟡', 3: '🟢', 4: '🟣', 5: '🟠'}
    
    for clan_id, name, emoji, is_active in clans:
        if is_active:
            emoji = emojis.get(clan_id, '🔵')
            buttons.append([InlineKeyboardButton(
                text=f'{emoji} {name}',
                callback_data=f'test_clan_{clan_id}'
            )])
    
    if not buttons:
        buttons.append([InlineKeyboardButton(
            text='❌ Нет доступных кланов',
            callback_data='noop'
        )])
    
    buttons.append([InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_test')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


# ============================================================
# 🔄 УПРАВЛЕНИЕ СТАТУСОМ КЛАНОВ (АДМИН)
# ============================================================

def admin_clan_status_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔴 KAIF', callback_data='admin_clan_status_1')],
        [InlineKeyboardButton(text='🟡 NA KAIFE', callback_data='admin_clan_status_2')],
        [InlineKeyboardButton(text='🟢 KAIF METRO', callback_data='admin_clan_status_3')],
        [InlineKeyboardButton(text='🟣 KAIF ESPORTS', callback_data='admin_clan_status_4')],
        [InlineKeyboardButton(text='🟠 TDM', callback_data='admin_clan_status_5')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_admin')],
    ])


def clan_toggle_button(clan_id: int, clan_name: str, is_active: bool):
    emojis = {1: '🔴', 2: '🟡', 3: '🟢', 4: '🟣', 5: '🟠'}
    emoji = emojis.get(clan_id, '🔵')
    status_text = "✅ ВКЛЮЧЁН" if is_active else "❌ ВЫКЛЮЧЁН"
    
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"🔄 {emoji} {clan_name}: {status_text}",
            callback_data=f'toggle_clan_{clan_id}'
        )],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='admin_clan_status')],
    ])


# ============================================================
# 🏗️ УПРАВЛЕНИЕ КЛАНАМИ (ДОБАВЛЕНИЕ/УДАЛЕНИЕ/РЕДАКТИРОВАНИЕ)
# ============================================================

def admin_clan_management_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='➕ Добавить клан', callback_data='admin_add_clan')],
        [InlineKeyboardButton(text='🗑 Удалить клан', callback_data='admin_delete_clan')],
        [InlineKeyboardButton(text='✏️ Редактировать клан', callback_data='admin_edit_clan')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_admin')],
    ])

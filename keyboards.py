from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# ============================================================
# 📌 ГЛАВНОЕ МЕНЮ
# ============================================================

def main_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📝 Подать анкету', callback_data='apply')],
        [InlineKeyboardButton(text='📊 Мои заявки', callback_data='my_applications')],
        [InlineKeyboardButton(text='ℹ️ О кланах', callback_data='about_clans')],
        [InlineKeyboardButton(text='📞 Контакты', callback_data='contacts')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='exit_test_mode')],  # ← НОВАЯ КНОПКА
    ])


def leader_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📋 Заявки в мой клан', callback_data='my_clan_applications')],
    ])


# ============================================================
# 🎯 ВЫБОР КЛАНА
# ============================================================

def clan_choice():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔴 KAIF', callback_data='clan_1')],
        [InlineKeyboardButton(text='🟡 NA KAIFE', callback_data='clan_2')],
        [InlineKeyboardButton(text='🟢 KAIF METRO', callback_data='clan_3')],
        [InlineKeyboardButton(text='🟣 KAIF ESPORTS', callback_data='clan_4')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_main')],
    ])


# ============================================================
# ✅ КНОПКИ ДЛЯ ЛИДЕРА/ЗАМА
# ============================================================

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


# ============================================================
# 📸 КНОПКИ ДЛЯ ФОТО
# ============================================================

def photo_old_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📸 Отправить фото 1', callback_data='send_photo_old')],
    ])


def photo_new_button_with_skip():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📸 Отправить фото 2', callback_data='send_photo_new')],
        [InlineKeyboardButton(text='⏭️ Пропустить', callback_data='skip_photo')],
    ])


# ============================================================
# 🔙 КНОПКИ НАВИГАЦИИ
# ============================================================

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
        [InlineKeyboardButton(text='🔙 Назад', callback_data=callback_data)],
    ])


# ============================================================
# ⚙️ АДМИН-ПАНЕЛЬ
# ============================================================

def admin_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📊 Статистика', callback_data='admin_stats')],
        [InlineKeyboardButton(text='📤 Экспорт CSV', callback_data='admin_export')],
        [InlineKeyboardButton(text='👥 Чёрный список', callback_data='admin_blacklist')],
        [InlineKeyboardButton(text='👥 Управление руководителями', callback_data='admin_manage_roles')],
        [InlineKeyboardButton(text='🧪 Тестовая анкета', callback_data='admin_test_application')],
        [InlineKeyboardButton(text='🗑 Очистить тестовые заявки', callback_data='admin_clear_test')],
        [InlineKeyboardButton(text='🧑‍💻 Стать кандидатом', callback_data='admin_become_candidate')],
        [InlineKeyboardButton(text='🔙 Выйти', callback_data='back_to_main')],
    ])


# ============================================================
# 👥 УПРАВЛЕНИЕ РУКОВОДИТЕЛЯМИ
# ============================================================

def manage_roles_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='➕ Назначить лидера', callback_data='role_assign_leader')],
        [InlineKeyboardButton(text='➕ Назначить зама', callback_data='role_assign_deputy')],
        [InlineKeyboardButton(text='🗑 Удалить лидера', callback_data='role_remove_leader')],
        [InlineKeyboardButton(text='🗑 Удалить зама', callback_data='role_remove_deputy')],
        [InlineKeyboardButton(text='📋 Список руководителей', callback_data='role_list')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_roles')],  
    ])


def assign_choice_menu():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📋 Выбрать из существующих', callback_data='assign_from_existing')],
        [InlineKeyboardButton(text='✏️ Ввести нового пользователя', callback_data='assign_from_new')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_roles')],
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
    buttons.append([InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_roles')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def select_clan_for_role_buttons(clans, role_type, user_id, username, name):
    buttons = []
    for clan in clans:
        clan_id, clan_name = clan[0], clan[1]
        emoji = '🔴' if clan_id == 1 else '🟡' if clan_id == 2 else '🟢' if clan_id == 3 else '🟣'
        buttons.append([InlineKeyboardButton(
            text=f"{emoji} {clan_name}",
            callback_data=f"assign_to_clan_{role_type}_{clan_id}_{user_id}_{username}_{name}"
        )])
    buttons.append([InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_roles')])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def clan_choice_for_roles():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔴 KAIF', callback_data='role_clan_1')],
        [InlineKeyboardButton(text='🟡 NA KAIFE', callback_data='role_clan_2')],
        [InlineKeyboardButton(text='🟢 KAIF METRO', callback_data='role_clan_3')],
        [InlineKeyboardButton(text='🟣 KAIF ESPORTS', callback_data='role_clan_4')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_roles')],
    ])


def cancel_button():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='❌ Отмена', callback_data='back_to_roles')],
    ])


# ============================================================
# 📋 КОПИРОВАТЬ ШАБЛОН
# ============================================================

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
        [InlineKeyboardButton(text='📤 Отправить сообщение', callback_data=f'send_message_{app_id}')],
        [InlineKeyboardButton(text='🔗 Добавить ссылку', callback_data=f'add_link_{app_id}')],
        [InlineKeyboardButton(text='✏️ Изменить ссылку', callback_data=f'edit_link_{app_id}')],
        [InlineKeyboardButton(text='🔙 Отмена', callback_data='back_to_main')],
    ])


def contact_with_link(app_id, link):
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='📤 Отправить сообщение', callback_data=f'send_message_{app_id}')],
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


def clan_choice_for_test():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='🔴 KAIF', callback_data='test_clan_1')],
        [InlineKeyboardButton(text='🟡 NA KAIFE', callback_data='test_clan_2')],
        [InlineKeyboardButton(text='🟢 KAIF METRO', callback_data='test_clan_3')],
        [InlineKeyboardButton(text='🟣 KAIF ESPORTS', callback_data='test_clan_4')],
        [InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_test')],
    ])

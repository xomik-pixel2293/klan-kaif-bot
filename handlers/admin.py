import json
import logging
from datetime import datetime

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.state import State, StatesGroup

from database import (
    get_clans,
    get_clan,
    get_clans_with_status,
    update_clan_leader,
    update_clan_deputy,
    remove_clan_leader,
    remove_clan_deputy,
    supabase,  # ✅ ТЕПЕРЬ РАБОТАЕТ
)
from keyboards import (
    admin_menu,
    manage_roles_menu,
    select_clan_for_role_buttons_simple,
    select_clan_for_role_buttons,
    cancel_button,
    back_button,
    admin_clan_status_menu,
    clan_toggle_button,
    admin_clan_management_menu,
    assign_choice_menu,
    select_existing_leader_buttons,
)
from config import ADMIN_IDS

router = Router()

# ============================================================
# 📌 FSM СОСТОЯНИЯ
# ============================================================

class RoleForm(StatesGroup):
    waiting_user_id = State()
    waiting_username = State()
    waiting_name = State()
    waiting_clan_id = State()


# ============================================================
# 👤 ПРОЦЕСС НАЗНАЧЕНИЯ НОВОГО ПОЛЬЗОВАТЕЛЯ (🔧 ИЗМЕНЕНО)
# ============================================================

@router.message(RoleForm.waiting_name)
async def process_new_user_name(message: Message, state: FSMContext):
    """Обработка ввода имени нового пользователя и выбор клана"""
    text = message.text.strip()
    if text.lower() in ['пропустить', 'skip']:
        name = None
    else:
        name = text
    
    data = await state.get_data()
    user_id = data.get('new_user_id')
    username = data.get('new_username')
    role_type = data.get('role_type', 'leader')
    role_name = 'лидером' if role_type == 'leader' else 'замом'
    
    await state.update_data(new_name=name)
    await state.update_data(pending_name=name)  # ✅ ДОБАВЛЕНО: сохраняем имя в state
    
    clans = await get_clans()
    text_msg = f'👤 Новый пользователь:\n'
    text_msg += f'ID: {user_id}\n'
    text_msg += f'Username: {username if username else "❌"}\n'
    text_msg += f'Имя: {name if name else "❌"}\n\n'
    text_msg += f'Выберите клан для назначения {role_name}:'
    
    await state.set_state(RoleForm.waiting_clan_id)
    
    # ✅ ИЗМЕНЕНО: используем новую функцию без имени в callback
    await message.answer(
        text_msg,
        reply_markup=select_clan_for_role_buttons_simple(clans, role_type, user_id, username or '')
    )


# ============================================================
# 👤 НАЗНАЧЕНИЕ ПОЛЬЗОВАТЕЛЯ (🆕 НОВАЯ ФУНКЦИЯ)
# ============================================================

@router.callback_query(F.data.startswith('assign_to_clan_simple_'))
async def assign_to_clan_simple(callback: CallbackQuery, state: FSMContext):
    """Назначить пользователя в клан (с именем из state)"""
    print(f"🔍 НАЖАТА КНОПКА: {callback.data}")
    
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()

    parts = callback.data.split('_')
    role_type = parts[3]
    clan_id = int(parts[4])
    user_id = int(parts[5])
    username = parts[6] if len(parts) > 6 else ''
    
    data = await state.get_data()
    name = data.get('pending_name') or data.get('new_name') or 'Пользователь'
    
    print(f"🔍 Имя из state: {name}")
    print(f"🔍 User ID для удаления: {user_id}")

    clan = await get_clan(clan_id)
    if not clan:
        await callback.message.answer('❌ Клан не найден')
        return

    # Удаляем пользователя со всех должностей
    print(f"🔍 НАЧИНАЕМ УДАЛЕНИЕ ПОЛЬЗОВАТЕЛЯ {user_id} СО ВСЕХ ДОЛЖНОСТЕЙ")
    
    try:
        await supabase.execute(
            "UPDATE clans SET leader_id = NULL, leader_name = NULL, leader_username = NULL WHERE leader_id = $1",
            user_id
        )
        print(f"🔍 Пользователь {user_id} удалён из всех лидеров (SQL)")
    except Exception as e:
        print(f"❌ Ошибка удаления лидера SQL: {e}")
    
    try:
        await supabase.execute(
            "UPDATE clans SET deputy_id = NULL, deputy_name = NULL, deputy_username = NULL WHERE deputy_id = $1",
            user_id
        )
        print(f"🔍 Пользователь {user_id} удалён из всех замов (SQL)")
    except Exception as e:
        print(f"❌ Ошибка удаления зама SQL: {e}")
    
    clans = await get_clans()
    for c in clans:
        if len(c) >= 11:
            c_id = c[0]
            leader_id_field = c[3] if len(c) > 3 else None
            deputy_id_field = c[6] if len(c) > 6 else None
        else:
            c_id = c[0]
            leader_id_field = c[2] if len(c) > 2 else None
            deputy_id_field = c[5] if len(c) > 5 else None
            
        if leader_id_field == user_id:
            await remove_clan_leader(c_id)
            print(f"🔍 Удалён лидер в клане {c_id}")
        if deputy_id_field == user_id:
            await remove_clan_deputy(c_id)
            print(f"🔍 Удалён зам в клане {c_id}")

    if role_type == 'leader':
        await update_clan_leader(clan_id, user_id, username, name)
        await callback.message.edit_text(
            f'✅ {name} (@{username}) назначен лидером клана {clan[1]}!\n'
            f'Старая должность автоматически удалена.'
        )
    else:
        await update_clan_deputy(clan_id, user_id, username, name)
        await callback.message.edit_text(
            f'✅ {name} (@{username}) назначен замом клана {clan[1]}!\n'
            f'Старая должность автоматически удалена.'
        )

    await state.clear()
    await callback.message.answer(
        '👥 Управление руководителями\n\nВыберите действие:',
        reply_markup=manage_roles_menu()
    )


# ============================================================
# ⚠️ СТАРАЯ ФУНКЦИЯ - ЗАКОММЕНТИРОВАНА (чтобы не мешала)
# ============================================================

# @router.callback_query(F.data.startswith('assign_to_clan_'))
# async def assign_to_clan(callback: CallbackQuery, state: FSMContext):
#     """Назначить пользователя в клан (устаревшая версия)"""
#     pass


# ============================================================
# 👥 УПРАВЛЕНИЕ РУКОВОДИТЕЛЯМИ
# ============================================================

@router.callback_query(F.data == 'admin_manage_roles')
async def admin_manage_roles(callback: CallbackQuery):
    """Меню управления руководителями"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()
    await callback.message.edit_text(
        '👥 Управление руководителями\n\nВыберите действие:',
        reply_markup=manage_roles_menu()
    )


@router.callback_query(F.data == 'role_assign_leader')
async def role_assign_leader(callback: CallbackQuery, state: FSMContext):
    """Назначить лидера"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()
    await state.update_data(role_type='leader')
    await callback.message.edit_text(
        'Выберите способ назначения лидера:',
        reply_markup=assign_choice_menu()
    )


@router.callback_query(F.data == 'role_assign_deputy')
async def role_assign_deputy(callback: CallbackQuery, state: FSMContext):
    """Назначить зама"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()
    await state.update_data(role_type='deputy')
    await callback.message.edit_text(
        'Выберите способ назначения зама:',
        reply_markup=assign_choice_menu()
    )


@router.callback_query(F.data == 'assign_from_new')
async def assign_from_new(callback: CallbackQuery, state: FSMContext):
    """Назначить нового пользователя"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()
    await state.set_state(RoleForm.waiting_user_id)
    await callback.message.edit_text(
        '✏️ Введите данные нового пользователя:\n\n'
        '1️⃣ Telegram ID (число):\n'
        'Пример: 123456789\n\n'
        '[❌ Отмена]',
        reply_markup=cancel_button()
    )


@router.message(RoleForm.waiting_user_id)
async def process_new_user_id(message: Message, state: FSMContext):
    """Обработка ID нового пользователя"""
    try:
        user_id = int(message.text.strip())
    except ValueError:
        await message.answer('❌ Введите корректный ID (число):')
        return
    
    await state.update_data(new_user_id=user_id)
    await state.set_state(RoleForm.waiting_username)
    await message.answer(
        f'✅ ID: {user_id}\n\n'
        '2️⃣ Введите USERNAME (без @):\n'
        'Пример: username\n\n'
        'Или отправьте "пропустить"',
        reply_markup=cancel_button()
    )


@router.message(RoleForm.waiting_username)
async def process_new_username(message: Message, state: FSMContext):
    """Обработка username нового пользователя"""
    text = message.text.strip()
    if text.lower() in ['пропустить', 'skip']:
        username = None
    else:
        username = text.replace('@', '')
    
    await state.update_data(new_username=username)
    await state.set_state(RoleForm.waiting_name)
    await message.answer(
        f'✅ Username: {username if username else "❌"}\n\n'
        '3️⃣ Введите ИМЯ пользователя:\n'
        'Пример: Антон\n\n'
        'Или отправьте "пропустить"',
        reply_markup=cancel_button()
    )


@router.callback_query(F.data == 'assign_from_existing')
async def assign_from_existing(callback: CallbackQuery, state: FSMContext):
    """Выбрать из существующих руководителей"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()
    
    data = await state.get_data()
    role_type = data.get('role_type', 'leader')
    
    clans = await get_clans()
    leaders = []
    for c in clans:
        if len(c) >= 11:
            leader_id = c[3] if len(c) > 3 else None
            leader_name = c[4] if len(c) > 4 else None
            leader_username = c[5] if len(c) > 5 else None
            clan_name = c[1]
            if leader_id:
                leaders.append({
                    'id': leader_id,
                    'name': leader_name or '❌',
                    'username': leader_username or '',
                    'role': 'Лидер',
                    'clan': clan_name,
                    'clan_id': c[0]
                })
            deputy_id = c[6] if len(c) > 6 else None
            deputy_name = c[7] if len(c) > 7 else None
            deputy_username = c[8] if len(c) > 8 else None
            if deputy_id:
                leaders.append({
                    'id': deputy_id,
                    'name': deputy_name or '❌',
                    'username': deputy_username or '',
                    'role': 'Зам',
                    'clan': clan_name,
                    'clan_id': c[0]
                })
    
    if not leaders:
        await callback.message.edit_text(
            '❌ Нет существующих руководителей.\n'
            'Используйте "Ввести нового пользователя"',
            reply_markup=assign_choice_menu()
        )
        return
    
    await callback.message.edit_text(
        'Выберите пользователя для назначения:',
        reply_markup=select_existing_leader_buttons(leaders, role_type)
    )


@router.callback_query(F.data.startswith('select_existing_'))
async def select_existing_leader(callback: CallbackQuery, state: FSMContext):
    """Выбор существующего руководителя"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()
    
    parts = callback.data.split('_')
    user_id = int(parts[2])
    clan_id = int(parts[3])
    
    data = await state.get_data()
    role_type = data.get('role_type', 'leader')
    
    clans = await get_clans()
    username = ''
    name = ''
    for c in clans:
        if len(c) >= 11:
            if c[3] == user_id:
                username = c[5] or ''
                name = c[4] or 'Пользователь'
                break
            if c[6] == user_id:
                username = c[8] or ''
                name = c[7] or 'Пользователь'
                break
    
    if not name:
        name = 'Пользователь'
    
    await state.update_data(
        new_user_id=user_id,
        new_username=username,
        pending_name=name,
        new_name=name
    )
    
    clans = await get_clans()
    role_name = 'лидером' if role_type == 'leader' else 'замом'
    
    await callback.message.edit_text(
        f'👤 Пользователь:\n'
        f'ID: {user_id}\n'
        f'Username: {username or "❌"}\n'
        f'Имя: {name}\n\n'
        f'Выберите клан для назначения {role_name}:',
        reply_markup=select_clan_for_role_buttons_simple(clans, role_type, user_id, username)
    )


@router.callback_query(F.data == 'role_remove_leader')
async def role_remove_leader(callback: CallbackQuery):
    """Удалить лидера"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()
    
    clans = await get_clans()
    text = '🗑 Выберите лидера для удаления:\n\n'
    buttons = []
    
    for c in clans:
        if len(c) >= 11:
            leader_id = c[3] if len(c) > 3 else None
            leader_name = c[4] if len(c) > 4 else None
            clan_name = c[1]
            if leader_id:
                text += f'👑 {leader_name} (@{c[5]}) - {clan_name}\n'
                buttons.append([InlineKeyboardButton(
                    text=f'🗑 {leader_name} - {clan_name}',
                    callback_data=f'remove_leader_{c[0]}_{leader_id}'
                )])
    
    if not buttons:
        await callback.message.edit_text('❌ Нет лидеров для удаления', reply_markup=back_button('back_to_admin'))
        return
    
    buttons.append([InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_admin')])
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


@router.callback_query(F.data == 'role_remove_deputy')
async def role_remove_deputy(callback: CallbackQuery):
    """Удалить зама"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()
    
    clans = await get_clans()
    text = '🗑 Выберите зама для удаления:\n\n'
    buttons = []
    
    for c in clans:
        if len(c) >= 11:
            deputy_id = c[6] if len(c) > 6 else None
            deputy_name = c[7] if len(c) > 7 else None
            clan_name = c[1]
            if deputy_id:
                text += f'👤 {deputy_name} (@{c[8]}) - {clan_name}\n'
                buttons.append([InlineKeyboardButton(
                    text=f'🗑 {deputy_name} - {clan_name}',
                    callback_data=f'remove_deputy_{c[0]}_{deputy_id}'
                )])
    
    if not buttons:
        await callback.message.edit_text('❌ Нет замов для удаления', reply_markup=back_button('back_to_admin'))
        return
    
    buttons.append([InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_admin')])
    await callback.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


@router.callback_query(F.data.startswith('remove_leader_'))
async def remove_leader_callback(callback: CallbackQuery):
    """Удалить лидера"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()
    
    parts = callback.data.split('_')
    clan_id = int(parts[2])
    user_id = int(parts[3])
    
    await remove_clan_leader(clan_id)
    await callback.message.edit_text(
        f'✅ Лидер удалён из клана!',
        reply_markup=back_button('back_to_admin')
    )


@router.callback_query(F.data.startswith('remove_deputy_'))
async def remove_deputy_callback(callback: CallbackQuery):
    """Удалить зама"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()
    
    parts = callback.data.split('_')
    clan_id = int(parts[2])
    user_id = int(parts[3])
    
    await remove_clan_deputy(clan_id)
    await callback.message.edit_text(
        f'✅ Зам удалён из клана!',
        reply_markup=back_button('back_to_admin')
    )


@router.callback_query(F.data == 'role_list')
async def show_roles_list(callback: CallbackQuery):
    """Показать список всех руководителей"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    
    await callback.answer()
    clans = await get_clans()
    
    if not clans:
        await callback.message.answer('❌ Кланы не найдены')
        return
    
    text = '👥 ТЕКУЩИЕ РУКОВОДИТЕЛИ:\n\n'
    emojis = {1: '🔴', 2: '🟡', 3: '🟢', 4: '🟣', 5: '🟠'}
    emoji_names = {1: 'KAIF', 2: 'NA KAIFE', 3: 'KAIF METRO', 4: 'KAIF ESPORTS', 5: 'TDM'}
    
    for clan in clans:
        clan_id = clan[0]
        clan_name = clan[1] if len(clan) > 1 else emoji_names.get(clan_id, 'Неизвестный')
        emoji = emojis.get(clan_id, '🔵')
        
        if len(clan) >= 11:
            leader_id = clan[3] if len(clan) > 3 else None
            leader_username = clan[4] if len(clan) > 4 else 'None'  # ← ИСПРАВЛЕНО
            leader_name = clan[5] if len(clan) > 5 else 'None'     # ← ИСПРАВЛЕНО
            deputy_id = clan[6] if len(clan) > 6 else None
            deputy_username = clan[7] if len(clan) > 7 else 'None' # ← ИСПРАВЛЕНО
            deputy_name = clan[8] if len(clan) > 8 else 'None'     # ← ИСПРАВЛЕНО
        else:
            leader_id = clan[2] if len(clan) > 2 else None
            leader_username = clan[3] if len(clan) > 3 else 'None' # ← ИСПРАВЛЕНО
            leader_name = clan[4] if len(clan) > 4 else 'None'     # ← ИСПРАВЛЕНО
            deputy_id = clan[5] if len(clan) > 5 else None
            deputy_username = clan[6] if len(clan) > 6 else 'None' # ← ИСПРАВЛЕНО
            deputy_name = clan[7] if len(clan) > 7 else 'None'     # ← ИСПРАВЛЕНО
        
        text += f'{emoji} {clan_name}:\n'
        text += f'   👑 Лидер: {leader_name} (@{leader_username}) (ID: {leader_id})\n'
        text += f'   👤 Зам: {deputy_name} (@{deputy_username}) (ID: {deputy_id})\n\n'
    
    await callback.message.edit_text(
        text,
        reply_markup=back_button('back_to_admin')
    )

# ============================================================
# 🔄 УПРАВЛЕНИЕ СТАТУСОМ КЛАНОВ
# ============================================================

@router.callback_query(F.data == 'admin_clan_status')
async def admin_clan_status(callback: CallbackQuery):
    """Меню управления статусом кланов"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()
    await callback.message.edit_text(
        '🔄 Управление статусом кланов\n\n'
        'Выберите клан для изменения статуса:',
        reply_markup=admin_clan_status_menu()
    )


@router.callback_query(F.data.startswith('admin_clan_status_'))
async def admin_clan_status_toggle(callback: CallbackQuery):
    """Показать статус клана и кнопку переключения"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()
    
    clan_id = int(callback.data.split('_')[-1])
    clans = await get_clans_with_status()
    
    for c in clans:
        if c[0] == clan_id:
            clan_name = c[1]
            is_active = c[3]
            await callback.message.edit_text(
                f'🔄 Клан: {clan_name}\n'
                f'Статус: {"✅ ВКЛЮЧЁН" if is_active else "❌ ВЫКЛЮЧЁН"}',
                reply_markup=clan_toggle_button(clan_id, clan_name, is_active)
            )
            return


@router.callback_query(F.data.startswith('toggle_clan_'))
async def toggle_clan(callback: CallbackQuery):
    """Переключить статус клана"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()
    
    clan_id = int(callback.data.split('_')[-1])
    
    clans = await get_clans_with_status()
    for c in clans:
        if c[0] == clan_id:
            new_status = not c[3]
            await supabase.execute(
                "UPDATE clans SET is_active = $1 WHERE id = $2",
                new_status,
                clan_id
            )
            await callback.message.edit_text(
                f'✅ Статус клана изменён!',
                reply_markup=back_button('admin_clan_status')
            )
            return


# ============================================================
# 🏗️ УПРАВЛЕНИЕ КЛАНАМИ
# ============================================================

@router.callback_query(F.data == 'admin_clan_management')
async def admin_clan_management(callback: CallbackQuery):
    """Меню управления кланами"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()
    await callback.message.edit_text(
        '🏗️ Управление кланами\n\nВыберите действие:',
        reply_markup=admin_clan_management_menu()
    )


@router.callback_query(F.data == 'admin_add_clan')
async def admin_add_clan(callback: CallbackQuery):
    """Добавить новый клан"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()
    await callback.message.edit_text(
        '✏️ Введите название нового клана:',
        reply_markup=cancel_button()
    )


@router.callback_query(F.data == 'admin_delete_clan')
async def admin_delete_clan(callback: CallbackQuery):
    """Удалить клан"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()
    
    clans = await get_clans()
    buttons = []
    for c in clans:
        buttons.append([InlineKeyboardButton(
            text=f'🗑 {c[1]}',
            callback_data=f'delete_clan_{c[0]}'
        )])
    buttons.append([InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_admin')])
    
    await callback.message.edit_text(
        '🗑 Выберите клан для удаления:',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


@router.callback_query(F.data.startswith('delete_clan_'))
async def delete_clan(callback: CallbackQuery):
    """Удалить клан из БД"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()
    
    clan_id = int(callback.data.split('_')[-1])
    await supabase.execute("DELETE FROM clans WHERE id = $1", clan_id)
    await callback.message.edit_text(
        '✅ Клан удалён!',
        reply_markup=back_button('back_to_admin')
    )


@router.callback_query(F.data == 'admin_edit_clan')
async def admin_edit_clan(callback: CallbackQuery):
    """Редактировать клан"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()
    
    clans = await get_clans()
    buttons = []
    for c in clans:
        buttons.append([InlineKeyboardButton(
            text=f'✏️ {c[1]}',
            callback_data=f'edit_clan_{c[0]}'
        )])
    buttons.append([InlineKeyboardButton(text='🔙 Назад', callback_data='back_to_admin')])
    
    await callback.message.edit_text(
        '✏️ Выберите клан для редактирования:',
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons)
    )


@router.callback_query(F.data.startswith('edit_clan_'))
async def edit_clan(callback: CallbackQuery):
    """Показать форму редактирования клана"""
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()
    
    clan_id = int(callback.data.split('_')[-1])
    clan = await get_clan(clan_id)
    
    if not clan:
        await callback.message.edit_text('❌ Клан не найден', reply_markup=back_button('back_to_admin'))
        return
    
    await callback.message.edit_text(
        f'✏️ Редактирование клана: {clan[1]}\n\n'
        f'ID: {clan_id}\n'
        f'Название: {clan[1]}\n\n'
        f'Отправьте новое название клана:',
        reply_markup=cancel_button()
    )


# ============================================================
# 🔙 НАЗАД
# ============================================================

@router.callback_query(F.data == 'back_to_admin')
async def back_to_admin(callback: CallbackQuery, state: FSMContext):
    """Вернуться в админ-панель"""
    await state.clear()
    await callback.message.edit_text(
        '👑 Админ-панель\n\nВыберите действие:',
        reply_markup=admin_menu()
    )


@router.callback_query(F.data == 'cancel')
async def cancel_action(callback: CallbackQuery, state: FSMContext):
    """Отменить действие"""
    await state.clear()
    await callback.message.edit_text(
        '👑 Админ-панель\n\nВыберите действие:',
        reply_markup=admin_menu()
    )

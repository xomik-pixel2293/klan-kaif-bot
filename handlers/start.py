import os
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from config import ADMIN_IDS
from database import get_clan_by_user
from keyboards import (
    main_menu, leader_menu, admin_menu,
    manage_roles_menu, test_application_menu,
    admin_clan_management_menu
)

router = Router()


# ============================================================
# 📌 СОСТОЯНИЯ (FSM)
# ============================================================

class ApplicationForm(StatesGroup):
    waiting_for_answers = State()
    waiting_photo_old = State()
    waiting_photo_new = State()
    waiting_contact_message = State()
    waiting_test_answers = State()


class RoleForm(StatesGroup):
    waiting_clan_id = State()
    waiting_user_id = State()
    waiting_username = State()
    waiting_name = State()
    waiting_role_type = State()


class ClanManagementForm(StatesGroup):
    waiting_new_clan_name = State()
    waiting_new_clan_emoji = State()
    waiting_new_clan_leader_id = State()
    waiting_new_clan_leader_username = State()
    waiting_new_clan_leader_name = State()
    waiting_new_clan_deputy_id = State()
    waiting_new_clan_deputy_username = State()
    waiting_new_clan_deputy_name = State()
    waiting_edit_clan_field = State()


# ============================================================
# 🏠 СТАРТ
# ============================================================

@router.message(Command('start'))
async def cmd_start(message: Message):
    clan = await get_clan_by_user(message.from_user.id)
    if clan:
        await message.answer('🏠 Добро пожаловать в KLAN KAIF!\n\nВыберите действие:', reply_markup=leader_menu())
    else:
        await message.answer('🏠 Добро пожаловать в KLAN KAIF!\n\nВыберите действие:', reply_markup=main_menu())


# ============================================================
# ⚙️ АДМИН
# ============================================================

@router.message(Command('admin'))
async def cmd_admin(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer('⛔ У вас нет прав администратора.')
        return
    await message.answer('⚙️ АДМИН-ПАНЕЛЬ KLAN KAIF\n\nВыберите действие:', reply_markup=admin_menu())


# ============================================================
# 🔙 ШАГ НАЗАД
# ============================================================

@router.callback_query(F.data == 'back_to_main')
async def back_to_main(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    
    data = await state.get_data()
    is_test = data.get('is_test_mode', False)
    
    if is_test:
        await callback.message.edit_text(
            '🏠 Добро пожаловать в KLAN KAIF!\n\nВыберите действие:',
            reply_markup=main_menu()
        )
        return
    
    await state.clear()
    clan = await get_clan_by_user(callback.from_user.id)
    if clan:
        await callback.message.edit_text('🏠 Главное меню:', reply_markup=leader_menu())
    else:
        await callback.message.edit_text('🏠 Главное меню:', reply_markup=main_menu())


@router.callback_query(F.data == 'back_to_admin')
async def back_to_admin(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        '⚙️ АДМИН-ПАНЕЛЬ KLAN KAIF\n\nВыберите действие:',
        reply_markup=admin_menu()
    )


@router.callback_query(F.data == 'back_to_roles')
async def back_to_roles(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        '⚙️ АДМИН-ПАНЕЛЬ KLAN KAIF\n\nВыберите действие:',
        reply_markup=admin_menu()
    )


@router.callback_query(F.data == 'back_to_test')
async def back_to_test(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        '🧪 ТЕСТОВАЯ АНКЕТА\n\n'
        'Нажмите "Написать тестовую анкету", чтобы отправить заявку как кандидат.\n\n'
        '📌 Анкета будет выглядеть как обычная заявка, но с пометкой "🧪 ТЕСТ"',
        reply_markup=test_application_menu()
    )


@router.callback_query(F.data == 'back_to_clan_management')
async def back_to_clan_management(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    await callback.message.edit_text(
        '🏗️ УПРАВЛЕНИЕ КЛАНАМИ\n\n'
        'Выберите действие:\n\n'
        '➕ Добавить новый клан\n'
        '🗑 Удалить существующий клан\n'
        '✏️ Редактировать данные клана',
        reply_markup=admin_clan_management_menu()
    )
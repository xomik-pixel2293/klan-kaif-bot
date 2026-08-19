import re
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InputMediaPhoto
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS
from database import (
    is_in_blacklist, get_clan, get_clan_by_name, get_clan_active_status,
    get_pending_application, add_application,
    update_application_photo_old, update_application_photo_new,
    update_application_has_photos
)
from keyboards import (
    back_button, after_apply_buttons, photo_old_button,
    photo_new_button_with_skip, copy_template_button, exit_test_button,
    clan_choice, main_menu, admin_menu, review_buttons
)
from .start import ApplicationForm

router = Router()


# ============================================================
# 🧑‍💻 СТАТЬ КАНДИДАТОМ (ДЛЯ АДМИНОВ)
# ============================================================

@router.callback_query(F.data == 'admin_become_candidate')
async def admin_become_candidate(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()

    await callback.message.edit_text(
        '🏠 Добро пожаловать в KLAN KAIF!\n\n'
        'Выберите действие:',
        reply_markup=main_menu()
    )
    
    await state.update_data(is_test_mode=True)


# ============================================================
# 🔙 ВЫХОД ИЗ ТЕСТОВОГО РЕЖИМА
# ============================================================

@router.callback_query(F.data == 'exit_test_mode')
async def exit_test_mode(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    
    await callback.message.edit_text(
        '⚙️ АДМИН-ПАНЕЛЬ KLAN KAIF\n\nВыберите действие:',
        reply_markup=admin_menu()
    )


# ============================================================
# 📝 ПОДАТЬ АНКЕТУ
# ============================================================

@router.callback_query(F.data == 'apply')
async def apply_start(callback: CallbackQuery):
    await callback.answer()
    if await is_in_blacklist(callback.from_user.id):
        await callback.message.edit_text(
            '🚫 Вы в чёрном списке кланов KAIF.\nОбратитесь к лидерам для разблокировки.',
            reply_markup=back_button('back_to_main')
        )
        return
    
    keyboard = await clan_choice()
    
    if not keyboard.inline_keyboard or len(keyboard.inline_keyboard) <= 1:
        await callback.message.edit_text(
            '❌ В данный момент ни один клан не принимает заявки.\nПопробуйте позже.',
            reply_markup=back_button('back_to_main')
        )
        return
    
    await callback.message.edit_text(
        'Выберите клан для подачи заявки:',
        reply_markup=keyboard
    )


# ============================================================
# 🎯 ВЫБОР КЛАНА
# ============================================================

@router.callback_query(F.data.startswith('clan_'))
async def select_clan(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    clan_id = int(callback.data.split('_')[1])
    clan = await get_clan(clan_id)
    if not clan:
        await callback.message.answer('❌ Клан не найден')
        return

    if len(clan) >= 9:
        clan_id = clan[0]
        name = clan[1]
        leader_id = clan[3]
        leader_username = clan[4]
        leader_name = clan[5]
        deputy_id = clan[6]
        deputy_username = clan[7]
        deputy_name = clan[8]
    else:
        clan_id = clan[0]
        name = clan[1]
        leader_id = clan[2] if len(clan) > 2 else None
        leader_username = clan[3] if len(clan) > 3 else None
        leader_name = clan[4] if len(clan) > 4 else None
        deputy_id = clan[5] if len(clan) > 5 else None
        deputy_username = clan[6] if len(clan) > 6 else None
        deputy_name = clan[7] if len(clan) > 7 else None

    try:
        is_active = await get_clan_active_status(clan_id)
    except Exception as e:
        print(f"❌ Ошибка get_clan_active_status: {e}")
        is_active = True
    
    if not is_active:
        await callback.message.edit_text(
            '❌ Этот клан временно не принимает заявки.\nВыберите другой клан.',
            reply_markup=await clan_choice()
        )
        return

    if not leader_id and not deputy_id:
        await callback.message.edit_text(
            '❌ В этом клане пока нет ответственных.\nЗаявки временно не принимаются.',
            reply_markup=back_button('back_to_main')
        )
        return

    existing = await get_pending_application(callback.from_user.id, clan_id)
    if existing:
        await callback.message.edit_text(
            '⏳ У вас уже есть заявка в этот клан!\nДождитесь решения.',
            reply_markup=after_apply_buttons()
        )
        return

    await state.update_data(clan_id=clan_id, clan_name=name)
    await state.set_state(ApplicationForm.waiting_for_answers)

    responsible = deputy_name if deputy_id else leader_name
    hint = f'ℹ️ Заявки принимает {responsible}\n\n'

    template = (
        'Имя: \n'
        'Возраст: \n'
        'Ник: \n'
        'ID: \n'
        'Часовой пояс (МСК): '
    )

    photo_text = (
        '📸 Теперь отправьте 2 фото:\n'
        '1️⃣ Скрин за ТЕКУЩИЙ сезон\n'
        '2️⃣ Скрин за ПРОШЛЫЙ сезон (если есть)'
    )

    await callback.message.edit_text(
        f'{hint}'
        '📋 СКОПИРУЙТЕ ШАБЛОН И ЗАПОЛНИТЕ:\n'
        '━━━━━━━━━━━━━━━━━━━━━━\n'
        f'{template}'
        '━━━━━━━━━━━━━━━━━━━━━━\n\n'
        '⚠️ Заполните все поля и отправьте одним сообщением.\n'
        'Каждое поле — с новой строки.\n\n'
        '📌 ПРИМЕР:\n'
        'Имя: Александр\n'
        'Возраст: 19\n'
        'Ник: KAIF_Pro\n'
        'ID: 123456789\n'
        'Часовой пояс (МСК): +0\n\n'
        f'{photo_text}',
        reply_markup=copy_template_button(template)
    )


# ============================================================
# 📥 ПОЛУЧЕНИЕ АНКЕТЫ
# ============================================================

@router.message(ApplicationForm.waiting_for_answers)
async def receive_application(message: Message, state: FSMContext):
    if await is_in_blacklist(message.from_user.id):
        await message.answer('🚫 Вы в чёрном списке.', reply_markup=back_button('back_to_main'))
        await state.clear()
        return

    data = await state.get_data()
    clan_id = data.get('clan_id')
    clan_name = data.get('clan_name')
    is_test = data.get('is_test_mode', False)

    text = message.text.strip()
    lines = [line.strip() for line in text.split('\n') if line.strip()]

    cleaned_lines = []
    for line in lines:
        if ':' in line or '：' in line:
            parts = re.split(r'[:：]', line, 1)
            if len(parts) == 2:
                cleaned_lines.append(parts[1].strip())
            else:
                cleaned_lines.append(line.strip())
        else:
            cleaned_lines.append(line.strip())

    if len(cleaned_lines) != 5:
        await message.answer(
            '❌ Нужно ровно 5 полей!\n\n'
            '📌 ПРАВИЛЬНЫЙ ФОРМАТ:\n'
            'Имя: Александр\n'
            'Возраст: 19\n'
            'Ник: KAIF_Pro\n'
            'ID: 123456789\n'
            'Часовой пояс (МСК): +0\n\n'
            '⚠️ Или просто 5 строк без названий полей:\n'
            'Александр\n'
            '19\n'
            'KAIF_Pro\n'
            '123456789\n'
            '+0',
            reply_markup=back_button('back_to_main')
        )
        return

    answers = {
        'name': cleaned_lines[0],
        'age': cleaned_lines[1],
        'nickname': cleaned_lines[2],
        'id': cleaned_lines[3],
        'timezone': cleaned_lines[4]
    }

    try:
        age = int(answers['age'])
        if age < 10 or age > 99:
            raise ValueError
    except:
        await message.answer(
            '❌ Возраст должен быть числом от 10 до 99!\n'
            'Попробуйте снова:',
            reply_markup=back_button('back_to_main')
        )
        return

    try:
        tz = int(answers['timezone'])
        if tz < -12 or tz > 12:
            raise ValueError
    except:
        await message.answer(
            '❌ Часовой пояс должен быть числом от -12 до +12!\n'
            'Попробуйте снова:',
            reply_markup=back_button('back_to_main')
        )
        return

    await state.update_data(is_test_mode=is_test)

    if is_test:
        app_id = await add_application(message.from_user.id, 'test_user', clan_id, answers)
    else:
        app_id = await add_application(message.from_user.id, message.from_user.username or 'unknown', clan_id, answers)

    await state.update_data(app_id=app_id, answers=answers, is_test_mode=is_test)
    await state.set_state(ApplicationForm.waiting_photo_old)

    if clan_name == "KAIF METRO":
        await message.answer(
            f'✅ Анкета сохранена!\n\n'
            f'📋 ПРОВЕРЬТЕ ДАННЫЕ:\n'
            f'1. Имя: {answers["name"]}\n'
            f'2. Возраст: {answers["age"]}\n'
            f'3. Ник: {answers["nickname"]}\n'
            f'4. ID: {answers["id"]}\n'
            f'5. Часовой пояс (МСК): {answers["timezone"]}\n\n'
            f'📸 Теперь отправьте 2 фото:\n'
            f'1️⃣ Скрин за ТЕКУЩИЙ сезон\n'
            f'2️⃣ Скрин за ПРОШЛЫЙ сезон (если есть)\n\n'
            f'Второе фото можно пропустить.',
            reply_markup=photo_old_button()
        )
    else:
        await message.answer(
            f'✅ Анкета сохранена!\n\n'
            f'📋 ПРОВЕРЬТЕ ДАННЫЕ:\n'
            f'1. Имя: {answers["name"]}\n'
            f'2. Возраст: {answers["age"]}\n'
            f'3. Ник: {answers["nickname"]}\n'
            f'4. ID: {answers["id"]}\n'
            f'5. Часовой пояс (МСК): {answers["timezone"]}\n\n'
            f'📸 Теперь отправьте 2 фото:\n'
            f'1️⃣ Скрин за ПРОШЛЫЙ сезон\n'
            f'2️⃣ Скрин за ТЕКУЩИЙ сезон\n\n'
            f'Второе фото можно пропустить.',
            reply_markup=photo_old_button()
        )


# ============================================================
# 📸 ОТПРАВКА ФОТО 1
# ============================================================

@router.callback_query(F.data == 'send_photo_old')
async def send_photo_old(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(ApplicationForm.waiting_photo_old)
    await callback.message.edit_text('📸 Отправьте фото 1.\nПросто пришлите фото в этот чат.')


# ============================================================
# 📥 ПОЛУЧЕНИЕ ФОТО 1
# ============================================================

@router.message(ApplicationForm.waiting_photo_old, F.photo)
async def receive_photo_old(message: Message, state: FSMContext):
    data = await state.get_data()
    app_id = data.get('app_id')
    is_test = data.get('is_test_mode', False)
    
    if not app_id:
        await message.answer('Ошибка. Попробуйте начать заново через /start')
        await state.clear()
        return

    await update_application_photo_old(app_id, message.photo[-1].file_id)
    await update_application_has_photos(app_id, 1)
    await state.update_data(photo_old=message.photo[-1].file_id, is_test_mode=is_test)
    await state.set_state(ApplicationForm.waiting_photo_new)

    clan_name = data.get('clan_name')
    if clan_name == "KAIF METRO":
        await message.answer(
            '✅ Фото 1 (текущий сезон) получено!\n'
            '📸 Теперь отправьте фото 2 (прошлый сезон, если есть)\n\n'
            'Или нажмите "Пропустить".',
            reply_markup=photo_new_button_with_skip()
        )
    else:
        await message.answer(
            '✅ Фото 1 (прошлый сезон) получено!\n'
            '📸 Теперь отправьте фото 2 (текущий сезон)\n\n'
            'Или нажмите "Пропустить".',
            reply_markup=photo_new_button_with_skip()
        )


# ============================================================
# 📸 ОТПРАВКА ФОТО 2
# ============================================================

@router.callback_query(F.data == 'send_photo_new')
async def send_photo_new(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.set_state(ApplicationForm.waiting_photo_new)
    await callback.message.edit_text('📸 Отправьте фото 2.\nПросто пришлите фото в этот чат.')


# ============================================================
# 📥 ПОЛУЧЕНИЕ ФОТО 2 + УВЕДОМЛЕНИЕ ЛИДЕРУ И ЗАМУ
# ============================================================

@router.message(ApplicationForm.waiting_photo_new, F.photo)
async def receive_photo_new(message: Message, state: FSMContext):
    data = await state.get_data()
    app_id = data.get('app_id')
    clan_name = data.get('clan_name')
    photo_old = data.get('photo_old')
    answers = data.get('answers', {})
    is_test = data.get('is_test_mode', False)

    if not app_id:
        await message.answer('Ошибка. Попробуйте начать заново через /start')
        await state.clear()
        return

    photo_new = message.photo[-1].file_id
    await update_application_photo_new(app_id, photo_new)
    await update_application_has_photos(app_id, 2)

    await state.clear()

    try:
        clan = await get_clan_by_name(clan_name)
        if not clan:
            await message.answer('❌ Клан не найден.')
            return

        if len(clan) >= 9:
            clan_id = clan[0]
            name = clan[1]
            leader_id = clan[3]
            leader_username = clan[4]
            leader_name = clan[5]
            deputy_id = clan[6]
            deputy_username = clan[7]
            deputy_name = clan[8]
        else:
            clan_id = clan[0]
            name = clan[1]
            leader_id = clan[2] if len(clan) > 2 else None
            leader_username = clan[3] if len(clan) > 3 else None
            leader_name = clan[4] if len(clan) > 4 else None
            deputy_id = clan[5] if len(clan) > 5 else None
            deputy_username = clan[6] if len(clan) > 6 else None
            deputy_name = clan[7] if len(clan) > 7 else None

        text = (
            f'🔔 НОВАЯ ЗАЯВКА #{app_id} В КЛАН {clan_name}\n\n'
            f'От: @{message.from_user.username or "unknown"} (ID: {message.from_user.id})\n'
            f'Дата: {datetime.now().strftime("%d.%m.%Y, %H:%M")}\n\n'
            f'📝 АНКЕТА:\n'
            f'1. Имя: {answers.get("name", "")}\n'
            f'2. Возраст: {answers.get("age", "")}\n'
            f'3. Ник: {answers.get("nickname", "")}\n'
            f'4. ID: {answers.get("id", "")}\n'
            f'5. Часовой пояс (МСК): {answers.get("timezone", "")}\n\n'
            f'📸 Скринов: 2'
        )

        if leader_id:
            try:
                await message.bot.send_media_group(
                    leader_id,
                    media=[
                        InputMediaPhoto(media=photo_old, caption=text),
                        InputMediaPhoto(media=photo_new)
                    ]
                )
                await message.bot.send_message(
                    leader_id,
                    "📌 Действия с заявкой:",
                    reply_markup=review_buttons(app_id)
                )
            except Exception as e:
                print(f"Ошибка отправки лидеру: {e}")

        if deputy_id:
            try:
                await message.bot.send_media_group(
                    deputy_id,
                    media=[
                        InputMediaPhoto(media=photo_old, caption=text),
                        InputMediaPhoto(media=photo_new)
                    ]
                )
                await message.bot.send_message(
                    deputy_id,
                    "📌 Действия с заявкой:",
                    reply_markup=review_buttons(app_id)
                )
            except Exception as e:
                print(f"Ошибка отправки заму: {e}")

        if is_test:
            await message.answer(
                f'🧪 ТЕСТОВАЯ заявка #{app_id} отправлена на рассмотрение!\n'
                f'Ожидайте решения лидера или зама.',
                reply_markup=exit_test_button()
            )
        else:
            await message.answer(
                f'✅ Заявка #{app_id} отправлена на рассмотрение!\n'
                f'Ожидайте решения лидера или зама.',
                reply_markup=after_apply_buttons()
            )

    except Exception as e:
        await message.answer(f'❌ Ошибка: {e}\nЗаявка сохранена.')


# ============================================================
# ⏭️ ПРОПУСТИТЬ ФОТО 2
# ============================================================

@router.callback_query(F.data == 'skip_photo')
async def skip_photo(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    data = await state.get_data()
    app_id = data.get('app_id')
    clan_name = data.get('clan_name')
    answers = data.get('answers', {})
    photo_old = data.get('photo_old')
    is_test = data.get('is_test_mode', False)

    if not app_id:
        await callback.message.answer('Ошибка. Попробуйте начать заново через /start')
        await state.clear()
        return

    await state.clear()

    try:
        clan = await get_clan_by_name(clan_name)
        if not clan:
            await callback.message.answer('❌ Клан не найден.')
            return

        if len(clan) >= 9:
            clan_id = clan[0]
            name = clan[1]
            leader_id = clan[3]
            leader_username = clan[4]
            leader_name = clan[5]
            deputy_id = clan[6]
            deputy_username = clan[7]
            deputy_name = clan[8]
        else:
            clan_id = clan[0]
            name = clan[1]
            leader_id = clan[2] if len(clan) > 2 else None
            leader_username = clan[3] if len(clan) > 3 else None
            leader_name = clan[4] if len(clan) > 4 else None
            deputy_id = clan[5] if len(clan) > 5 else None
            deputy_username = clan[6] if len(clan) > 6 else None
            deputy_name = clan[7] if len(clan) > 7 else None

        text = (
            f'🔔 НОВАЯ ЗАЯВКА #{app_id} В КЛАН {clan_name}\n\n'
            f'От: @{callback.from_user.username or "unknown"} (ID: {callback.from_user.id})\n'
            f'Дата: {datetime.now().strftime("%d.%m.%Y, %H:%M")}\n\n'
            f'📝 АНКЕТА:\n'
            f'1. Имя: {answers.get("name", "")}\n'
            f'2. Возраст: {answers.get("age", "")}\n'
            f'3. Ник: {answers.get("nickname", "")}\n'
            f'4. ID: {answers.get("id", "")}\n'
            f'5. Часовой пояс (МСК): {answers.get("timezone", "")}\n\n'
            f'📸 Скринов: 1 (второе фото пропущено)'
        )

        await update_application_has_photos(app_id, 1)

        if leader_id:
            try:
                await callback.bot.send_photo(
                    leader_id,
                    photo=photo_old,
                    caption=text,
                    reply_markup=review_buttons(app_id)
                )
            except Exception as e:
                print(f"Ошибка отправки лидеру: {e}")

        if deputy_id:
            try:
                await callback.bot.send_photo(
                    deputy_id,
                    photo=photo_old,
                    caption=text,
                    reply_markup=review_buttons(app_id)
                )
            except Exception as e:
                print(f"Ошибка отправки заму: {e}")

        if is_test:
            await callback.message.edit_text(
                f'⏭️ Вы пропустили второе фото.\n'
                f'✅ ТЕСТОВАЯ заявка #{app_id} отправлена на рассмотрение!\n'
                f'Ожидайте решения лидера или зама.',
                reply_markup=exit_test_button()
            )
        else:
            await callback.message.edit_text(
                f'⏭️ Вы пропустили второе фото.\n'
                f'✅ Заявка #{app_id} отправлена на рассмотрение!\n'
                f'Ожидайте решения лидера или зама.',
                reply_markup=after_apply_buttons()
            )

    except Exception as e:
        await callback.message.answer(f'❌ Ошибка: {e}\nЗаявка сохранена.')

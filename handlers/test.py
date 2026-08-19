import re
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

from config import ADMIN_IDS
from database import (
    get_clan, get_clan_active_status,
    add_application, review_buttons
)
from keyboards import (
    test_application_menu, back_button,
    clan_choice_for_test, admin_menu
)
from .start import ApplicationForm

router = Router()


# ============================================================
# 🧪 ТЕСТОВАЯ АНКЕТА (ДЛЯ АДМИНОВ)
# ============================================================

@router.callback_query(F.data == 'admin_test_application')
async def admin_test_application(callback: CallbackQuery):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()

    await callback.message.edit_text(
        '🧪 ТЕСТОВАЯ АНКЕТА\n\n'
        'Нажмите "Написать тестовую анкету", чтобы отправить заявку как кандидат.\n\n'
        '📌 Анкета будет выглядеть как обычная заявка, но с пометкой "🧪 ТЕСТ"',
        reply_markup=test_application_menu()
    )


@router.callback_query(F.data == 'write_test_application')
async def write_test_application(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()

    await state.set_state(ApplicationForm.waiting_test_answers)

    await callback.message.edit_text(
        '📝 НАПИШИТЕ ТЕСТОВУЮ АНКЕТУ\n\n'
        '📋 Скопируйте шаблон и заполните:\n'
        '━━━━━━━━━━━━━━━━━━━━━━\n'
        'Имя: \n'
        'Возраст: \n'
        'Ник: \n'
        'ID: \n'
        'Часовой пояс (МСК): \n'
        '━━━━━━━━━━━━━━━━━━━━━━\n\n'
        '📌 ПРИМЕР:\n'
        'Имя: Тестовый Пользователь\n'
        'Возраст: 25\n'
        'Ник: Test_User\n'
        'ID: 123456789\n'
        'Часовой пояс (МСК): +0\n\n'
        '⚠️ После заполнения выберите клан для отправки.',
        reply_markup=back_button('back_to_test')
    )


@router.message(ApplicationForm.waiting_test_answers)
async def receive_test_application(message: Message, state: FSMContext):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer('⛔ У вас нет прав')
        await state.clear()
        return

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
            'Имя: Тестовый Пользователь\n'
            'Возраст: 25\n'
            'Ник: Test_User\n'
            'ID: 123456789\n'
            'Часовой пояс (МСК): +0',
            reply_markup=back_button('back_to_test')
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
            reply_markup=back_button('back_to_test')
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
            reply_markup=back_button('back_to_test')
        )
        return

    await state.update_data(test_answers=answers)
    await state.set_state(None)

    await message.answer(
        '✅ Анкета сохранена!\n\n'
        'Теперь выберите клан для отправки тестовой заявки:',
        reply_markup=await clan_choice_for_test()
    )


@router.callback_query(F.data.startswith('test_clan_'))
async def test_select_clan(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMIN_IDS:
        await callback.answer('⛔ Нет прав')
        return
    await callback.answer()

    clan_id = int(callback.data.split('_')[2])
    
    try:
        is_active = await get_clan_active_status(clan_id)
    except Exception as e:
        print(f"❌ Ошибка get_clan_active_status: {e}")
        is_active = True
    
    if not is_active:
        await callback.message.edit_text(
            '❌ Этот клан временно не принимает заявки.\nВыберите другой клан.',
            reply_markup=await clan_choice_for_test()
        )
        return
    
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

    data = await state.get_data()
    answers = data.get('test_answers', {})

    if not answers:
        await callback.message.answer('❌ Анкета не найдена. Попробуйте снова.')
        return

    app_id = await add_application(
        callback.from_user.id,
        'test_user',
        clan_id,
        answers
    )

    text = (
        f'🧪 ТЕСТОВАЯ ЗАЯВКА #{app_id} В КЛАН {name}\n\n'
        f'От: @{callback.from_user.username or "test"} (ID: {callback.from_user.id})\n'
        f'Дата: {datetime.now().strftime("%d.%m.%Y, %H:%M")}\n\n'
        f'📝 АНКЕТА:\n'
        f'1. Имя: {answers.get("name", "")}\n'
        f'2. Возраст: {answers.get("age", "")}\n'
        f'3. Ник: {answers.get("nickname", "")}\n'
        f'4. ID: {answers.get("id", "")}\n'
        f'5. Часовой пояс (МСК): {answers.get("timezone", "")}\n\n'
        f'📸 Скрины: [тестовые]'
    )

    if leader_id:
        try:
            await callback.bot.send_message(
                leader_id,
                text,
                reply_markup=review_buttons(app_id)
            )
        except Exception as e:
            print(f"Ошибка отправки лидеру: {e}")

    if deputy_id:
        try:
            await callback.bot.send_message(
                deputy_id,
                text,
                reply_markup=review_buttons(app_id)
            )
        except Exception as e:
            print(f"Ошибка отправки заму: {e}")

    await state.clear()

    await callback.message.edit_text(
        f'✅ Тестовая заявка #{app_id} создана!\n'
        f'📨 Отправлена лидеру и заму клана {name}.\n\n'
        f'🧪 Это тестовая заявка — она помечена как "ТЕСТ" в базе данных.',
        reply_markup=admin_menu()
    )
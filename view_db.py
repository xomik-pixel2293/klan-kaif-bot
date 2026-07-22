import sqlite3
import json

DB_PATH = 'klan_kaif.db'


def view_applications(show_test=False):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    if show_test:
        cursor.execute('''
            SELECT a.id, a.user_id, a.username, c.name, a.answers, a.status, a.created_at
            FROM applications a
            JOIN clans c ON a.clan_id = c.id
            WHERE a.username = 'test_user'
            ORDER BY a.created_at DESC
        ''')
        print("🧪 ТЕСТОВЫЕ ЗАЯВКИ:\n")
    else:
        cursor.execute('''
            SELECT a.id, a.user_id, a.username, c.name, a.answers, a.status, a.created_at
            FROM applications a
            JOIN clans c ON a.clan_id = c.id
            WHERE a.username != 'test_user'
            ORDER BY a.created_at DESC
        ''')
        print("📋 ВСЕ ЗАЯВКИ (КРОМЕ ТЕСТОВЫХ):\n")

    rows = cursor.fetchall()

    print("=" * 80)

    for row in rows:
        app_id, user_id, username, clan_name, answers_json, status, created_at = row
        answers = json.loads(answers_json)

        print(f"ID: {app_id}")
        print(f"Клан: {clan_name}")
        print(f"Пользователь: @{username} (ID: {user_id})")
        print(f"Статус: {status}")
        print(f"Дата: {created_at}")
        print(f"Имя: {answers.get('name', '')}")
        print(f"Возраст: {answers.get('age', '')}")
        print(f"Ник: {answers.get('nickname', '')}")
        print(f"ID игровой: {answers.get('id', '')}")
        print(f"Часовой пояс: {answers.get('timezone', '')}")
        print("-" * 40)

    conn.close()


def view_clans():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM clans')
    rows = cursor.fetchall()

    print("\n🏆 КЛАНЫ:\n")
    for row in rows:
        clan_id, name, leader_id, leader_username, leader_name, deputy_id, deputy_username, deputy_name, created_at = row
        print(f"{name}:")
        print(f"  Лидер: {leader_name} (@{leader_username})" if leader_id else "  Лидер: ❌")
        print(f"  Зам: {deputy_name} (@{deputy_username})" if deputy_id else "  Зам: ❌")
        print()

    conn.close()


def view_blacklist():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM blacklist')
    rows = cursor.fetchall()

    print("\n🚫 ЧЁРНЫЙ СПИСОК:\n")
    for row in rows:
        bl_id, user_id, reason, added_by, created_at = row
        print(f"ID: {user_id}")
        print(f"Причина: {reason}")
        print(f"Добавлен: {created_at}")
        print("-" * 30)

    conn.close()


def clear_test():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM applications WHERE username = 'test_user'")
    count = cursor.fetchone()[0]

    if count == 0:
        print("🧪 Нет тестовых заявок для удаления.")
        conn.close()
        return

    print(f"⚠️ Найдено {count} тестовых заявок.")
    confirm = input("Удалить все тестовые заявки? (y/n): ")

    if confirm.lower() == 'y':
        cursor.execute("DELETE FROM applications WHERE username = 'test_user'")
        conn.commit()
        print(f"✅ Удалено {count} тестовых заявок.")
    else:
        print("❌ Отмена.")

    conn.close()


if __name__ == '__main__':
    print("📌 ВЫБЕРИТЕ ДЕЙСТВИЕ:")
    print("1. Показать все кланы")
    print("2. Показать все заявки (кроме тестовых)")
    print("3. Показать только тестовые заявки")
    print("4. Показать чёрный список")
    print("5. Очистить тестовые заявки")

    choice = input("\nВведите номер (1-5): ")

    if choice == '1':
        view_clans()
    elif choice == '2':
        view_applications(show_test=False)
    elif choice == '3':
        view_applications(show_test=True)
    elif choice == '4':
        view_blacklist()
    elif choice == '5':
        clear_test()
    else:
        print("❌ Неверный выбор.")
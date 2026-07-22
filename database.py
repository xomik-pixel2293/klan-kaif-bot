import aiosqlite
import json

DB_PATH = 'klan_kaif.db'


# ============================================================
# 📌 ДАННЫЕ КЛАНОВ (ОБНОВЛЕНЫ!)
# ============================================================

CLANS_DATA = [
    {'id': 1, 'name': 'KAIF', 'leader_id': 8029326399, 'leader_username': 'KAIFLfrik', 'leader_name': 'Лёша',
     'deputy_id': None, 'deputy_username': None, 'deputy_name': None},
    {'id': 2, 'name': 'NA KAIFE', 'leader_id': 7271067034, 'leader_username': 'Vibnot', 'leader_name': 'Катя',
     'deputy_id': 884404620, 'deputy_username': 'KAIFBOOK', 'deputy_name': 'Игорь'},
    {'id': 3, 'name': 'KAIF METRO', 'leader_id': 5590623366, 'leader_username': 'gold_Histori', 'leader_name': 'София',
     'deputy_id': 1622791763, 'deputy_username': 'Xoma9991', 'deputy_name': 'Xoma'},
    {'id': 4, 'name': 'KAIF ESPORTS', 'leader_id': 643813214, 'leader_username': 'vi_sergeeevna',
     'leader_name': 'Виктория', 'deputy_id': 5346986362, 'deputy_username': 'DiamirManager', 'deputy_name': 'Саид'},
]


# ============================================================
# 🗄️ ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# ============================================================

async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        # Таблица кланов
        await db.execute('''
            CREATE TABLE IF NOT EXISTS clans (
                id INTEGER PRIMARY KEY,
                name TEXT UNIQUE NOT NULL,
                leader_id INTEGER,
                leader_username TEXT,
                leader_name TEXT,
                deputy_id INTEGER,
                deputy_username TEXT,
                deputy_name TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица заявок
        await db.execute('''
            CREATE TABLE IF NOT EXISTS applications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                username TEXT,
                clan_id INTEGER NOT NULL,
                answers TEXT NOT NULL,
                photo_old_file_id TEXT,
                photo_new_file_id TEXT,
                has_photos BOOLEAN DEFAULT 0,
                chat_id INTEGER,
                status TEXT DEFAULT 'pending',
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                reviewed_by INTEGER,
                reviewed_at DATETIME,
                FOREIGN KEY (clan_id) REFERENCES clans(id)
            )
        ''')

        # Таблица чёрного списка
        await db.execute('''
            CREATE TABLE IF NOT EXISTS blacklist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                reason TEXT,
                added_by INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Таблица ссылок на чаты кланов
        await db.execute('''
            CREATE TABLE IF NOT EXISTS clan_links (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                clan_id INTEGER NOT NULL,
                chat_link TEXT,
                updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (clan_id) REFERENCES clans(id)
            )
        ''')

        # Заполняем кланы
        for clan in CLANS_DATA:
            await db.execute('''
                INSERT OR IGNORE INTO clans (id, name, leader_id, leader_username, leader_name, deputy_id, deputy_username, deputy_name)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (clan['id'], clan['name'], clan['leader_id'], clan['leader_username'], clan['leader_name'],
                  clan['deputy_id'], clan['deputy_username'], clan['deputy_name']))

        await db.commit()


# ============================================================
# 📋 ФУНКЦИИ РАБОТЫ С КЛАНАМИ
# ============================================================

async def get_clans():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT * FROM clans ORDER BY id') as cursor:
            return await cursor.fetchall()


async def get_clan(clan_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT * FROM clans WHERE id = ?', (clan_id,)) as cursor:
            return await cursor.fetchone()


async def get_clan_by_name(name):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT * FROM clans WHERE name = ?', (name,)) as cursor:
            return await cursor.fetchone()


async def get_clan_by_user(user_id):
    """Найти клан, где user_id является лидером или замом"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT * FROM clans WHERE leader_id = ? OR deputy_id = ?', (user_id, user_id)) as cursor:
            return await cursor.fetchone()


# ============================================================
# 👥 ФУНКЦИИ УПРАВЛЕНИЯ РУКОВОДИТЕЛЯМИ
# ============================================================

async def update_clan_leader(clan_id, leader_id, leader_username, leader_name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            UPDATE clans SET leader_id = ?, leader_username = ?, leader_name = ?
            WHERE id = ?
        ''', (leader_id, leader_username, leader_name, clan_id))
        await db.commit()


async def update_clan_deputy(clan_id, deputy_id, deputy_username, deputy_name):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            UPDATE clans SET deputy_id = ?, deputy_username = ?, deputy_name = ?
            WHERE id = ?
        ''', (deputy_id, deputy_username, deputy_name, clan_id))
        await db.commit()


async def remove_clan_leader(clan_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            UPDATE clans SET leader_id = NULL, leader_username = NULL, leader_name = NULL
            WHERE id = ?
        ''', (clan_id,))
        await db.commit()


async def remove_clan_deputy(clan_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            UPDATE clans SET deputy_id = NULL, deputy_username = NULL, deputy_name = NULL
            WHERE id = ?
        ''', (clan_id,))
        await db.commit()


# ============================================================
# 📝 ФУНКЦИИ РАБОТЫ С ЗАЯВКАМИ
# ============================================================

async def add_application(user_id, username, clan_id, answers):
    answers_json = json.dumps(answers, ensure_ascii=False)
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute('''
            INSERT INTO applications (user_id, username, clan_id, answers)
            VALUES (?, ?, ?, ?)
        ''', (user_id, username, clan_id, answers_json))
        await db.commit()
        return cursor.lastrowid


async def update_application_photo_old(app_id, photo_old_file_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE applications SET photo_old_file_id = ? WHERE id = ?', (photo_old_file_id, app_id))
        await db.commit()


async def update_application_photo_new(app_id, photo_new_file_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE applications SET photo_new_file_id = ? WHERE id = ?', (photo_new_file_id, app_id))
        await db.commit()


async def update_application_chat(app_id, chat_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('UPDATE applications SET chat_id = ? WHERE id = ?', (chat_id, app_id))
        await db.commit()


async def get_user_applications(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT a.*, c.name as clan_name 
            FROM applications a
            JOIN clans c ON a.clan_id = c.id
            WHERE a.user_id = ?
            ORDER BY a.created_at DESC
        ''', (user_id,)) as cursor:
            return await cursor.fetchall()


async def get_application_by_id(app_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT a.*, c.name as clan_name 
            FROM applications a
            JOIN clans c ON a.clan_id = c.id
            WHERE a.id = ?
        ''', (app_id,)) as cursor:
            return await cursor.fetchone()


async def get_pending_application(user_id, clan_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT * FROM applications WHERE user_id = ? AND clan_id = ? AND status = "pending"',
                              (user_id, clan_id)) as cursor:
            return await cursor.fetchone()


async def update_application_status(app_id, status, reviewer_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            UPDATE applications 
            SET status = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, reviewer_id, app_id))
        await db.commit()


async def revoke_application(app_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("UPDATE applications SET status = 'revoked' WHERE id = ?", (app_id,))
        await db.commit()


async def get_clan_applications(clan_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT a.*, c.name as clan_name 
            FROM applications a
            JOIN clans c ON a.clan_id = c.id
            WHERE a.clan_id = ?
            ORDER BY a.created_at DESC
        ''', (clan_id,)) as cursor:
            return await cursor.fetchall()


# ============================================================
# 🚫 ФУНКЦИИ РАБОТЫ С ЧЁРНЫМ СПИСКОМ
# ============================================================

async def is_in_blacklist(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT * FROM blacklist WHERE user_id = ?', (user_id,)) as cursor:
            return await cursor.fetchone()


async def add_to_blacklist(user_id, reason, added_by):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT OR REPLACE INTO blacklist (user_id, reason, added_by)
            VALUES (?, ?, ?)
        ''', (user_id, reason, added_by))
        await db.commit()


async def remove_from_blacklist(user_id):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('DELETE FROM blacklist WHERE user_id = ?', (user_id,))
        await db.commit()


async def get_blacklist():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT * FROM blacklist ORDER BY created_at DESC') as cursor:
            return await cursor.fetchall()


# ============================================================
# 📊 ФУНКЦИИ ДЛЯ АДМИНОВ (СТАТИСТИКА, ЭКСПОРТ)
# ============================================================

async def get_statistics():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT 
                COUNT(*) as total,
                SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) as accepted,
                SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected,
                SUM(CASE WHEN status = 'revoked' THEN 1 ELSE 0 END) as revoked
            FROM applications
        ''') as cursor:
            stats = await cursor.fetchone()

        async with db.execute('''
            SELECT c.name, COUNT(a.id) as count
            FROM clans c
            LEFT JOIN applications a ON c.id = a.clan_id
            GROUP BY c.id
        ''') as cursor:
            by_clan = await cursor.fetchall()

        return stats, by_clan


async def get_all_applications():
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT 
                a.id, a.user_id, a.username, c.name as clan_name, a.answers,
                a.photo_old_file_id, a.photo_new_file_id, a.has_photos,
                a.status, a.created_at, a.reviewed_by, a.reviewed_at
            FROM applications a
            JOIN clans c ON a.clan_id = c.id
            ORDER BY a.created_at DESC
        ''') as cursor:
            return await cursor.fetchall()


# ============================================================
# 🔗 ФУНКЦИИ РАБОТЫ СО ССЫЛКАМИ НА ЧАТЫ КЛАНОВ
# ============================================================

async def get_clan_link(clan_id):
    """Получить ссылку на чат клана"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('SELECT chat_link FROM clan_links WHERE clan_id = ?', (clan_id,)) as cursor:
            result = await cursor.fetchone()
            return result[0] if result else None


async def set_clan_link(clan_id, chat_link):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute('''
            INSERT OR REPLACE INTO clan_links (clan_id, chat_link, updated_at)
            VALUES (?, ?, CURRENT_TIMESTAMP)
        ''', (clan_id, chat_link))
        await db.commit()


async def get_all_clan_links():
    """Получить все ссылки кланов"""
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute('''
            SELECT c.name, cl.chat_link, cl.updated_at
            FROM clan_links cl
            JOIN clans c ON cl.clan_id = c.id
        ''') as cursor:
            return await cursor.fetchall()


# ============================================================
# 🗑 ОЧИСТКА ТЕСТОВЫХ ЗАЯВОК
# ============================================================

async def clear_test_applications():
    """Удалить все тестовые заявки (username = 'test_user')"""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM applications WHERE username = 'test_user'")
        await db.commit()
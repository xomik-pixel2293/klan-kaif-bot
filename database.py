import asyncpg
import json
import os
from datetime import datetime

# ============================================================
# 📌 ДАННЫЕ КЛАНОВ
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
# 🔌 ПОДКЛЮЧЕНИЕ К БД
# ============================================================

def get_database_url():
    """Получить URL базы данных из переменных окружения"""
    # Приоритет: Supabase > локальная SQLite
    url = os.getenv('DATABASE_URL')
    if url:
        return url
    return None


async def get_connection():
    """Получить подключение к БД (Supabase или SQLite)"""
    url = get_database_url()
    if url:
        # Используем Supabase (PostgreSQL)
        return await asyncpg.connect(url)
    else:
        # Используем SQLite (локально)
        import aiosqlite
        return await aiosqlite.connect('klan_kaif.db')


# ============================================================
# 🗄️ ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# ============================================================

async def init_db():
    """Создать таблицы (если их нет)"""
    url = get_database_url()
    
    if url:
        # ==================== SUPABASE ====================
        conn = await asyncpg.connect(url)
        try:
            # Таблица кланов
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS clans (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    leader_id INTEGER,
                    leader_username TEXT,
                    leader_name TEXT,
                    deputy_id INTEGER,
                    deputy_username TEXT,
                    deputy_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица заявок
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS applications (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    username TEXT,
                    clan_id INTEGER NOT NULL,
                    answers TEXT NOT NULL,
                    photo_old_file_id TEXT,
                    photo_new_file_id TEXT,
                    has_photos INTEGER DEFAULT 0,
                    chat_id INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    reviewed_by INTEGER,
                    reviewed_at TIMESTAMP
                )
            ''')
            
            # Таблица чёрного списка
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS blacklist (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER NOT NULL UNIQUE,
                    reason TEXT,
                    added_by INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Таблица ссылок на чаты
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS clan_links (
                    id SERIAL PRIMARY KEY,
                    clan_id INTEGER NOT NULL,
                    chat_link TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Заполняем кланы (если пусто)
            for clan in CLANS_DATA:
                await conn.execute('''
                    INSERT INTO clans (id, name, leader_id, leader_username, leader_name, deputy_id, deputy_username, deputy_name)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
                    ON CONFLICT (id) DO NOTHING
                ''', clan['id'], clan['name'], clan['leader_id'], clan['leader_username'], clan['leader_name'],
                    clan['deputy_id'], clan['deputy_username'], clan['deputy_name'])
            
            print("✅ Supabase подключена и инициализирована!")
        except Exception as e:
            print(f"❌ Ошибка при инициализации Supabase: {e}")
        finally:
            await conn.close()
    else:
        # ==================== SQLITE (локально) ====================
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
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
                    has_photos INTEGER DEFAULT 0,
                    chat_id INTEGER,
                    status TEXT DEFAULT 'pending',
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    reviewed_by INTEGER,
                    reviewed_at DATETIME
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
            
            # Таблица ссылок на чаты
            await db.execute('''
                CREATE TABLE IF NOT EXISTS clan_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clan_id INTEGER NOT NULL,
                    chat_link TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
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
            print("✅ SQLite инициализирована (локальный режим)")


# ============================================================
# 📋 ФУНКЦИИ РАБОТЫ С КЛАНАМИ
# ============================================================

async def get_clans():
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            rows = await conn.fetch('SELECT * FROM clans ORDER BY id')
            return [tuple(row) for row in rows]
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            cursor = await db.execute('SELECT * FROM clans ORDER BY id')
            return await cursor.fetchall()


async def get_clan(clan_id):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            row = await conn.fetchrow('SELECT * FROM clans WHERE id = $1', clan_id)
            return tuple(row) if row else None
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            cursor = await db.execute('SELECT * FROM clans WHERE id = ?', (clan_id,))
            return await cursor.fetchone()


async def get_clan_by_name(name):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            row = await conn.fetchrow('SELECT * FROM clans WHERE name = $1', name)
            return tuple(row) if row else None
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            cursor = await db.execute('SELECT * FROM clans WHERE name = ?', (name,))
            return await cursor.fetchone()


async def get_clan_by_user(user_id):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            row = await conn.fetchrow('SELECT * FROM clans WHERE leader_id = $1 OR deputy_id = $1', user_id)
            return tuple(row) if row else None
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            cursor = await db.execute('SELECT * FROM clans WHERE leader_id = ? OR deputy_id = ?', (user_id, user_id))
            return await cursor.fetchone()


# ============================================================
# 👥 ФУНКЦИИ УПРАВЛЕНИЯ РУКОВОДИТЕЛЯМИ
# ============================================================

async def update_clan_leader(clan_id, leader_id, leader_username, leader_name):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute('''
                UPDATE clans SET leader_id = $1, leader_username = $2, leader_name = $3
                WHERE id = $4
            ''', leader_id, leader_username, leader_name, clan_id)
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            await db.execute('''
                UPDATE clans SET leader_id = ?, leader_username = ?, leader_name = ?
                WHERE id = ?
            ''', (leader_id, leader_username, leader_name, clan_id))
            await db.commit()


async def update_clan_deputy(clan_id, deputy_id, deputy_username, deputy_name):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute('''
                UPDATE clans SET deputy_id = $1, deputy_username = $2, deputy_name = $3
                WHERE id = $4
            ''', deputy_id, deputy_username, deputy_name, clan_id)
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            await db.execute('''
                UPDATE clans SET deputy_id = ?, deputy_username = ?, deputy_name = ?
                WHERE id = ?
            ''', (deputy_id, deputy_username, deputy_name, clan_id))
            await db.commit()


async def remove_clan_leader(clan_id):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute('''
                UPDATE clans SET leader_id = NULL, leader_username = NULL, leader_name = NULL
                WHERE id = $1
            ''', clan_id)
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            await db.execute('''
                UPDATE clans SET leader_id = NULL, leader_username = NULL, leader_name = NULL
                WHERE id = ?
            ''', (clan_id,))
            await db.commit()


async def remove_clan_deputy(clan_id):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute('''
                UPDATE clans SET deputy_id = NULL, deputy_username = NULL, deputy_name = NULL
                WHERE id = $1
            ''', clan_id)
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
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
    url = get_database_url()
    
    if url:
        conn = await asyncpg.connect(url)
        try:
            row = await conn.fetchrow('''
                INSERT INTO applications (user_id, username, clan_id, answers)
                VALUES ($1, $2, $3, $4)
                RETURNING id
            ''', user_id, username, clan_id, answers_json)
            return row['id']
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            cursor = await db.execute('''
                INSERT INTO applications (user_id, username, clan_id, answers)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, clan_id, answers_json))
            await db.commit()
            return cursor.lastrowid


async def update_application_photo_old(app_id, photo_old_file_id):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute('UPDATE applications SET photo_old_file_id = $1 WHERE id = $2', photo_old_file_id, app_id)
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            await db.execute('UPDATE applications SET photo_old_file_id = ? WHERE id = ?', (photo_old_file_id, app_id))
            await db.commit()


async def update_application_photo_new(app_id, photo_new_file_id):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute('UPDATE applications SET photo_new_file_id = $1 WHERE id = $2', photo_new_file_id, app_id)
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            await db.execute('UPDATE applications SET photo_new_file_id = ? WHERE id = ?', (photo_new_file_id, app_id))
            await db.commit()


async def update_application_has_photos(app_id, count):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute('UPDATE applications SET has_photos = $1 WHERE id = $2', count, app_id)
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            await db.execute('UPDATE applications SET has_photos = ? WHERE id = ?', (count, app_id))
            await db.commit()


async def update_application_chat(app_id, chat_id):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute('UPDATE applications SET chat_id = $1 WHERE id = $2', chat_id, app_id)
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            await db.execute('UPDATE applications SET chat_id = ? WHERE id = ?', (chat_id, app_id))
            await db.commit()


async def get_user_applications(user_id):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            rows = await conn.fetch('''
                SELECT a.*, c.name as clan_name 
                FROM applications a
                JOIN clans c ON a.clan_id = c.id
                WHERE a.user_id = $1
                ORDER BY a.created_at DESC
            ''', user_id)
            return [tuple(row) for row in rows]
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            cursor = await db.execute('''
                SELECT a.*, c.name as clan_name 
                FROM applications a
                JOIN clans c ON a.clan_id = c.id
                WHERE a.user_id = ?
                ORDER BY a.created_at DESC
            ''', (user_id,))
            return await cursor.fetchall()


async def get_application_by_id(app_id):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            row = await conn.fetchrow('''
                SELECT a.*, c.name as clan_name 
                FROM applications a
                JOIN clans c ON a.clan_id = c.id
                WHERE a.id = $1
            ''', app_id)
            return tuple(row) if row else None
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            cursor = await db.execute('''
                SELECT a.*, c.name as clan_name 
                FROM applications a
                JOIN clans c ON a.clan_id = c.id
                WHERE a.id = ?
            ''', (app_id,))
            return await cursor.fetchone()


async def get_pending_application(user_id, clan_id):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            row = await conn.fetchrow('''
                SELECT * FROM applications WHERE user_id = $1 AND clan_id = $2 AND status = 'pending'
            ''', user_id, clan_id)
            return tuple(row) if row else None
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            cursor = await db.execute('''
                SELECT * FROM applications WHERE user_id = ? AND clan_id = ? AND status = "pending"
            ''', (user_id, clan_id))
            return await cursor.fetchone()


async def update_application_status(app_id, status, reviewer_id):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute('''
                UPDATE applications 
                SET status = $1, reviewed_by = $2, reviewed_at = CURRENT_TIMESTAMP
                WHERE id = $3
            ''', status, reviewer_id, app_id)
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            await db.execute('''
                UPDATE applications 
                SET status = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP
                WHERE id = ?
            ''', (status, reviewer_id, app_id))
            await db.commit()


async def revoke_application(app_id):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute("UPDATE applications SET status = 'revoked' WHERE id = $1", app_id)
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            await db.execute("UPDATE applications SET status = 'revoked' WHERE id = ?", (app_id,))
            await db.commit()


async def get_clan_applications(clan_id):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            rows = await conn.fetch('''
                SELECT a.*, c.name as clan_name 
                FROM applications a
                JOIN clans c ON a.clan_id = c.id
                WHERE a.clan_id = $1
                ORDER BY a.created_at DESC
            ''', clan_id)
            return [tuple(row) for row in rows]
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            cursor = await db.execute('''
                SELECT a.*, c.name as clan_name 
                FROM applications a
                JOIN clans c ON a.clan_id = c.id
                WHERE a.clan_id = ?
                ORDER BY a.created_at DESC
            ''', (clan_id,))
            return await cursor.fetchall()


# ============================================================
# 🚫 ФУНКЦИИ РАБОТЫ С ЧЁРНЫМ СПИСКОМ
# ============================================================

async def is_in_blacklist(user_id):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            row = await conn.fetchrow('SELECT * FROM blacklist WHERE user_id = $1', user_id)
            return row is not None
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            cursor = await db.execute('SELECT * FROM blacklist WHERE user_id = ?', (user_id,))
            return await cursor.fetchone()


async def add_to_blacklist(user_id, reason, added_by):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute('''
                INSERT INTO blacklist (user_id, reason, added_by)
                VALUES ($1, $2, $3)
                ON CONFLICT (user_id) DO UPDATE SET reason = $2, added_by = $3
            ''', user_id, reason, added_by)
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            await db.execute('''
                INSERT OR REPLACE INTO blacklist (user_id, reason, added_by)
                VALUES (?, ?, ?)
            ''', (user_id, reason, added_by))
            await db.commit()


async def remove_from_blacklist(user_id):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute('DELETE FROM blacklist WHERE user_id = $1', user_id)
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            await db.execute('DELETE FROM blacklist WHERE user_id = ?', (user_id,))
            await db.commit()


async def get_blacklist():
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            rows = await conn.fetch('SELECT * FROM blacklist ORDER BY created_at DESC')
            return [tuple(row) for row in rows]
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            cursor = await db.execute('SELECT * FROM blacklist ORDER BY created_at DESC')
            return await cursor.fetchall()


# ============================================================
# 📊 ФУНКЦИИ ДЛЯ АДМИНОВ
# ============================================================

async def get_statistics():
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            stats = await conn.fetchrow('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) as accepted,
                    SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected,
                    SUM(CASE WHEN status = 'revoked' THEN 1 ELSE 0 END) as revoked
                FROM applications
            ''')
            
            by_clan = await conn.fetch('''
                SELECT c.name, COUNT(a.id) as count
                FROM clans c
                LEFT JOIN applications a ON c.id = a.clan_id
                GROUP BY c.id
            ''')
            
            return (stats['total'], stats['pending'], stats['accepted'], 
                    stats['rejected'], stats['revoked']), [(row['name'], row['count']) for row in by_clan]
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            stats_cursor = await db.execute('''
                SELECT 
                    COUNT(*) as total,
                    SUM(CASE WHEN status = 'pending' THEN 1 ELSE 0 END) as pending,
                    SUM(CASE WHEN status = 'accepted' THEN 1 ELSE 0 END) as accepted,
                    SUM(CASE WHEN status = 'rejected' THEN 1 ELSE 0 END) as rejected,
                    SUM(CASE WHEN status = 'revoked' THEN 1 ELSE 0 END) as revoked
                FROM applications
            ''')
            stats = await stats_cursor.fetchone()
            
            by_clan_cursor = await db.execute('''
                SELECT c.name, COUNT(a.id) as count
                FROM clans c
                LEFT JOIN applications a ON c.id = a.clan_id
                GROUP BY c.id
            ''')
            by_clan = await by_clan_cursor.fetchall()
            
            return stats, by_clan


async def get_all_applications():
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            rows = await conn.fetch('''
                SELECT 
                    a.id, a.user_id, a.username, c.name as clan_name, a.answers,
                    a.photo_old_file_id, a.photo_new_file_id, a.has_photos,
                    a.status, a.created_at, a.reviewed_by, a.reviewed_at
                FROM applications a
                JOIN clans c ON a.clan_id = c.id
                ORDER BY a.created_at DESC
            ''')
            return [tuple(row) for row in rows]
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            cursor = await db.execute('''
                SELECT 
                    a.id, a.user_id, a.username, c.name as clan_name, a.answers,
                    a.photo_old_file_id, a.photo_new_file_id, a.has_photos,
                    a.status, a.created_at, a.reviewed_by, a.reviewed_at
                FROM applications a
                JOIN clans c ON a.clan_id = c.id
                ORDER BY a.created_at DESC
            ''')
            return await cursor.fetchall()


# ============================================================
# 🔗 ФУНКЦИИ РАБОТЫ СО ССЫЛКАМИ
# ============================================================

async def get_clan_link(clan_id):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            row = await conn.fetchrow('SELECT chat_link FROM clan_links WHERE clan_id = $1', clan_id)
            return row['chat_link'] if row else None
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            cursor = await db.execute('SELECT chat_link FROM clan_links WHERE clan_id = ?', (clan_id,))
            result = await cursor.fetchone()
            return result[0] if result else None


async def set_clan_link(clan_id, chat_link):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute('''
                INSERT INTO clan_links (clan_id, chat_link, updated_at)
                VALUES ($1, $2, CURRENT_TIMESTAMP)
                ON CONFLICT (clan_id) DO UPDATE SET chat_link = $2, updated_at = CURRENT_TIMESTAMP
            ''', clan_id, chat_link)
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            await db.execute('''
                INSERT OR REPLACE INTO clan_links (clan_id, chat_link, updated_at)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            ''', (clan_id, chat_link))
            await db.commit()


async def get_all_clan_links():
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            rows = await conn.fetch('''
                SELECT c.name, cl.chat_link, cl.updated_at
                FROM clan_links cl
                JOIN clans c ON cl.clan_id = c.id
            ''')
            return [(row['name'], row['chat_link'], row['updated_at']) for row in rows]
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            cursor = await db.execute('''
                SELECT c.name, cl.chat_link, cl.updated_at
                FROM clan_links cl
                JOIN clans c ON cl.clan_id = c.id
            ''')
            return await cursor.fetchall()


# ============================================================
# 🗑 ОЧИСТКА ТЕСТОВЫХ ЗАЯВОК
# ============================================================

async def clear_test_applications():
    """Удалить все тестовые заявки (username = 'test_user')"""
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute("DELETE FROM applications WHERE username = 'test_user'")
        finally:
            await conn.close()
    else:
        import aiosqlite
        async with aiosqlite.connect('klan_kaif.db') as db:
            await db.execute("DELETE FROM applications WHERE username = 'test_user'")
            await db.commit()

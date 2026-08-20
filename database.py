import asyncpg
import aiosqlite
import json
import os
from datetime import datetime

DB_PATH = 'klan_kaif.db'


# ============================================================
# 🔌 ПОДКЛЮЧЕНИЕ К БД
# ============================================================

def get_database_url():
    url = os.getenv('DATABASE_URL')
    if url:
        return url
    return None


async def get_connection():
    url = get_database_url()
    if url:
        return await asyncpg.connect(url)
    else:
        return await aiosqlite.connect(DB_PATH)


# ============================================================
# 🗄️ ИНИЦИАЛИЗАЦИЯ БАЗЫ ДАННЫХ
# ============================================================

async def init_db():
    url = get_database_url()
    
    if url:
        conn = await asyncpg.connect(url)
        try:
            # Добавляем колонки если их нет
            try:
                await conn.execute('ALTER TABLE clans ADD COLUMN emoji TEXT DEFAULT "🔵"')
                print("✅ Добавлена колонка emoji")
            except Exception as e:
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    pass
                else:
                    print(f"⚠️ Ошибка при добавлении emoji: {e}")
            
            try:
                await conn.execute('ALTER TABLE clans ADD COLUMN is_active BOOLEAN DEFAULT TRUE')
                print("✅ Добавлена колонка is_active")
            except Exception as e:
                if 'already exists' in str(e).lower() or 'duplicate' in str(e).lower():
                    pass
                else:
                    print(f"⚠️ Ошибка при добавлении is_active: {e}")
            
            print("✅ База данных подключена и инициализирована!")
        except Exception as e:
            print(f"❌ Ошибка при инициализации: {e}")
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('''
                CREATE TABLE IF NOT EXISTS clans (
                    id INTEGER PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    emoji TEXT,
                    leader_id INTEGER,
                    leader_username TEXT,
                    leader_name TEXT,
                    deputy_id INTEGER,
                    deputy_username TEXT,
                    deputy_name TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
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
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS blacklist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL UNIQUE,
                    reason TEXT,
                    added_by INTEGER,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            await db.execute('''
                CREATE TABLE IF NOT EXISTS clan_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    clan_id INTEGER NOT NULL,
                    chat_link TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            try:
                await db.execute('ALTER TABLE clans ADD COLUMN is_active INTEGER DEFAULT 1')
            except:
                pass
            
            try:
                await db.execute('ALTER TABLE clans ADD COLUMN emoji TEXT DEFAULT "🔵"')
            except:
                pass
            
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
        async with aiosqlite.connect(DB_PATH) as db:
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
        async with aiosqlite.connect(DB_PATH) as db:
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
        async with aiosqlite.connect(DB_PATH) as db:
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
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('SELECT * FROM clans WHERE leader_id = ? OR deputy_id = ?', (user_id, user_id))
            return await cursor.fetchone()


# ============================================================
# 🔄 СТАТУСЫ КЛАНОВ
# ============================================================

async def get_clans_with_status():
    url = get_database_url()
    if url:
        try:
            conn = await asyncpg.connect(url)
            try:
                rows = await conn.fetch('SELECT id, name, emoji, is_active FROM clans ORDER BY id')
                return [(row['id'], row['name'], row['emoji'], row['is_active']) for row in rows]
            finally:
                await conn.close()
        except Exception as e:
            print(f"❌ Ошибка get_clans_with_status: {e}")
            return []
    else:
        try:
            async with aiosqlite.connect(DB_PATH) as db:
                cursor = await db.execute('SELECT id, name, emoji, is_active FROM clans ORDER BY id')
                rows = await cursor.fetchall()
                return [(row[0], row[1], row[2], bool(row[3])) for row in rows]
        except Exception as e:
            print(f"❌ Ошибка get_clans_with_status: {e}")
            return []


async def set_clan_active(clan_id: int, is_active: bool):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute('UPDATE clans SET is_active = $1 WHERE id = $2', is_active, clan_id)
            print(f"✅ Статус клана {clan_id} изменён на {is_active}")
        except Exception as e:
            print(f"❌ Ошибка при обновлении статуса: {e}")
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('UPDATE clans SET is_active = ? WHERE id = ?', (1 if is_active else 0, clan_id))
            await db.commit()
            print(f"✅ Статус клана {clan_id} изменён на {is_active}")


async def get_clan_active_status(clan_id: int) -> bool:
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            row = await conn.fetchrow('SELECT is_active FROM clans WHERE id = $1', clan_id)
            return row['is_active'] if row else True
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('SELECT is_active FROM clans WHERE id = ?', (clan_id,))
            row = await cursor.fetchone()
            return bool(row[0]) if row else True


# ============================================================
# 👥 УПРАВЛЕНИЕ РУКОВОДИТЕЛЯМИ
# ============================================================

async def update_clan_leader(clan_id, leader_id, leader_username, leader_name):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute('UPDATE clans SET leader_id = $1, leader_username = $2, leader_name = $3 WHERE id = $4',
                               leader_id, leader_username, leader_name, clan_id)
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('UPDATE clans SET leader_id = ?, leader_username = ?, leader_name = ? WHERE id = ?',
                             (leader_id, leader_username, leader_name, clan_id))
            await db.commit()


async def update_clan_deputy(clan_id, deputy_id, deputy_username, deputy_name):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute('UPDATE clans SET deputy_id = $1, deputy_username = $2, deputy_name = $3 WHERE id = $4',
                               deputy_id, deputy_username, deputy_name, clan_id)
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('UPDATE clans SET deputy_id = ?, deputy_username = ?, deputy_name = ? WHERE id = ?',
                             (deputy_id, deputy_username, deputy_name, clan_id))
            await db.commit()


async def remove_clan_leader(clan_id):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute('UPDATE clans SET leader_id = NULL, leader_username = NULL, leader_name = NULL WHERE id = $1', clan_id)
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('UPDATE clans SET leader_id = NULL, leader_username = NULL, leader_name = NULL WHERE id = ?', (clan_id,))
            await db.commit()


async def remove_clan_deputy(clan_id):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute('UPDATE clans SET deputy_id = NULL, deputy_username = NULL, deputy_name = NULL WHERE id = $1', clan_id)
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('UPDATE clans SET deputy_id = NULL, deputy_username = NULL, deputy_name = NULL WHERE id = ?', (clan_id,))
            await db.commit()


# ============================================================
# 🏗️ ДОБАВЛЕНИЕ И УДАЛЕНИЕ КЛАНОВ
# ============================================================

async def add_clan(name: str, emoji: str = '🔵', leader_id: int = None, 
                   leader_username: str = None, leader_name: str = None,
                   deputy_id: int = None, deputy_username: str = None, 
                   deputy_name: str = None) -> int:
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            max_id = await conn.fetchval('SELECT COALESCE(MAX(id), 0) + 1 FROM clans')
            await conn.execute('''
                INSERT INTO clans (id, name, emoji, leader_id, leader_username, leader_name, deputy_id, deputy_username, deputy_name, is_active)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, TRUE)
            ''', max_id, name, emoji, leader_id, leader_username, leader_name,
                deputy_id, deputy_username, deputy_name)
            return max_id
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('SELECT COALESCE(MAX(id), 0) + 1 FROM clans')
            max_id = (await cursor.fetchone())[0]
            await db.execute('''
                INSERT INTO clans (id, name, emoji, leader_id, leader_username, leader_name, deputy_id, deputy_username, deputy_name, is_active)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
            ''', (max_id, name, emoji, leader_id, leader_username, leader_name,
                  deputy_id, deputy_username, deputy_name))
            await db.commit()
            return max_id


async def delete_clan(clan_id: int) -> bool:
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute('DELETE FROM applications WHERE clan_id = $1', clan_id)
            await conn.execute('DELETE FROM clan_links WHERE clan_id = $1', clan_id)
            await conn.execute('DELETE FROM clans WHERE id = $1', clan_id)
            return True
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('DELETE FROM applications WHERE clan_id = ?', (clan_id,))
            await db.execute('DELETE FROM clan_links WHERE clan_id = ?', (clan_id,))
            await db.execute('DELETE FROM clans WHERE id = ?', (clan_id,))
            await db.commit()
            return True


async def update_clan(clan_id: int, name: str = None, emoji: str = None,
                      leader_id: int = None, leader_username: str = None, leader_name: str = None,
                      deputy_id: int = None, deputy_username: str = None, deputy_name: str = None):
    url = get_database_url()
    
    updates = []
    params = []
    param_index = 1
    
    if name is not None:
        updates.append(f"name = ${param_index}")
        params.append(name)
        param_index += 1
    if emoji is not None:
        updates.append(f"emoji = ${param_index}")
        params.append(emoji)
        param_index += 1
    if leader_id is not None:
        updates.append(f"leader_id = ${param_index}")
        params.append(leader_id)
        param_index += 1
    if leader_username is not None:
        updates.append(f"leader_username = ${param_index}")
        params.append(leader_username)
        param_index += 1
    if leader_name is not None:
        updates.append(f"leader_name = ${param_index}")
        params.append(leader_name)
        param_index += 1
    if deputy_id is not None:
        updates.append(f"deputy_id = ${param_index}")
        params.append(deputy_id)
        param_index += 1
    if deputy_username is not None:
        updates.append(f"deputy_username = ${param_index}")
        params.append(deputy_username)
        param_index += 1
    if deputy_name is not None:
        updates.append(f"deputy_name = ${param_index}")
        params.append(deputy_name)
        param_index += 1
    
    if not updates:
        return False
    
    params.append(clan_id)
    query = f"UPDATE clans SET {', '.join(updates)} WHERE id = ${param_index}"
    
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute(query, *params)
            return True
        finally:
            await conn.close()
    else:
        placeholders = [f"{col.split(' ')[0]} = ?" for col in updates]
        sqlite_params = [p for p in params[:-1]] + [clan_id]
        query = f"UPDATE clans SET {', '.join(placeholders)} WHERE id = ?"
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute(query, sqlite_params)
            await db.commit()
            return True


# ============================================================
# 📝 ФУНКЦИИ РАБОТЫ С ЗАЯВКАМИ
# ============================================================

async def add_application(user_id, username, clan_id, answers):
    answers_json = json.dumps(answers, ensure_ascii=False)
    url = get_database_url()
    
    if url:
        conn = await asyncpg.connect(url)
        try:
            row = await conn.fetchrow('INSERT INTO applications (user_id, username, clan_id, answers) VALUES ($1, $2, $3, $4) RETURNING id',
                                      user_id, username, clan_id, answers_json)
            return row['id']
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('INSERT INTO applications (user_id, username, clan_id, answers) VALUES (?, ?, ?, ?)',
                                      (user_id, username, clan_id, answers_json))
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
        async with aiosqlite.connect(DB_PATH) as db:
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
        async with aiosqlite.connect(DB_PATH) as db:
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
        async with aiosqlite.connect(DB_PATH) as db:
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
        async with aiosqlite.connect(DB_PATH) as db:
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
        async with aiosqlite.connect(DB_PATH) as db:
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
        async with aiosqlite.connect(DB_PATH) as db:
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
            row = await conn.fetchrow('SELECT * FROM applications WHERE user_id = $1 AND clan_id = $2 AND status = $3',
                                      user_id, clan_id, 'pending')
            return tuple(row) if row else None
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('SELECT * FROM applications WHERE user_id = ? AND clan_id = ? AND status = "pending"',
                                      (user_id, clan_id))
            return await cursor.fetchone()


async def update_application_status(app_id, status, reviewer_id):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute('UPDATE applications SET status = $1, reviewed_by = $2, reviewed_at = CURRENT_TIMESTAMP WHERE id = $3',
                               status, reviewer_id, app_id)
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('UPDATE applications SET status = ?, reviewed_by = ?, reviewed_at = CURRENT_TIMESTAMP WHERE id = ?',
                             (status, reviewer_id, app_id))
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
        async with aiosqlite.connect(DB_PATH) as db:
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
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('''
                SELECT a.*, c.name as clan_name 
                FROM applications a
                JOIN clans c ON a.clan_id = c.id
                WHERE a.clan_id = ?
                ORDER BY a.created_at DESC
            ''', (clan_id,))
            return await cursor.fetchall()


# ============================================================
# 🚫 ЧЁРНЫЙ СПИСОК
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
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('SELECT * FROM blacklist WHERE user_id = ?', (user_id,))
            return await cursor.fetchone() is not None


async def add_to_blacklist(user_id, reason, added_by):
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute('INSERT INTO blacklist (user_id, reason, added_by) VALUES ($1, $2, $3) ON CONFLICT (user_id) DO UPDATE SET reason = $2, added_by = $3',
                               user_id, reason, added_by)
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute('INSERT OR REPLACE INTO blacklist (user_id, reason, added_by) VALUES (?, ?, ?)',
                             (user_id, reason, added_by))
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
        async with aiosqlite.connect(DB_PATH) as db:
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
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('SELECT * FROM blacklist ORDER BY created_at DESC')
            return await cursor.fetchall()


# ============================================================
# 📊 СТАТИСТИКА
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
        async with aiosqlite.connect(DB_PATH) as db:
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
        async with aiosqlite.connect(DB_PATH) as db:
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
# 🔗 ССЫЛКИ
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
        async with aiosqlite.connect(DB_PATH) as db:
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
        async with aiosqlite.connect(DB_PATH) as db:
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
        async with aiosqlite.connect(DB_PATH) as db:
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
    url = get_database_url()
    if url:
        conn = await asyncpg.connect(url)
        try:
            await conn.execute("DELETE FROM applications WHERE username = 'test_user'")
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            await db.execute("DELETE FROM applications WHERE username = 'test_user'")
            await db.commit()


# ============================================================
# 🔔 НАПОМИНАНИЯ
# ============================================================

async def get_old_pending_applications():
    from datetime import datetime, timedelta
    url = get_database_url()
    cutoff = datetime.now() - timedelta(hours=24)
    
    if url:
        conn = await asyncpg.connect(url)
        try:
            rows = await conn.fetch('''
                SELECT a.*, c.name as clan_name, c.leader_id, c.leader_username, c.leader_name,
                       c.deputy_id, c.deputy_username, c.deputy_name
                FROM applications a
                JOIN clans c ON a.clan_id = c.id
                WHERE a.status = 'pending' AND a.created_at < $1
                ORDER BY a.created_at ASC
            ''', cutoff)
            return [tuple(row) for row in rows]
        finally:
            await conn.close()
    else:
        async with aiosqlite.connect(DB_PATH) as db:
            cursor = await db.execute('''
                SELECT a.*, c.name as clan_name, c.leader_id, c.leader_username, c.leader_name,
                       c.deputy_id, c.deputy_username, c.deputy_name
                FROM applications a
                JOIN clans c ON a.clan_id = c.id
                WHERE a.status = 'pending' AND a.created_at < datetime('now', '-1 day')
                ORDER BY a.created_at ASC
            ''')
            return await cursor.fetchall()


# ============================================================
# 🔌 SUPABASE КЛИЕНТ
# ============================================================

import os
from supabase import create_client

def get_supabase_client():
    url = os.getenv('SUPABASE_URL')
    key = os.getenv('SUPABASE_KEY')
    if url and key:
        return create_client(url, key)
    return None

supabase = get_supabase_client()

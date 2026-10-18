import sqlite3
import hashlib
import os
from datetime import datetime

DB_PATH = 'chat.db'

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def init_db():
    """Создаёт таблицы и добавляет администратора, если их нет."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Таблица пользователей
    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            full_name TEXT,
            position TEXT,
            phone TEXT,
            photo_path TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_seen TIMESTAMP,
            is_online BOOLEAN DEFAULT 0,
            is_admin BOOLEAN DEFAULT 0,
            upload_limit REAL DEFAULT 10.0,  -- в МБ
            display_name TEXT,               -- отображаемый ник
            nickname_color TEXT DEFAULT '#000000',
            theme TEXT DEFAULT 'light'
        )
    ''')
    
    # Таблица сообщений
    c.execute('''
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            message TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Таблица категорий форума
    c.execute('''
        CREATE TABLE IF NOT EXISTS forum_categories (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            created_by INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # Таблица страниц форума (внутри категорий)
    c.execute('''
        CREATE TABLE IF NOT EXISTS forum_pages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            created_by INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (category_id) REFERENCES forum_categories (id),
            FOREIGN KEY (created_by) REFERENCES users (id)
        )
    ''')
    
    # Таблица постов на страницах форума
    c.execute('''
        CREATE TABLE IF NOT EXISTS forum_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            content TEXT NOT NULL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (page_id) REFERENCES forum_pages (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')
    
    # Таблица прикреплённых файлов к страницам форума
    c.execute('''
        CREATE TABLE IF NOT EXISTS forum_attachments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            filepath TEXT NOT NULL,
            filesize INTEGER NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (page_id) REFERENCES forum_pages (id),
            FOREIGN KEY (user_id) REFERENCES users (id)
        )
    ''')

    # Создаём администратора, если его нет
    admin = c.execute("SELECT * FROM users WHERE username='admin'").fetchone()
    if not admin:
        c.execute('''
            INSERT INTO users (username, password_hash, is_admin, display_name)
            VALUES (?, ?, ?, ?)
        ''', ('admin', hash_password('admin123'), 1, 'admin'))
        print("Администратор создан: admin / admin123")
    
    # ========================================================
    # ВСТАВИТЬ ВОТ СЮДА:
    # Безопасное добавление новых колонок (если их еще нет)
    try:
        c.execute("ALTER TABLE users ADD COLUMN sound_enabled INTEGER DEFAULT 1")
        c.execute("ALTER TABLE users ADD COLUMN sound_path TEXT DEFAULT ''")
    except sqlite3.OperationalError:
        pass # Колонки уже существуют
    # ========================================================
    
    conn.commit()
    conn.close()

# --- Работа с пользователями ---

def register_user(username, password, full_name='', position='', phone=''):
    """Регистрирует нового пользователя. Возвращает (success, message, user_id)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    try:
        c.execute('''
            INSERT INTO users (username, password_hash, full_name, position, phone, display_name)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (username, hash_password(password), full_name, position, phone, username))
        user_id = c.lastrowid
        conn.commit()
        return True, "Регистрация успешна", user_id
    except sqlite3.IntegrityError:
        return False, "Пользователь с таким логином уже существует", None
    finally:
        conn.close()

def authenticate(username, password):
    """Проверяет логин и пароль. Возвращает (user_id, is_admin) или (None, None)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, password_hash, is_admin FROM users WHERE username=?', (username,))
    row = c.fetchone()
    conn.close()
    if row and row[1] == hash_password(password):
        # обновим last_seen и онлайн
        update_last_seen(row[0])
        set_online_status(row[0], True)
        return row[0], bool(row[2])
    return None, None

def get_user(user_id):
    """Возвращает словарь с данными пользователя по id."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT id, username, full_name, position, phone, photo_path, registered_at,
               last_seen, is_online, is_admin, upload_limit, display_name, nickname_color, theme,
               sound_enabled, sound_path
        FROM users WHERE id=?
    ''', (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        columns = ['id', 'username', 'full_name', 'position', 'phone', 'photo_path',
                   'registered_at', 'last_seen', 'is_online', 'is_admin',
                   'upload_limit', 'display_name', 'nickname_color', 'theme',
                   'sound_enabled', 'sound_path']
        return dict(zip(columns, row))
    return None

def get_user_by_username(username):
    """Возвращает id пользователя по имени."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id FROM users WHERE username=?', (username,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else None

def update_user_profile(user_id, full_name, position, phone, photo_path=None):
    """Обновляет профиль пользователя."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    if photo_path is not None:
        c.execute('''
            UPDATE users SET full_name=?, position=?, phone=?, photo_path=?
            WHERE id=?
        ''', (full_name, position, phone, photo_path, user_id))
    else:
        c.execute('''
            UPDATE users SET full_name=?, position=?, phone=?
            WHERE id=?
        ''', (full_name, position, phone, user_id))
    conn.commit()
    conn.close()

def change_password(user_id, old_password, new_password):
    """Меняет пароль, если старый совпадает."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT password_hash FROM users WHERE id=?', (user_id,))
    row = c.fetchone()
    if row and row[0] == hash_password(old_password):
        c.execute('UPDATE users SET password_hash=? WHERE id=?', (hash_password(new_password), user_id))
        conn.commit()
        conn.close()
        return True
    conn.close()
    return False

def set_online_status(user_id, status):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET is_online=? WHERE id=?', (1 if status else 0, user_id))
    conn.commit()
    conn.close()

def update_last_seen(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET last_seen=CURRENT_TIMESTAMP WHERE id=?', (user_id,))
    conn.commit()
    conn.close()

def get_all_users():
    """Возвращает список всех пользователей (id, username, display_name, is_online, is_admin)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT id, username, display_name, is_online, is_admin, nickname_color
        FROM users ORDER BY username
    ''')
    rows = c.fetchall()
    conn.close()
    return rows

def update_display_name(user_id, new_name):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET display_name=? WHERE id=?', (new_name, user_id))
    conn.commit()
    conn.close()

def update_nickname_color(user_id, color):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET nickname_color=? WHERE id=?', (color, user_id))
    conn.commit()
    conn.close()

def update_theme(user_id, theme):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET theme=? WHERE id=?', (theme, user_id))
    conn.commit()
    conn.close()

def get_user_settings(user_id):
    """Возвращает display_name, nickname_color, theme."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT display_name, nickname_color, theme FROM users WHERE id=?', (user_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {'display_name': row[0], 'nickname_color': row[1], 'theme': row[2]}
    return {}

# --- Работа с сообщениями ---
def add_message(user_id, message):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO messages (user_id, message) VALUES (?, ?)', (user_id, message))
    conn.commit()
    conn.close()
    
    # Автоочистка: оставляем только 1000 последних сообщений
    cleanup_old_messages(1000) 

def get_messages(limit=100):
    """Возвращает последние сообщения с данными пользователя."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT m.id, m.user_id, u.username, u.display_name, u.nickname_color, m.message, m.timestamp
        FROM messages m
        JOIN users u ON m.user_id = u.id
        ORDER BY m.timestamp DESC LIMIT ?
    ''', (limit,))
    rows = c.fetchall()
    conn.close()
    # Возвращаем в обратном порядке (от старых к новым)
    return rows[::-1]

# --- Работа с форумом ---

def create_category(name, user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO forum_categories (name, created_by) VALUES (?, ?)', (name, user_id))
    cat_id = c.lastrowid
    conn.commit()
    conn.close()
    return cat_id

def get_categories():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, name, created_by FROM forum_categories ORDER BY name')
    rows = c.fetchall()
    conn.close()
    return rows

def delete_category(cat_id, user_id):
    """Удаляет категорию, если пользователь админ или создатель."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Проверим права
    c.execute('SELECT created_by FROM forum_categories WHERE id=?', (cat_id,))
    row = c.fetchone()
    if row:
        # Админ может удалить любую, создатель - свою
        c.execute('SELECT is_admin FROM users WHERE id=?', (user_id,))
        is_admin = c.fetchone()[0]
        if is_admin or row[0] == user_id:
            # Удаляем страницы, посты, вложения
            c.execute('DELETE FROM forum_posts WHERE page_id IN (SELECT id FROM forum_pages WHERE category_id=?)', (cat_id,))
            c.execute('DELETE FROM forum_attachments WHERE page_id IN (SELECT id FROM forum_pages WHERE category_id=?)', (cat_id,))
            c.execute('DELETE FROM forum_pages WHERE category_id=?', (cat_id,))
            c.execute('DELETE FROM forum_categories WHERE id=?', (cat_id,))
            conn.commit()
            conn.close()
            return True
    conn.close()
    return False

def create_page(category_id, title, user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO forum_pages (category_id, title, created_by) VALUES (?, ?, ?)',
              (category_id, title, user_id))
    page_id = c.lastrowid
    conn.commit()
    conn.close()
    return page_id

def get_pages_by_category(category_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, title, created_by, created_at, last_updated FROM forum_pages WHERE category_id=? ORDER BY created_at', (category_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_page(page_id, user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT created_by FROM forum_pages WHERE id=?', (page_id,))
    row = c.fetchone()
    if row:
        c.execute('SELECT is_admin FROM users WHERE id=?', (user_id,))
        is_admin = c.fetchone()[0]
        if is_admin or row[0] == user_id:
            c.execute('DELETE FROM forum_posts WHERE page_id=?', (page_id,))
            c.execute('DELETE FROM forum_attachments WHERE page_id=?', (page_id,))
            c.execute('DELETE FROM forum_pages WHERE id=?', (page_id,))
            conn.commit()
            conn.close()
            return True
    conn.close()
    return False

def add_post(page_id, user_id, content):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('INSERT INTO forum_posts (page_id, user_id, content) VALUES (?, ?, ?)', (page_id, user_id, content))
    # обновим last_updated
    c.execute('UPDATE forum_pages SET last_updated=CURRENT_TIMESTAMP WHERE id=?', (page_id,))
    conn.commit()
    conn.close()

def get_posts(page_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT p.id, p.user_id, u.username, u.display_name, u.nickname_color, p.content, p.timestamp
        FROM forum_posts p
        JOIN users u ON p.user_id = u.id
        WHERE p.page_id=?
        ORDER BY p.timestamp
    ''', (page_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def add_attachment(page_id, user_id, filename, filepath, filesize):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO forum_attachments (page_id, user_id, filename, filepath, filesize)
        VALUES (?, ?, ?, ?, ?)
    ''', (page_id, user_id, filename, filepath, filesize))
    conn.commit()
    conn.close()

def get_attachments(page_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT id, user_id, filename, filepath, filesize, uploaded_at FROM forum_attachments WHERE page_id=?', (page_id,))
    rows = c.fetchall()
    conn.close()
    return rows

def delete_attachment(att_id, user_id):
    """Удаляет файл, если пользователь админ или загрузил его."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT user_id, filepath FROM forum_attachments WHERE id=?', (att_id,))
    row = c.fetchone()
    if row:
        c.execute('SELECT is_admin FROM users WHERE id=?', (user_id,))
        is_admin = c.fetchone()[0]
        if is_admin or row[0] == user_id:
            # Удаляем физический файл
            if os.path.exists(row[1]):
                os.remove(row[1])
            c.execute('DELETE FROM forum_attachments WHERE id=?', (att_id,))
            conn.commit()
            conn.close()
            return True
    conn.close()
    return False

# Статистика
def get_all_attachments_with_user():
    """Возвращает все вложения с именами пользователей и категориями для статистики."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT a.id, a.user_id, u.username, u.display_name, a.filename, a.filesize, a.uploaded_at,
               a.page_id, p.title, c.name as category_name, a.filepath
        FROM forum_attachments a
        JOIN users u ON a.user_id = u.id
        JOIN forum_pages p ON a.page_id = p.id
        JOIN forum_categories c ON p.category_id = c.id
        ORDER BY a.uploaded_at DESC
    ''')
    rows = c.fetchall()
    conn.close()
    return rows

def get_user_upload_total(user_id):
    """Суммарный размер загруженных файлов пользователя в байтах."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT SUM(filesize) FROM forum_attachments WHERE user_id=?', (user_id,))
    total = c.fetchone()[0]
    conn.close()
    return total or 0

def get_user_attachment_count(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM forum_attachments WHERE user_id=?', (user_id,))
    count = c.fetchone()[0]
    conn.close()
    return count

def get_user_upload_limit(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT upload_limit FROM users WHERE id=?', (user_id,))
    limit = c.fetchone()[0]
    conn.close()
    return limit

def set_user_upload_limit(user_id, limit_mb):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET upload_limit=? WHERE id=?', (limit_mb, user_id))
    conn.commit()
    conn.close()

# --- Вспомогательные ---
def is_admin(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT is_admin FROM users WHERE id=?', (user_id,))
    row = c.fetchone()
    conn.close()
    return row and row[0] == 1

def get_user_upload_count(user_id):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM forum_attachments WHERE user_id=?', (user_id,))
    count = c.fetchone()[0]
    conn.close()
    return count

def update_page_title(page_id, new_title):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE forum_pages SET title=?, last_updated=CURRENT_TIMESTAMP WHERE id=?', (new_title, page_id))
    conn.commit()
    conn.close()
    
def update_category_name(cat_id, new_name):
    """Обновляет название категории."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE forum_categories SET name=? WHERE id=?', (new_name, cat_id))
    conn.commit()
    conn.close()
    
def admin_change_password(user_id, new_password):
    """Меняет пароль пользователя без проверки старого (только для администратора)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET password_hash=? WHERE id=?', (hash_password(new_password), user_id))
    conn.commit()
    conn.close()
    
def clear_page_posts(page_id):
    """Удаляет все посты на указанной странице."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM forum_posts WHERE page_id=?', (page_id,))
    conn.commit()
    conn.close()
    
def delete_user(target_user_id):
    """Полностью удаляет пользователя и все связанные с ним данные."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1. Удаляем физические файлы вложений форума, загруженные этим пользователем
    c.execute('SELECT filepath FROM forum_attachments WHERE user_id=?', (target_user_id,))
    for row in c.fetchall():
        if os.path.exists(row[0]):
            try: os.remove(row[0])
            except: pass

    # 2. Удаляем аватарку
    c.execute('SELECT photo_path FROM users WHERE id=?', (target_user_id,))
    row = c.fetchone()
    if row and row[0] and os.path.exists(row[0]):
        try: os.remove(row[0])
        except: pass

    # 3. Удаляем записи из БД
    c.execute('DELETE FROM forum_attachments WHERE user_id=?', (target_user_id,))
    c.execute('DELETE FROM forum_posts WHERE user_id=?', (target_user_id,))
    c.execute('DELETE FROM messages WHERE user_id=?', (target_user_id,))

    # 4. Удаляем категории, созданные пользователем (вместе со всеми страницами и файлами внутри них)
    c.execute('SELECT id FROM forum_categories WHERE created_by=?', (target_user_id,))
    categories = c.fetchall()
    for cat in categories:
        cat_id = cat[0]
        c.execute('SELECT id FROM forum_pages WHERE category_id=?', (cat_id,))
        pages = c.fetchall()
        for p in pages:
            pid = p[0]
            # Удаляем файлы страниц
            c.execute('SELECT filepath FROM forum_attachments WHERE page_id=?', (pid,))
            for att in c.fetchall():
                if os.path.exists(att[0]):
                    try: os.remove(att[0])
                    except: pass
            c.execute('DELETE FROM forum_attachments WHERE page_id=?', (pid,))
            c.execute('DELETE FROM forum_posts WHERE page_id=?', (pid,))
            c.execute('DELETE FROM forum_pages WHERE id=?', (pid,))
        c.execute('DELETE FROM forum_categories WHERE id=?', (cat_id,))

    # 5. Удаляем оставшиеся страницы, созданные пользователем (в чужих категориях)
    c.execute('SELECT id FROM forum_pages WHERE created_by=?', (target_user_id,))
    pages = c.fetchall()
    for p in pages:
        pid = p[0]
        c.execute('SELECT filepath FROM forum_attachments WHERE page_id=?', (pid,))
        for att in c.fetchall():
            if os.path.exists(att[0]):
                try: os.remove(att[0])
                except: pass
        c.execute('DELETE FROM forum_attachments WHERE page_id=?', (pid,))
        c.execute('DELETE FROM forum_posts WHERE page_id=?', (pid,))
        c.execute('DELETE FROM forum_pages WHERE id=?', (pid,))

    # 6. Удаляем самого пользователя
    c.execute('DELETE FROM users WHERE id=?', (target_user_id,))

    conn.commit()
    conn.close()
    return True

def set_admin_status(user_id, status):
    """Выдает или забирает права администратора."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET is_admin=? WHERE id=?', (1 if status else 0, user_id))
    conn.commit()
    conn.close()

def get_all_users_detailed():
    """Возвращает расширенную информацию о всех пользователях для админ-панели."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        SELECT id, username, display_name, is_online, is_admin, registered_at
        FROM users ORDER BY id
    ''')
    rows = c.fetchall()
    conn.close()
    return rows

def clear_all_messages():
    """Полностью очищает историю сообщений (для админа)."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('DELETE FROM messages')
    conn.commit()
    conn.close()

def cleanup_old_messages(limit=1000):
    """Оставляет в базе только последние `limit` сообщений."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # Удаляем все сообщения, ID которых меньше, чем ID (limit)-го сообщения с конца
    c.execute('''
        DELETE FROM messages 
        WHERE id NOT IN (
            SELECT id FROM messages ORDER BY id DESC LIMIT ?
        )
    ''', (limit,))
    conn.commit()
    conn.close()
    
def update_sound_settings(user_id, enabled, sound_path):
    """Обновляет настройки звуковых уведомлений."""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('UPDATE users SET sound_enabled=?, sound_path=? WHERE id=?', (1 if enabled else 0, sound_path, user_id))
    conn.commit()
    conn.close()
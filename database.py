import sqlite3
from config import DB_PATH

# DATABASE HELPERS
def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        username TEXT UNIQUE,
        display_name TEXT,
        password_hash TEXT,
        bio TEXT,
        profile_pic_path TEXT,
        created_at REAL,
        wallet_address TEXT,
        private_key TEXT,
        mnemonic TEXT
    )
    """)
    c.execute("""CREATE TABLE IF NOT EXISTS posts (id INTEGER PRIMARY KEY, user_id INTEGER, text TEXT, image_path TEXT, created_at REAL, orig_post_id INTEGER DEFAULT NULL, FOREIGN KEY(user_id) REFERENCES users(id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS follows (follower_id INTEGER, followed_id INTEGER, created_at REAL, PRIMARY KEY (follower_id, followed_id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS likes (user_id INTEGER, post_id INTEGER, created_at REAL, PRIMARY KEY (user_id, post_id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS bookmarks (user_id INTEGER, post_id INTEGER, created_at REAL, PRIMARY KEY (user_id, post_id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS replies (id INTEGER PRIMARY KEY, post_id INTEGER, user_id INTEGER, text TEXT, created_at REAL, FOREIGN KEY(post_id) REFERENCES posts(id), FOREIGN KEY(user_id) REFERENCES users(id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, sender_id INTEGER, receiver_id INTEGER, text TEXT, created_at REAL, FOREIGN KEY(sender_id) REFERENCES users(id), FOREIGN KEY(receiver_id) REFERENCES users(id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS notifications (id INTEGER PRIMARY KEY, user_id INTEGER, text TEXT, seen INTEGER DEFAULT 0, created_at REAL, FOREIGN KEY(user_id) REFERENCES users(id))""")
    conn.commit()
    return conn

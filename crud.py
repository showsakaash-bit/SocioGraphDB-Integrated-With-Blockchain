import sqlite3
from typing import List, Optional
from database import get_conn
from utils import hash_password, now_ts
from blockchain import generate_new_wallet

# DATA API

def create_user(username: str, display_name: str, password: str, bio: str = "", profile_pic_path: Optional[str] = None) -> Optional[int]:
    conn = get_conn()
    c = conn.cursor()
    wallet_addr, priv_key, mnemonic = generate_new_wallet()
    try:
        c.execute(
            """INSERT INTO users (username, display_name, password_hash, bio, profile_pic_path, created_at, wallet_address, private_key, mnemonic) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (username, display_name, hash_password(password), bio, profile_pic_path, now_ts(), wallet_addr, priv_key, mnemonic),
        )
        conn.commit()
        return c.lastrowid
    except sqlite3.IntegrityError:
        return None

def update_user_details(user_id: int, display_name: str, bio: str, new_pic_path: Optional[str] = None):
    conn = get_conn()
    c = conn.cursor()
    if new_pic_path:
        c.execute("UPDATE users SET display_name = ?, bio = ?, profile_pic_path = ? WHERE id = ?", (display_name, bio, new_pic_path, user_id))
    else:
        c.execute("UPDATE users SET display_name = ?, bio = ? WHERE id = ?", (display_name, bio, user_id))
    conn.commit()
    return get_user_by_id(user_id)

def authenticate(username: str, password: str) -> Optional[dict]:
    c = get_conn().cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    if not row: return None
    if row["password_hash"] == hash_password(password): return dict(row)
    return None

def get_user_by_id(user_id: int) -> Optional[dict]:
    c = get_conn().cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    row = c.fetchone()
    return dict(row) if row else None

def get_user_by_username(username: str) -> Optional[dict]:
    c = get_conn().cursor()
    c.execute("SELECT * FROM users WHERE username = ?", (username,))
    row = c.fetchone()
    return dict(row) if row else None

def create_post(user_id: int, text: str, image_path: Optional[str] = None, orig_post_id: Optional[int] = None) -> int:
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO posts (user_id, text, image_path, created_at, orig_post_id) VALUES (?, ?, ?, ?, ?)", (user_id, text, image_path, now_ts(), orig_post_id))
    post_id = c.lastrowid
    conn.commit()
    return post_id

def follow_user(follower_id: int, followed_id: int) -> bool:
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO follows (follower_id, followed_id, created_at) VALUES (?, ?, ?)", (follower_id, followed_id, now_ts()))
        conn.commit()
        create_notification(followed_id, f"@{get_user_by_id(follower_id)['username']} followed you")
        return True
    except sqlite3.IntegrityError:
        return False

def unfollow_user(follower_id: int, followed_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM follows WHERE follower_id = ? AND followed_id = ?", (follower_id, followed_id))
    conn.commit()

def is_following(follower_id: int, followed_id: int) -> bool:
    c = get_conn().cursor()
    c.execute("SELECT 1 FROM follows WHERE follower_id = ? AND followed_id = ?", (follower_id, followed_id))
    return c.fetchone() is not None

def like_post(user_id: int, post_id: int) -> bool:
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO likes (user_id, post_id, created_at) VALUES (?, ?, ?)", (user_id, post_id, now_ts()))
        conn.commit()
        post = get_post(post_id)
        if post: create_notification(post['user_id'], f"@{get_user_by_id(user_id)['username']} liked your post")
        return True
    except sqlite3.IntegrityError:
        return False

def unlike_post(user_id: int, post_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM likes WHERE user_id = ? AND post_id = ?", (user_id, post_id))
    conn.commit()

def bookmark_post(user_id: int, post_id: int) -> bool:
    conn = get_conn()
    c = conn.cursor()
    try:
        c.execute("INSERT INTO bookmarks (user_id, post_id, created_at) VALUES (?, ?, ?)", (user_id, post_id, now_ts()))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False

def unbookmark_post(user_id: int, post_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("DELETE FROM bookmarks WHERE user_id = ? AND post_id = ?", (user_id, post_id))
    conn.commit()

def reply_to_post(user_id: int, post_id: int, text: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO replies (post_id, user_id, text, created_at) VALUES (?, ?, ?, ?)", (post_id, user_id, text, now_ts()))
    conn.commit()
    post = get_post(post_id)
    if post: create_notification(post['user_id'], f"@{get_user_by_id(user_id)['username']} replied to your post")

def send_message(sender_id: int, receiver_id: int, text: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO messages (sender_id, receiver_id, text, created_at) VALUES (?, ?, ?, ?)", (sender_id, receiver_id, text, now_ts()))
    conn.commit()
    create_notification(receiver_id, f"New message from @{get_user_by_id(sender_id)['username']}")

def get_post(post_id: int) -> Optional[sqlite3.Row]:
    c = get_conn().cursor()
    c.execute("SELECT p.*, u.username, u.display_name, u.profile_pic_path FROM posts p JOIN users u ON p.user_id = u.id WHERE p.id = ?", (post_id,))
    return c.fetchone()

def get_posts_for_user(user_id: int, limit=50) -> List[sqlite3.Row]:
    c = get_conn().cursor()
    c.execute("SELECT p.*, u.username, u.display_name, u.profile_pic_path FROM posts p JOIN users u ON p.user_id = u.id WHERE p.user_id = ? ORDER BY p.created_at DESC LIMIT ?", (user_id, limit))
    return c.fetchall()

def get_liked_posts_for_user(user_id: int) -> List[sqlite3.Row]:
    c = get_conn().cursor()
    c.execute("SELECT p.*, u.username, u.display_name, u.profile_pic_path FROM posts p JOIN users u ON p.user_id = u.id JOIN likes l ON l.post_id = p.id WHERE l.user_id = ? ORDER BY l.created_at DESC", (user_id,))
    return c.fetchall()

def get_replies_for_user(user_id: int) -> List[sqlite3.Row]:
    c = get_conn().cursor()
    c.execute("SELECT r.id as reply_id, r.text as reply_text, r.created_at as reply_created_at, p.id as orig_post_id, p.text as orig_text, p.image_path as orig_image, p.created_at as orig_created, u.username as orig_username, u.display_name as orig_display, u.profile_pic_path as orig_pic FROM replies r JOIN posts p ON r.post_id = p.id JOIN users u ON p.user_id = u.id WHERE r.user_id = ? ORDER BY r.created_at DESC", (user_id,))
    return c.fetchall()

def get_feed(user_id: int, limit=50) -> List[sqlite3.Row]:
    c = get_conn().cursor()
    c.execute("SELECT p.*, u.username, u.display_name, u.profile_pic_path FROM posts p JOIN users u ON p.user_id = u.id WHERE p.user_id IN (SELECT followed_id FROM follows WHERE follower_id = ?) OR p.user_id = ? ORDER BY p.created_at DESC LIMIT ?", (user_id, user_id, limit))
    return c.fetchall()

def get_likes_for_post(post_id: int) -> int:
    c = get_conn().cursor()
    c.execute("SELECT COUNT(*) as cnt FROM likes WHERE post_id = ?", (post_id,))
    return c.fetchone()["cnt"]

def get_following_count(user_id: int) -> int:
    c = get_conn().cursor()
    c.execute("SELECT COUNT(followed_id) as cnt FROM follows WHERE follower_id = ?", (user_id,))
    return c.fetchone()["cnt"]

def get_follower_count(user_id: int) -> int:
    c = get_conn().cursor()
    c.execute("SELECT COUNT(follower_id) as cnt FROM follows WHERE followed_id = ?", (user_id,))
    return c.fetchone()["cnt"]
    
def get_following_list(user_id: int) -> List[sqlite3.Row]:
    c = get_conn().cursor()
    c.execute("SELECT u.id, u.username, u.display_name, u.bio, u.profile_pic_path FROM users u JOIN follows f ON u.id = f.followed_id WHERE f.follower_id = ?", (user_id,))
    return c.fetchall()

def get_followers_list(user_id: int) -> List[sqlite3.Row]:
    c = get_conn().cursor()
    c.execute("SELECT u.id, u.username, u.display_name, u.bio, u.profile_pic_path FROM users u JOIN follows f ON u.id = f.follower_id WHERE f.followed_id = ?", (user_id,))
    return c.fetchall()

def get_replies_for_post(post_id: int) -> List[sqlite3.Row]:
    c = get_conn().cursor()
    c.execute("SELECT r.*, u.username, u.display_name FROM replies r JOIN users u ON r.user_id = u.id WHERE r.post_id = ? ORDER BY r.created_at", (post_id,))
    return c.fetchall()

def get_bookmarks_for_user(user_id: int) -> List[sqlite3.Row]:
    c = get_conn().cursor()
    c.execute("SELECT p.*, u.username, u.display_name, u.profile_pic_path FROM bookmarks b JOIN posts p ON b.post_id = p.id JOIN users u ON p.user_id = u.id WHERE b.user_id = ? ORDER BY b.created_at DESC", (user_id,))
    return c.fetchall()

def get_messages_between(a: int, b: int) -> List[sqlite3.Row]:
    c = get_conn().cursor()
    c.execute("SELECT m.*, su.username as sender_name, ru.username as receiver_name FROM messages m JOIN users su ON m.sender_id = su.id JOIN users ru ON m.receiver_id = ru.id WHERE (sender_id = ? AND receiver_id = ?) OR (sender_id = ? AND receiver_id = ?) ORDER BY m.created_at", (a, b, b, a))
    return c.fetchall()

def search_users(term: str) -> List[sqlite3.Row]:
    c = get_conn().cursor()
    q = f"%{term}%"
    c.execute("SELECT * FROM users WHERE username LIKE ? OR display_name LIKE ? LIMIT 50", (q, q))
    return c.fetchall()

def search_posts(term: str) -> List[sqlite3.Row]:
    c = get_conn().cursor()
    q = f"%{term}%"
    c.execute("SELECT p.*, u.username, u.display_name, u.profile_pic_path FROM posts p JOIN users u ON p.user_id = u.id WHERE p.text LIKE ? ORDER BY p.created_at DESC LIMIT 100", (q,))
    return c.fetchall()

def create_notification(user_id: int, text: str):
    conn = get_conn()
    c = conn.cursor()
    c.execute("INSERT INTO notifications (user_id, text, seen, created_at) VALUES (?, ?, 0, ?)", (user_id, text, now_ts()))
    conn.commit()

def get_notifications(user_id: int) -> List[sqlite3.Row]:
    c = get_conn().cursor()
    c.execute("SELECT * FROM notifications WHERE user_id = ? ORDER BY created_at DESC LIMIT 200", (user_id,))
    return c.fetchall()

def mark_notifications_seen(user_id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("UPDATE notifications SET seen = 1 WHERE user_id = ?", (user_id,))
    conn.commit()

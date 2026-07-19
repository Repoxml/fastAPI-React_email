import sqlite3
from fastapi import HTTPException
from typing import Optional

DB_PATH = "users.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            hashed_password TEXT NOT NULL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            sender TEXT NOT NULL,
            title TEXT NOT NULL,
            context TEXT NOT NULL,
            date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS message_recipients (
            message_id INTEGER NOT NULL,
            recipient TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def get_user(username: str) -> Optional[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT username, hashed_password FROM users WHERE username = ?",
        (username,)
    ).fetchone()
    conn.close()
    if row:
        return {"username": row["username"], "hashed_password": row["hashed_password"]}
    return None

def create_user(username: str, hashed_password: str):
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.execute(
            "INSERT INTO users (username, hashed_password) VALUES (?, ?)",
            (username, hashed_password)
        )
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=409, detail="Username already taken")
    finally:
        conn.close()

        
def get_all_users():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        "SELECT username FROM users"
    ).fetchall()
    conn.close()
    return [row["username"] for row in rows]


def create_message(sender: str, title: str, context: str, recipients: list):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO messages (sender, title, context) VALUES (?, ?, ?)",
        (sender, title, context)
    )
    message_id = cursor.lastrowid
    for recipient in recipients:
        cursor.execute(
            "INSERT INTO message_recipients (message_id, recipient) VALUES (?, ?)",
            (message_id, recipient)
        )
    conn.commit()
    conn.close()
    return message_id

def get_messages_for_user(username: str) -> list[dict]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    
    messages = conn.execute("""
        SELECT id, sender, title, context, date FROM messages
        WHERE sender = ?
           OR id IN (SELECT message_id FROM message_recipients WHERE recipient = ?)
        ORDER BY date DESC
    """, (username, username)).fetchall()
    
    result = []
    for msg in messages:
        recipients_rows = conn.execute(
            "SELECT recipient FROM message_recipients WHERE message_id = ?",
            (msg["id"],)
        ).fetchall()
        
        result.append({
            "id": msg["id"],
            "sender": msg["sender"],
            "title": msg["title"],
            "context": msg["context"],
            "date": msg["date"],
            "recipients": [r["recipient"] for r in recipients_rows],
        })
    
    conn.close()
    return result
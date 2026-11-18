"""Password verification and expiring account sessions stored in SQLite."""

import hashlib
import hmac
import secrets
import sqlite3
import time
from contextlib import closing

from backend.db.order_db import get_connection, init_db

SESSION_SECONDS = 24 * 60 * 60


def password_hash(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 600_000)


def register(username: str, password: str) -> bool:
    init_db()
    salt = secrets.token_bytes(16)
    digest = password_hash(password, salt)
    with closing(get_connection()) as conn, conn:
        try:
            conn.execute(
                "INSERT INTO users (username, salt, password_hash) VALUES (?, ?, ?)",
                (username, salt, digest),
            )
        except sqlite3.IntegrityError:
            return False
    return True


def sign_in(username: str, password: str) -> str | None:
    init_db()
    with closing(get_connection()) as conn:
        user = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
        digest = password_hash(password, user["salt"] if user else bytes(16))
        if user is None or not hmac.compare_digest(digest, user["password_hash"]):
            return None
        token = secrets.token_urlsafe(32)
        now = int(time.time())
        with conn:
            conn.execute("DELETE FROM sessions WHERE expires_at <= ?", (now,))
            conn.execute(
                "INSERT INTO sessions VALUES (?, ?, ?)",
                (token_hash(token), user["id"], now + SESSION_SECONDS),
            )
        return token


def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def session_user(token: str) -> int | None:
    init_db()
    with closing(get_connection()) as conn:
        row = conn.execute(
            "SELECT user_id FROM sessions WHERE token_hash = ? AND expires_at > ?",
            (token_hash(token), int(time.time())),
        ).fetchone()
    return row["user_id"] if row else None


def sign_out(token: str) -> None:
    init_db()
    with closing(get_connection()) as conn, conn:
        conn.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash(token),))

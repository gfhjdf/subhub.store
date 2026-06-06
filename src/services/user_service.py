"""User service — registration, lookup, and language management."""
import uuid
from src.database.connection import get_db


async def register_or_update_user(telegram_id: int, username: str | None,
                                   first_name: str | None, last_name: str | None) -> dict:
    """Register a new user or update existing user info. Returns user dict."""
    db = await get_db()
    existing = await db.execute_fetchall(
        "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
    )
    if existing:
        user = dict(existing[0])
        await db.execute(
            """UPDATE users SET telegram_username = ?, first_name = ?, last_name = ?,
               updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?""",
            (username, first_name, last_name, telegram_id)
        )
        await db.commit()
        user["telegram_username"] = username
        user["first_name"] = first_name
        user["last_name"] = last_name
        return user
    else:
        referral_code = uuid.uuid4().hex[:8]
        await db.execute(
            """INSERT INTO users (telegram_id, telegram_username, first_name, last_name, referral_code)
               VALUES (?, ?, ?, ?, ?)""",
            (telegram_id, username, first_name, last_name, referral_code)
        )
        await db.commit()
        rows = await db.execute_fetchall(
            "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
        )
        return dict(rows[0])


async def get_user_by_telegram_id(telegram_id: int) -> dict | None:
    """Get user by Telegram ID."""
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
    )
    return dict(rows[0]) if rows else None


async def get_user_by_id(user_id: int) -> dict | None:
    """Get user by internal ID."""
    db = await get_db()
    rows = await db.execute_fetchall("SELECT * FROM users WHERE id = ?", (user_id,))
    return dict(rows[0]) if rows else None


async def get_user_by_referral_code(code: str) -> dict | None:
    """Get user by referral code."""
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT * FROM users WHERE referral_code = ?", (code,)
    )
    return dict(rows[0]) if rows else None


async def update_language(telegram_id: int, language_code: str) -> None:
    """Update user's language preference."""
    db = await get_db()
    await db.execute(
        "UPDATE users SET language_code = ?, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?",
        (language_code, telegram_id)
    )
    await db.commit()


async def get_all_users(limit: int = 100, offset: int = 0, search: str | None = None) -> list[dict]:
    """Get paginated user list for admin."""
    db = await get_db()
    if search:
        rows = await db.execute_fetchall(
            """SELECT * FROM users WHERE telegram_username LIKE ? OR first_name LIKE ?
               OR CAST(telegram_id AS TEXT) LIKE ?
               ORDER BY created_at DESC LIMIT ? OFFSET ?""",
            (f"%{search}%", f"%{search}%", f"%{search}%", limit, offset)
        )
    else:
        rows = await db.execute_fetchall(
            "SELECT * FROM users ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset)
        )
    return [dict(r) for r in rows]


async def get_users_count(search: str | None = None) -> int:
    """Get total user count."""
    db = await get_db()
    if search:
        rows = await db.execute_fetchall(
            """SELECT COUNT(*) as cnt FROM users WHERE telegram_username LIKE ?
               OR first_name LIKE ? OR CAST(telegram_id AS TEXT) LIKE ?""",
            (f"%{search}%", f"%{search}%", f"%{search}%")
        )
    else:
        rows = await db.execute_fetchall("SELECT COUNT(*) as cnt FROM users")
    return rows[0]["cnt"]

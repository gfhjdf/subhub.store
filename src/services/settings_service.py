"""Settings service — manage editable system texts and configuration."""
import json
from src.database.connection import get_db


async def get_setting(key: str) -> str:
    """Get a setting value by key."""
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT value_json FROM settings WHERE key = ?", (key,)
    )
    if rows:
        return json.loads(rows[0]["value_json"])
    return ""


async def set_setting(key: str, value: str) -> None:
    """Set a setting value. Creates if not exists, updates if exists."""
    db = await get_db()
    existing = await db.execute_fetchall(
        "SELECT key FROM settings WHERE key = ?", (key,)
    )
    if existing:
        await db.execute(
            "UPDATE settings SET value_json = ?, updated_at = CURRENT_TIMESTAMP WHERE key = ?",
            (json.dumps(value), key)
        )
    else:
        await db.execute(
            "INSERT INTO settings (key, value_json) VALUES (?, ?)",
            (key, json.dumps(value))
        )
    await db.commit()


async def get_text(key: str, language: str) -> str:
    """Get a text setting by key and language suffix.
    e.g., get_text('payment_instructions', 'uz') looks up 'payment_instructions_uz'
    """
    full_key = f"{key}_{language}"
    return await get_setting(full_key)


async def get_all_settings() -> dict:
    """Get all settings as a dict for admin."""
    db = await get_db()
    rows = await db.execute_fetchall("SELECT key, value_json FROM settings ORDER BY key")
    result = {}
    for row in rows:
        try:
            result[row["key"]] = json.loads(row["value_json"])
        except (json.JSONDecodeError, TypeError):
            result[row["key"]] = row["value_json"]
    return result


async def update_settings(settings_dict: dict) -> None:
    """Update multiple settings at once."""
    for key, value in settings_dict.items():
        await set_setting(key, value)

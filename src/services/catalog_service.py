"""Catalog service — platform and plan CRUD with stock counts."""
import sqlite3
from src.database.connection import get_db


# ── Platforms ──────────────────────────────────────────────

async def get_active_platforms() -> list[dict]:
    """Get all active platforms ordered by sort_order."""
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT * FROM platforms WHERE is_active = 1 ORDER BY sort_order, name"
    )
    return [dict(r) for r in rows]


async def get_all_platforms() -> list[dict]:
    """Get all platforms (admin)."""
    db = await get_db()
    rows = await db.execute_fetchall("SELECT * FROM platforms ORDER BY sort_order, name")
    return [dict(r) for r in rows]


async def get_platform_by_id(platform_id: int) -> dict | None:
    db = await get_db()
    rows = await db.execute_fetchall("SELECT * FROM platforms WHERE id = ?", (platform_id,))
    return dict(rows[0]) if rows else None


async def create_platform(name: str, slug: str, custom_emoji_code: str | None = None, is_active: bool = True, sort_order: int = 0) -> dict:
    db = await get_db()
    await db.execute(
        "INSERT INTO platforms (name, slug, custom_emoji_code, is_active, sort_order) VALUES (?, ?, ?, ?, ?)",
        (name, slug, custom_emoji_code, int(is_active), sort_order)
    )
    await db.commit()
    rows = await db.execute_fetchall("SELECT * FROM platforms WHERE slug = ?", (slug,))
    return dict(rows[0])


async def update_platform(platform_id: int, **kwargs) -> dict | None:
    db = await get_db()
    allowed = {"name", "slug", "custom_emoji_code", "is_active", "sort_order"}
    updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not updates:
        return await get_platform_by_id(platform_id)
    if "is_active" in updates:
        updates["is_active"] = int(updates["is_active"])
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [platform_id]
    await db.execute(
        f"UPDATE platforms SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        values
    )
    await db.commit()
    return await get_platform_by_id(platform_id)


async def delete_platform(platform_id: int) -> bool:
    db = await get_db()
    await db.execute("DELETE FROM platforms WHERE id = ?", (platform_id,))
    await db.commit()
    return True


# ── Plans ─────────────────────────────────────────────────

async def get_plans_for_platform(platform_id: int) -> list[dict]:
    """Get active plans for a platform with stock counts."""
    db = await get_db()
    rows = await db.execute_fetchall(
        """SELECT p.*,
           (SELECT COUNT(*) FROM accounts a WHERE a.plan_id = p.id AND a.status = 'available') as stock
           FROM plans p
           WHERE p.platform_id = ? AND p.is_active = 1
           ORDER BY p.sort_order, p.name""",
        (platform_id,)
    )
    return [dict(r) for r in rows]


async def get_all_plans(platform_id: int | None = None) -> list[dict]:
    """Get all plans (admin), optionally filtered by platform."""
    db = await get_db()
    if platform_id:
        rows = await db.execute_fetchall(
            """SELECT p.*,
               (SELECT COUNT(*) FROM accounts a WHERE a.plan_id = p.id AND a.status = 'available') as stock,
               pl.name as platform_name
               FROM plans p JOIN platforms pl ON p.platform_id = pl.id
               WHERE p.platform_id = ? ORDER BY p.sort_order, p.name""",
            (platform_id,)
        )
    else:
        rows = await db.execute_fetchall(
            """SELECT p.*,
               (SELECT COUNT(*) FROM accounts a WHERE a.plan_id = p.id AND a.status = 'available') as stock,
               pl.name as platform_name
               FROM plans p JOIN platforms pl ON p.platform_id = pl.id
               ORDER BY pl.sort_order, p.sort_order, p.name"""
        )
    return [dict(r) for r in rows]


async def get_plan_by_id(plan_id: int) -> dict | None:
    db = await get_db()
    rows = await db.execute_fetchall(
        """SELECT p.*,
           (SELECT COUNT(*) FROM accounts a WHERE a.plan_id = p.id AND a.status = 'available') as stock,
           pl.name as platform_name,
           pl.custom_emoji_code as platform_emoji_code
           FROM plans p JOIN platforms pl ON p.platform_id = pl.id
           WHERE p.id = ?""",
        (plan_id,)
    )
    return dict(rows[0]) if rows else None


async def get_stock_count(plan_id: int) -> int:
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT COUNT(*) as cnt FROM accounts WHERE plan_id = ? AND status = 'available'",
        (plan_id,)
    )
    return rows[0]["cnt"]


async def create_plan(platform_id: int, name: str, price_uzs: int,
                      description_uz: str = "", description_ru: str = "",
                      faq_uz: str = "", faq_ru: str = "",
                      is_active: bool = True, sort_order: int = 0,
                      plan_type: str = "regular") -> dict:
    db = await get_db()
    cursor = await db.execute(
        """INSERT INTO plans (platform_id, name, price_uzs, description_uz, description_ru,
           faq_uz, faq_ru, is_active, sort_order, plan_type) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (platform_id, name, price_uzs, description_uz, description_ru,
         faq_uz, faq_ru, int(is_active), sort_order, plan_type)
    )
    await db.commit()
    return await get_plan_by_id(cursor.lastrowid)


async def update_plan(plan_id: int, **kwargs) -> dict | None:
    db = await get_db()
    allowed = {"name", "platform_id", "price_uzs", "description_uz", "description_ru",
               "faq_uz", "faq_ru", "is_active", "sort_order", "plan_type"}
    updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not updates:
        return await get_plan_by_id(plan_id)
    if "is_active" in updates:
        updates["is_active"] = int(updates["is_active"])
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [plan_id]
    await db.execute(
        f"UPDATE plans SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        values
    )
    await db.commit()
    return await get_plan_by_id(plan_id)


async def delete_plan(plan_id: int) -> bool:
    db = await get_db()
    try:
        await db.execute("DELETE FROM plans WHERE id = ?", (plan_id,))
        await db.commit()
        return True
    except sqlite3.IntegrityError:
        raise ValueError(
            "Невозможно удалить этот тариф, так как с ним связаны существующие заказы. "
            "Пожалуйста, просто отключите его (сделайте неактивным)."
        )

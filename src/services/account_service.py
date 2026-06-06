"""Account service — credential management, atomic assignment, bulk import."""
from src.database.connection import get_db


async def add_account(plan_id: int, login: str, password: str, notes: str | None = None) -> dict:
    """Add a single credential to inventory."""
    db = await get_db()
    cursor = await db.execute(
        "INSERT INTO accounts (plan_id, login, password, notes) VALUES (?, ?, ?, ?)",
        (plan_id, login, password, notes)
    )
    await db.commit()
    rows = await db.execute_fetchall("SELECT * FROM accounts WHERE id = ?", (cursor.lastrowid,))
    return dict(rows[0])


async def bulk_add_accounts(plan_id: int, accounts_list: list[dict]) -> int:
    """Bulk import credentials. Each item: {login, password, notes?}. Returns count added."""
    db = await get_db()
    count = 0
    for acc in accounts_list:
        await db.execute(
            "INSERT INTO accounts (plan_id, login, password, notes) VALUES (?, ?, ?, ?)",
            (plan_id, acc["login"], acc["password"], acc.get("notes"))
        )
        count += 1
    await db.commit()
    return count


async def get_available_account(plan_id: int) -> dict | None:
    """Get one available account for a plan (does not reserve it)."""
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT * FROM accounts WHERE plan_id = ? AND status = 'available' LIMIT 1",
        (plan_id,)
    )
    return dict(rows[0]) if rows else None


async def reserve_account(plan_id: int, order_id: int) -> dict | None:
    """Atomically reserve one available account for an order."""
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT id FROM accounts WHERE plan_id = ? AND status = 'available' LIMIT 1",
        (plan_id,)
    )
    if not rows:
        return None
    account_id = rows[0]["id"]
    await db.execute(
        """UPDATE accounts SET status = 'reserved', reserved_for_order_id = ?,
           updated_at = CURRENT_TIMESTAMP WHERE id = ? AND status = 'available'""",
        (order_id, account_id)
    )
    await db.commit()
    # Verify it was actually updated (atomic check)
    rows = await db.execute_fetchall(
        "SELECT * FROM accounts WHERE id = ? AND status = 'reserved' AND reserved_for_order_id = ?",
        (account_id, order_id)
    )
    return dict(rows[0]) if rows else None


async def assign_account(account_id: int, order_id: int, user_id: int) -> dict:
    """Mark a reserved account as sold."""
    db = await get_db()
    await db.execute(
        """UPDATE accounts SET status = 'sold', sold_order_id = ?, sold_to_user_id = ?,
           sold_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
        (order_id, user_id, account_id)
    )
    await db.commit()
    rows = await db.execute_fetchall("SELECT * FROM accounts WHERE id = ?", (account_id,))
    return dict(rows[0])


async def release_account(account_id: int) -> None:
    """Release a reserved account back to available."""
    db = await get_db()
    await db.execute(
        """UPDATE accounts SET status = 'available', reserved_for_order_id = NULL,
           updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
        (account_id,)
    )
    await db.commit()


async def get_stock_count(plan_id: int) -> int:
    """Get count of available accounts for a plan."""
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT COUNT(*) as cnt FROM accounts WHERE plan_id = ? AND status = 'available'",
        (plan_id,)
    )
    return rows[0]["cnt"]


async def get_stock_summary() -> list[dict]:
    """Get stock summary grouped by platform/plan for admin."""
    db = await get_db()
    rows = await db.execute_fetchall(
        """SELECT pl.name as platform_name, p.name as plan_name, p.id as plan_id,
           SUM(CASE WHEN a.status = 'available' THEN 1 ELSE 0 END) as available,
           SUM(CASE WHEN a.status = 'reserved' THEN 1 ELSE 0 END) as reserved,
           SUM(CASE WHEN a.status = 'sold' THEN 1 ELSE 0 END) as sold,
           COUNT(a.id) as total
           FROM plans p
           JOIN platforms pl ON p.platform_id = pl.id
           LEFT JOIN accounts a ON a.plan_id = p.id
           GROUP BY p.id
           ORDER BY pl.sort_order, p.sort_order"""
    )
    return [dict(r) for r in rows]


async def get_accounts(plan_id: int | None = None, status: str | None = None,
                       limit: int = 100, offset: int = 0) -> list[dict]:
    """Get paginated accounts list for admin."""
    db = await get_db()
    conditions = []
    params = []
    if plan_id:
        conditions.append("a.plan_id = ?")
        params.append(plan_id)
    if status:
        conditions.append("a.status = ?")
        params.append(status)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = await db.execute_fetchall(
        f"""SELECT a.*, p.name as plan_name, pl.name as platform_name
            FROM accounts a
            JOIN plans p ON a.plan_id = p.id
            JOIN platforms pl ON p.platform_id = pl.id
            {where}
            ORDER BY a.created_at DESC LIMIT ? OFFSET ?""",
        params + [limit, offset]
    )
    return [dict(r) for r in rows]


async def update_account(account_id: int, **kwargs) -> dict | None:
    """Update account fields (admin)."""
    db = await get_db()
    allowed = {"login", "password", "notes", "status"}
    updates = {k: v for k, v in kwargs.items() if k in allowed and v is not None}
    if not updates:
        rows = await db.execute_fetchall("SELECT * FROM accounts WHERE id = ?", (account_id,))
        return dict(rows[0]) if rows else None
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [account_id]
    await db.execute(
        f"UPDATE accounts SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        values
    )
    await db.commit()
    rows = await db.execute_fetchall("SELECT * FROM accounts WHERE id = ?", (account_id,))
    return dict(rows[0]) if rows else None

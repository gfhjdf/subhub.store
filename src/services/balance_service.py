"""Balance service — manage user balances and transactions."""
from src.database.connection import get_db


async def get_balance(user_id: int) -> int:
    """Get user's current balance in UZS."""
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT balance_uzs FROM users WHERE id = ?", (user_id,)
    )
    return rows[0]["balance_uzs"] if rows else 0


async def add_balance(user_id: int, amount: int, tx_type: str,
                      order_id: int | None = None, related_user_id: int | None = None,
                      comment: str | None = None) -> int:
    """Add to user's balance and create a transaction record. Returns new balance."""
    db = await get_db()
    await db.execute(
        "UPDATE users SET balance_uzs = balance_uzs + ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (amount, user_id)
    )
    await db.execute(
        """INSERT INTO balance_transactions (user_id, type, amount_uzs, order_id, related_user_id, comment)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (user_id, tx_type, amount, order_id, related_user_id, comment)
    )
    await db.commit()
    return await get_balance(user_id)


async def reserve_balance(user_id: int, amount: int, order_id: int) -> None:
    """Reserve balance for a hybrid order (deduct from user balance)."""
    db = await get_db()
    await db.execute(
        "UPDATE users SET balance_uzs = balance_uzs - ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (amount, user_id)
    )
    await db.execute(
        """INSERT INTO balance_transactions (user_id, type, amount_uzs, order_id, comment)
           VALUES (?, 'order_reserve', ?, ?, 'Balance reserved for hybrid order')""",
        (user_id, -amount, order_id)
    )
    await db.commit()


async def release_balance(user_id: int, amount: int, order_id: int) -> None:
    """Release reserved balance back to user (on rejection/cancellation)."""
    db = await get_db()
    await db.execute(
        "UPDATE users SET balance_uzs = balance_uzs + ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (amount, user_id)
    )
    await db.execute(
        """INSERT INTO balance_transactions (user_id, type, amount_uzs, order_id, comment)
           VALUES (?, 'order_release', ?, ?, 'Balance restored after order rejection/cancellation')""",
        (user_id, amount, order_id)
    )
    await db.commit()


async def spend_balance(user_id: int, amount: int, order_id: int) -> None:
    """Permanently spend balance for an order (balance-only payment)."""
    db = await get_db()
    await db.execute(
        "UPDATE users SET balance_uzs = balance_uzs - ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (amount, user_id)
    )
    await db.execute(
        """INSERT INTO balance_transactions (user_id, type, amount_uzs, order_id, comment)
           VALUES (?, 'order_spend', ?, ?, 'Balance spent for order')""",
        (user_id, -amount, order_id)
    )
    await db.commit()


async def get_transactions(user_id: int, limit: int = 50) -> list[dict]:
    """Get user's balance transaction history."""
    db = await get_db()
    rows = await db.execute_fetchall(
        """SELECT * FROM balance_transactions WHERE user_id = ?
           ORDER BY created_at DESC LIMIT ?""",
        (user_id, limit)
    )
    return [dict(r) for r in rows]

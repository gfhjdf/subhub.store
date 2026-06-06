"""Points service — manage user points balances, check-ins, and point transactions."""
from datetime import datetime
from src.database.connection import get_db
from src.services import settings_service


async def get_points_balance(user_id: int) -> int:
    """Get user's current points balance."""
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT points_balance FROM users WHERE id = ?", (user_id,)
    )
    return rows[0]["points_balance"] if rows else 0


async def add_points(user_id: int, amount: int, tx_type: str,
                     redemption_id: int | None = None,
                     description: str | None = None) -> int:
    """Add points to user's balance and create a transaction record. Returns new points balance."""
    db = await get_db()
    await db.execute(
        "UPDATE users SET points_balance = points_balance + ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (amount, user_id)
    )
    await db.execute(
        """INSERT INTO points_transactions (user_id, type, points, redemption_id, description)
           VALUES (?, ?, ?, ?, ?)""",
        (user_id, tx_type, amount, redemption_id, description)
    )
    await db.commit()
    return await get_points_balance(user_id)


async def get_points_transactions(user_id: int, limit: int = 50) -> list[dict]:
    """Get points transaction history for a user."""
    db = await get_db()
    rows = await db.execute_fetchall(
        """SELECT * FROM points_transactions WHERE user_id = ?
           ORDER BY created_at DESC LIMIT ?""",
        (user_id, limit)
    )
    return [dict(r) for r in rows]


async def has_checked_in_today(user_id: int) -> bool:
    """Check if the user has already checked in today."""
    db = await get_db()
    today_str = datetime.now().date().isoformat()
    rows = await db.execute_fetchall(
        "SELECT id FROM daily_checkins WHERE user_id = ? AND checkin_date = ?",
        (user_id, today_str)
    )
    return len(rows) > 0


async def claim_daily_checkin(user_id: int) -> tuple[bool, int, str]:
    """
    Claim daily check-in points for the user.
    Returns (success, points_rewarded, status_code)
    """
    db = await get_db()
    
    # Check if already checked in today
    already_claimed = await has_checked_in_today(user_id)
    if already_claimed:
        return False, 0, "already_claimed"
        
    # Get points amount from settings
    points_val = await settings_service.get_setting("points_per_daily_checkin")
    points = int(points_val) if points_val else 1
    
    today_str = datetime.now().date().isoformat()
    
    try:
        # Enforce checkin record
        await db.execute(
            "INSERT INTO daily_checkins (user_id, checkin_date, points_rewarded) VALUES (?, ?, ?)",
            (user_id, today_str, points)
        )
        
        # Credit user points
        await add_points(
            user_id=user_id,
            amount=points,
            tx_type="daily_checkin",
            description="Daily check-in points reward"
        )
        
        await db.commit()
        return True, points, "claimed"
    except Exception as e:
        await db.rollback()
        raise e

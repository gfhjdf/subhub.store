"""Referral service — apply referrals, detect suspicious activity, manage rewards."""
import json
from datetime import datetime, timedelta
from src.database.connection import get_db
from src.services import balance_service, settings_service, points_service
from src.config import REFERRAL_REWARD_UZS, SUSPICIOUS_REFERRAL_THRESHOLD, SUSPICIOUS_REFERRAL_WINDOW_HOURS


async def apply_referral(inviter_code: str, invited_telegram_id: int) -> dict:
    """
    Apply a referral when a new user starts the bot.
    Returns {success: bool, message: str, suspicious: bool}
    """
    db = await get_db()

    # Get inviter by referral code
    inviter_rows = await db.execute_fetchall(
        "SELECT * FROM users WHERE referral_code = ?", (inviter_code,)
    )
    if not inviter_rows:
        return {"success": False, "message": "Invalid referral code", "suspicious": False}

    inviter = dict(inviter_rows[0])

    # Get invited user
    invited_rows = await db.execute_fetchall(
        "SELECT * FROM users WHERE telegram_id = ?", (invited_telegram_id,)
    )
    if not invited_rows:
        return {"success": False, "message": "Invited user not found", "suspicious": False}

    invited = dict(invited_rows[0])

    # Self-referral check
    if inviter["id"] == invited["id"]:
        return {"success": False, "message": "Self-referral not allowed", "suspicious": False}

    # Already referred check
    if invited["referred_by_user_id"] is not None:
        return {"success": False, "message": "User already referred", "suspicious": False}

    # Duplicate referral check
    existing = await db.execute_fetchall(
        "SELECT id FROM referrals WHERE invited_user_id = ?", (invited["id"],)
    )
    if existing:
        return {"success": False, "message": "Referral already recorded", "suspicious": False}

    # Check for suspicious activity (10+ referrals in 1 hour)
    suspicious = await _check_suspicious(inviter["id"])

    # Create referral record (money reward is 0 now)
    status = "flagged" if suspicious else "credited"
    await db.execute(
        """INSERT INTO referrals (inviter_user_id, invited_user_id, reward_uzs, status)
           VALUES (?, ?, 0, ?)""",
        (inviter["id"], invited["id"], status)
    )

    # Update invited user's referred_by
    await db.execute(
        "UPDATE users SET referred_by_user_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (inviter["id"], invited["id"])
    )

    if not suspicious:
        # Get points amount from settings
        points_val = await settings_service.get_setting("points_per_referral")
        points = int(points_val) if points_val else 1

        # Credit inviter points
        await points_service.add_points(
            user_id=inviter["id"],
            amount=points,
            tx_type="referral",
            description=f"Referral reward for inviting user {invited['telegram_id']}"
        )
    else:
        # Create system alert
        await db.execute(
            """INSERT INTO system_alerts (type, severity, user_id, related_user_id, payload_json)
               VALUES ('suspicious_referral', 'warning', ?, ?, ?)""",
            (inviter["id"], invited["id"],
             json.dumps({"inviter_telegram_id": inviter["telegram_id"],
                         "invited_telegram_id": invited_telegram_id,
                         "reason": f"10+ referrals in {SUSPICIOUS_REFERRAL_WINDOW_HOURS}h"}))
        )

    await db.commit()

    return {
        "success": not suspicious,
        "message": "Referral applied" if not suspicious else "Referral flagged as suspicious",
        "suspicious": suspicious,
        "inviter_id": inviter["id"],
        "inviter_telegram_id": inviter["telegram_id"]
    }


async def _check_suspicious(inviter_user_id: int) -> bool:
    """Check if inviter has 10+ referrals in the last hour."""
    db = await get_db()
    window = datetime.utcnow() - timedelta(hours=SUSPICIOUS_REFERRAL_WINDOW_HOURS)
    rows = await db.execute_fetchall(
        """SELECT COUNT(*) as cnt FROM referrals
           WHERE inviter_user_id = ? AND created_at >= ?""",
        (inviter_user_id, window.isoformat())
    )
    return rows[0]["cnt"] >= SUSPICIOUS_REFERRAL_THRESHOLD


async def get_referral_info(user_id: int) -> dict:
    """Get referral info for a user."""
    db = await get_db()

    # Get user's referral code
    user_rows = await db.execute_fetchall(
        "SELECT referral_code FROM users WHERE id = ?", (user_id,)
    )
    if not user_rows:
        return {"code": "", "link": "", "invited_count": 0, "total_earned": 0, "total_points_earned": 0}

    code = user_rows[0]["referral_code"]

    # Count invited users
    count_rows = await db.execute_fetchall(
        "SELECT COUNT(*) as cnt FROM referrals WHERE inviter_user_id = ? AND status = 'credited'",
        (user_id,)
    )
    invited_count = count_rows[0]["cnt"]

    # Total earned (cash UZS - for legacy)
    earned_rows = await db.execute_fetchall(
        "SELECT COALESCE(SUM(reward_uzs), 0) as total FROM referrals WHERE inviter_user_id = ? AND status = 'credited'",
        (user_id,)
    )
    total_earned = earned_rows[0]["total"]

    # Total points earned
    points_rows = await db.execute_fetchall(
        "SELECT COALESCE(SUM(points), 0) as total FROM points_transactions WHERE user_id = ? AND type = 'referral'",
        (user_id,)
    )
    total_points = points_rows[0]["total"]

    return {
        "code": code,
        "link": "",  # Will be constructed by the bot with bot username
        "invited_count": invited_count,
        "total_earned": total_earned,
        "total_points_earned": total_points,
    }


async def get_all_referrals(limit: int = 100, offset: int = 0) -> list[dict]:
    """Get referral list for admin."""
    db = await get_db()
    rows = await db.execute_fetchall(
        """SELECT r.*,
           inv.telegram_username as inviter_username, inv.telegram_id as inviter_telegram_id,
           itd.telegram_username as invited_username, itd.telegram_id as invited_telegram_id
           FROM referrals r
           JOIN users inv ON r.inviter_user_id = inv.id
           JOIN users itd ON r.invited_user_id = itd.id
           ORDER BY r.created_at DESC LIMIT ? OFFSET ?""",
        (limit, offset)
    )
    return [dict(r) for r in rows]


async def get_system_alerts(status: str | None = None, limit: int = 50) -> list[dict]:
    """Get system alerts for admin."""
    db = await get_db()
    if status:
        rows = await db.execute_fetchall(
            """SELECT sa.*, u.telegram_username, u.telegram_id as alert_user_telegram_id
               FROM system_alerts sa
               LEFT JOIN users u ON sa.user_id = u.id
               WHERE sa.status = ? ORDER BY sa.created_at DESC LIMIT ?""",
            (status, limit)
        )
    else:
        rows = await db.execute_fetchall(
            """SELECT sa.*, u.telegram_username, u.telegram_id as alert_user_telegram_id
               FROM system_alerts sa
               LEFT JOIN users u ON sa.user_id = u.id
               ORDER BY sa.created_at DESC LIMIT ?""",
            (limit,)
        )
    return [dict(r) for r in rows]

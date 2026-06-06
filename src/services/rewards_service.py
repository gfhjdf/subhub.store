"""Rewards service — manage configured prizes/rewards and redemption requests."""
import uuid
from src.database.connection import get_db
from src.services import points_service


# ── Rewards CRUD ──────────────────────────────────────────

async def get_active_rewards() -> list[dict]:
    """Get all active rewards for the bot shop."""
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT * FROM rewards WHERE is_active = 1 ORDER BY points_required ASC, name ASC"
    )
    return [dict(r) for r in rows]


async def get_all_rewards() -> list[dict]:
    """Get all rewards (active/inactive) for the admin catalog."""
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT * FROM rewards ORDER BY points_required ASC, name ASC"
    )
    return [dict(r) for r in rows]


async def get_reward_by_id(reward_id: int) -> dict | None:
    """Get a reward by ID."""
    db = await get_db()
    rows = await db.execute_fetchall("SELECT * FROM rewards WHERE id = ?", (reward_id,))
    return dict(rows[0]) if rows else None


async def create_reward(name: str, description_uz: str, description_ru: str,
                        points_required: int, plan_id: int | None = None, is_active: bool = True) -> dict:
    """Create a new reward prize in the database."""
    db = await get_db()
    cursor = await db.execute(
        """INSERT INTO rewards (name, description_uz, description_ru, points_required, plan_id, is_active)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (name, description_uz, description_ru, points_required, plan_id, int(is_active))
    )
    reward_id = cursor.lastrowid
    await db.commit()
    return await get_reward_by_id(reward_id)


async def update_reward(reward_id: int, **kwargs) -> dict | None:
    """Update a reward's details."""
    db = await get_db()
    allowed = {"name", "description_uz", "description_ru", "points_required", "plan_id", "is_active"}
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return await get_reward_by_id(reward_id)
    if "is_active" in updates and updates["is_active"] is not None:
        updates["is_active"] = int(updates["is_active"])
        
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [reward_id]
    await db.execute(
        f"UPDATE rewards SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        values
    )
    await db.commit()
    return await get_reward_by_id(reward_id)


async def delete_reward(reward_id: int) -> bool:
    """Delete a reward."""
    db = await get_db()
    await db.execute("DELETE FROM rewards WHERE id = ?", (reward_id,))
    await db.commit()
    return True


# ── Redemptions ───────────────────────────────────────────

async def get_redemption_by_id(redemption_id: int) -> dict | None:
    """Get a redemption by internal ID."""
    db = await get_db()
    rows = await db.execute_fetchall(
        """SELECT r.*, rw.name as reward_name, rw.description_uz as reward_desc_uz, rw.description_ru as reward_desc_ru,
           u.telegram_id, u.telegram_username, u.first_name as user_first_name,
           a.login as account_login, a.password as account_password, a.notes as account_notes
           FROM redemptions r
           JOIN rewards rw ON r.reward_id = rw.id
           JOIN users u ON r.user_id = u.id
           LEFT JOIN accounts a ON r.account_id = a.id
           WHERE r.id = ?""",
        (redemption_id,)
    )
    return dict(rows[0]) if rows else None


async def create_redemption(user_id: int, reward_id: int) -> dict:
    """Create a new redemption request for a user."""
    db = await get_db()
    
    # 1. Fetch reward
    reward = await get_reward_by_id(reward_id)
    if not reward:
        raise ValueError("Reward not found")
    if not reward["is_active"]:
        raise ValueError("Reward is currently inactive")

    # 2. Auto-delivery check (if plan_id is linked)
    account_id = None
    if reward.get("plan_id") is not None:
        account_rows = await db.execute_fetchall(
            "SELECT id FROM accounts WHERE plan_id = ? AND status = 'available' LIMIT 1",
            (reward["plan_id"],)
        )
        if account_rows:
            account_id = account_rows[0]["id"]
        
    # 3. Check points balance
    user_points = await points_service.get_points_balance(user_id)
    points_required = reward["points_required"]
    if user_points < points_required:
        raise ValueError("Insufficient points balance")
        
    # 4. Create redemption
    public_id = f"RD-{uuid.uuid4().hex[:8].upper()}"
    status = "completed" if account_id is not None else "pending"
    cursor = await db.execute(
        """INSERT INTO redemptions (public_redemption_id, user_id, reward_id, account_id, points_spent, status)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (public_id, user_id, reward_id, account_id, points_required, status)
    )
    redemption_id = cursor.lastrowid
    
    # 5. Mark account as sold if auto-delivered
    if account_id is not None:
        await db.execute(
            """UPDATE accounts SET status = 'sold', sold_to_user_id = ?, sold_at = CURRENT_TIMESTAMP,
               notes = COALESCE(notes, '') || ' [Redeemed via Gift Request ' || ? || ']'
               WHERE id = ?""",
            (user_id, public_id, account_id)
        )

    # 6. Deduct points and log points transaction
    await points_service.add_points(
        user_id=user_id,
        amount=-points_required,
        tx_type="reward_redemption",
        redemption_id=redemption_id,
        description=f"Redeemed reward: {reward['name']}"
    )
    
    await db.commit()
    return await get_redemption_by_id(redemption_id)


async def get_user_redemptions(user_id: int) -> list[dict]:
    """Get all redemption requests for a specific user."""
    db = await get_db()
    rows = await db.execute_fetchall(
        """SELECT r.*, rw.name as reward_name, rw.description_uz as reward_desc_uz, rw.description_ru as reward_desc_ru,
           a.login as account_login, a.password as account_password, a.notes as account_notes
           FROM redemptions r
           JOIN rewards rw ON r.reward_id = rw.id
           LEFT JOIN accounts a ON r.account_id = a.id
           WHERE r.user_id = ?
           ORDER BY r.created_at DESC""",
          (user_id,)
    )
    return [dict(r) for r in rows]


async def get_all_redemptions(status: str | None = None, limit: int = 50, offset: int = 0) -> list[dict]:
    """Get redemptions for admin panel."""
    db = await get_db()
    params = []
    where_clause = ""
    if status:
        where_clause = "WHERE r.status = ?"
        params.append(status)
        
    query = f"""SELECT r.*, rw.name as reward_name,
               u.telegram_id, u.telegram_username, u.first_name as user_first_name,
               a.login as account_login, a.password as account_password
               FROM redemptions r
               JOIN rewards rw ON r.reward_id = rw.id
               JOIN users u ON r.user_id = u.id
               LEFT JOIN accounts a ON r.account_id = a.id
               {where_clause}
               ORDER BY r.created_at DESC LIMIT ? OFFSET ?"""
               
    rows = await db.execute_fetchall(query, params + [limit, offset])
    return [dict(r) for r in rows]


async def get_redemptions_count(status: str | None = None) -> int:
    """Get total redemptions count, optionally filtered by status."""
    db = await get_db()
    params = []
    where_clause = ""
    if status:
        where_clause = "WHERE status = ?"
        params.append(status)
        
    rows = await db.execute_fetchall(
        f"SELECT COUNT(*) as cnt FROM redemptions {where_clause}", params
    )
    return rows[0]["cnt"]


async def process_redemption(redemption_id: int, status: str, admin_id: int,
                             rejection_note: str | None = None) -> dict:
    """Update redemption request status (approve, reject, complete)."""
    db = await get_db()
    
    redemption = await get_redemption_by_id(redemption_id)
    if not redemption:
        raise ValueError("Redemption request not found")
        
    current_status = redemption["status"]
    if current_status == status:
        return redemption
        
    if status not in ("pending", "approved", "rejected", "completed"):
        raise ValueError("Invalid target status")
        
    # If rejecting, we must refund points
    if status == "rejected":
        # Check if points were already refunded
        if current_status == "rejected":
            pass
        else:
            await points_service.add_points(
                user_id=redemption["user_id"],
                amount=redemption["points_spent"],
                tx_type="refund",
                redemption_id=redemption_id,
                description=f"Points refund for rejected redemption #{redemption['public_redemption_id']}"
            )
            
    await db.execute(
        """UPDATE redemptions SET status = ?, rejection_note = ?,
           processed_by_admin_id = ?, processed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
           WHERE id = ?""",
        (status, rejection_note, admin_id, redemption_id)
    )
    await db.commit()
    return await get_redemption_by_id(redemption_id)

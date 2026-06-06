"""Wallet service — manage user wallet balance, top-up requests, and audit logs."""
import uuid
from datetime import datetime
from src.database.connection import get_db

async def get_wallet_balance(user_id: int) -> int:
    """Get user's current wallet balance (balance_uzs) in UZS."""
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT balance_uzs FROM users WHERE id = ?", (user_id,)
    )
    return rows[0]["balance_uzs"] if rows else 0

async def add_wallet_balance(
    user_id: int,
    amount: int,
    tx_type: str,
    order_id: int | None = None,
    top_up_request_id: int | None = None,
    description: str | None = None
) -> int:
    """
    Atomically updates balance_uzs for the user and records a transaction log.
    Ensures safe transaction commit. Returns new balance.
    """
    db = await get_db()
    # We do a sequential execute. Since there's one global connection,
    # we can retrieve the balance and update within the same logical sequence.
    # Note: sqlite requires a commit.
    rows = await db.execute_fetchall(
        "SELECT balance_uzs FROM users WHERE id = ?", (user_id,)
    )
    if not rows:
        raise ValueError("User not found")
    balance_before = rows[0]["balance_uzs"]
    balance_after = balance_before + amount

    if balance_after < 0:
        raise ValueError("Insufficient wallet balance")

    await db.execute(
        "UPDATE users SET balance_uzs = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        (balance_after, user_id)
    )

    await db.execute(
        """INSERT INTO wallet_transactions (
            user_id, type, amount, balance_before, balance_after,
            order_id, top_up_request_id, description
           ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        (user_id, tx_type, amount, balance_before, balance_after,
         order_id, top_up_request_id, description)
    )
    await db.commit()
    return balance_after

async def create_topup_request(
    user_id: int,
    amount_requested: int,
    screenshot_path: str | None = None,
    screenshot_file_id: str | None = None
) -> dict:
    """Create a pending wallet topup request."""
    db = await get_db()
    public_topup_id = f"WT-{uuid.uuid4().hex[:8].upper()}"
    cursor = await db.execute(
        """INSERT INTO wallet_topups (
            public_topup_id, user_id, amount_requested, status,
            screenshot_path, screenshot_file_id
           ) VALUES (?, ?, ?, 'pending', ?, ?)""",
        (public_topup_id, user_id, amount_requested, screenshot_path, screenshot_file_id)
    )
    topup_id = cursor.lastrowid
    await db.commit()
    return await get_topup_by_id(topup_id)

async def get_topup_by_id(topup_id: int) -> dict | None:
    """Get topup details."""
    db = await get_db()
    rows = await db.execute_fetchall(
        """SELECT wt.*, u.telegram_id, u.telegram_username, u.first_name, u.last_name, u.language_code
           FROM wallet_topups wt
           JOIN users u ON wt.user_id = u.id
           WHERE wt.id = ?""",
        (topup_id,)
    )
    return dict(rows[0]) if rows else None

async def get_topup_by_public_id(public_topup_id: str) -> dict | None:
    """Get topup details by public ID."""
    db = await get_db()
    rows = await db.execute_fetchall(
        """SELECT wt.*, u.telegram_id, u.telegram_username, u.first_name, u.last_name, u.language_code
           FROM wallet_topups wt
           JOIN users u ON wt.user_id = u.id
           WHERE wt.public_topup_id = ?""",
        (public_topup_id,)
    )
    return dict(rows[0]) if rows else None

async def get_all_topups(status: str | None = None, limit: int = 50, offset: int = 0) -> list[dict]:
    """Get list of top-up requests."""
    db = await get_db()
    if status:
        rows = await db.execute_fetchall(
            """SELECT wt.*, u.telegram_id, u.telegram_username, u.first_name, u.last_name
               FROM wallet_topups wt
               JOIN users u ON wt.user_id = u.id
               WHERE wt.status = ?
               ORDER BY wt.created_at DESC LIMIT ? OFFSET ?""",
            (status, limit, offset)
        )
    else:
        rows = await db.execute_fetchall(
            """SELECT wt.*, u.telegram_id, u.telegram_username, u.first_name, u.last_name
               FROM wallet_topups wt
               JOIN users u ON wt.user_id = u.id
               ORDER BY wt.created_at DESC LIMIT ? OFFSET ?""",
            (limit, offset)
        )
    return [dict(r) for r in rows]

async def process_topup(
    topup_id: int,
    status: str,
    amount_approved: int | None = None,
    rejection_note: str | None = None,
    admin_id: int | None = None
) -> dict:
    """
    Process top-up request (approve or reject).
    Credits user's balance and writes transaction log on approval.
    """
    db = await get_db()
    
    # Retrieve current top-up details and check if it's already processed
    topup = await get_topup_by_id(topup_id)
    if not topup:
        raise ValueError("Top-up request not found")
    if topup["status"] != "pending":
        raise ValueError("Top-up request is already processed")

    if status == "approved":
        if amount_approved is None or amount_approved <= 0:
            raise ValueError("Invalid approved amount")

        # Update topup status
        await db.execute(
            """UPDATE wallet_topups
               SET status = 'approved', amount_approved = ?, processed_by_admin_id = ?,
                   processed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (amount_approved, admin_id, topup_id)
        )

        # Credit user wallet balance atomically
        await add_wallet_balance(
            user_id=topup["user_id"],
            amount=amount_approved,
            tx_type="top_up",
            top_up_request_id=topup_id,
            description=f"Wallet topped up via request {topup['public_topup_id']}"
        )
    elif status == "rejected":
        # Update topup status to rejected
        await db.execute(
            """UPDATE wallet_topups
               SET status = 'rejected', rejection_note = ?, processed_by_admin_id = ?,
                   processed_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP
               WHERE id = ?""",
            (rejection_note, admin_id, topup_id)
        )
    else:
        raise ValueError("Invalid process status")

    await db.commit()
    return await get_topup_by_id(topup_id)

async def pay_with_wallet(user_id: int, amount: int, order_id: int) -> int:
    """Deduct balance atomically for a purchase."""
    return await add_wallet_balance(
        user_id=user_id,
        amount=-amount,
        tx_type="purchase",
        order_id=order_id,
        description=f"Wallet purchase for order #{order_id}"
    )

async def get_wallet_transactions(user_id: int, limit: int = 50, offset: int = 0) -> list[dict]:
    """Get user's wallet transactions history."""
    db = await get_db()
    rows = await db.execute_fetchall(
        """SELECT * FROM wallet_transactions WHERE user_id = ?
           ORDER BY created_at DESC, id DESC LIMIT ? OFFSET ?""",
        (user_id, limit, offset)
    )
    return [dict(r) for r in rows]

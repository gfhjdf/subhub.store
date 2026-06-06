"""Order service — create, manage, approve/reject, and deliver orders."""
import uuid
from src.database.connection import get_db
from src.services import account_service, wallet_service


async def create_order(user_id: int, platform_id: int, plan_id: int,
                       payment_method: str, price: int,
                       balance_used: int = 0, card_due: int = 0) -> dict:
    """Create a new order. Returns order dict."""
    db = await get_db()
    public_id = f"SH-{uuid.uuid4().hex[:8].upper()}"

    status = "created"
    if payment_method == "balance":
        status = "created"  # Will be auto-delivered immediately after
    elif payment_method in ("full_card", "hybrid"):
        status = "pending_payment"

    cursor = await db.execute(
        """INSERT INTO orders (public_order_id, user_id, platform_id, plan_id,
           payment_method, price_original_uzs, balance_used_uzs, card_due_uzs, status)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (public_id, user_id, platform_id, plan_id,
         payment_method, price, balance_used, card_due, status)
    )
    order_id = cursor.lastrowid
    await db.commit()

    if status == "pending_payment":
        # Atomically reserve an account for this order immediately
        account = await account_service.reserve_account(plan_id, order_id)
        if not account:
            # Release hybrid balance if reserved
            if payment_method == "hybrid" and balance_used > 0:
                await wallet_service.add_wallet_balance(
                    user_id=user_id,
                    amount=balance_used,
                    tx_type="refund",
                    description="Refund - hybrid order stock fail"
                )
            raise ValueError("No stock available")
        
        # Save reserved account_id in order
        await db.execute(
            "UPDATE orders SET account_id = ? WHERE id = ?",
            (account["id"], order_id)
        )
        await db.commit()

    return await get_order_by_id(order_id)


async def get_order_by_id(order_id: int) -> dict | None:
    """Get order with joined platform/plan names."""
    db = await get_db()
    rows = await db.execute_fetchall(
        """SELECT o.*, p.name as plan_name, pl.name as platform_name,
           pl.custom_emoji_code as platform_emoji_code,
           a.login as account_login, a.password as account_password
           FROM orders o
           JOIN plans p ON o.plan_id = p.id
           JOIN platforms pl ON o.platform_id = pl.id
           LEFT JOIN accounts a ON o.account_id = a.id
           WHERE o.id = ?""",
        (order_id,)
    )
    return dict(rows[0]) if rows else None


async def get_order_by_public_id(public_id: str) -> dict | None:
    """Get order by public order ID."""
    db = await get_db()
    rows = await db.execute_fetchall(
        """SELECT o.*, p.name as plan_name, pl.name as platform_name,
           pl.custom_emoji_code as platform_emoji_code,
           a.login as account_login, a.password as account_password
           FROM orders o
           JOIN plans p ON o.plan_id = p.id
           JOIN platforms pl ON o.platform_id = pl.id
           LEFT JOIN accounts a ON o.account_id = a.id
           WHERE o.public_order_id = ?""",
        (public_id,)
    )
    return dict(rows[0]) if rows else None


async def get_user_orders(user_id: int) -> list[dict]:
    """Get all orders for a user."""
    db = await get_db()
    rows = await db.execute_fetchall(
        """SELECT o.*, p.name as plan_name, pl.name as platform_name,
           pl.custom_emoji_code as platform_emoji_code,
           a.login as account_login, a.password as account_password
           FROM orders o
           JOIN plans p ON o.plan_id = p.id
           JOIN platforms pl ON o.platform_id = pl.id
           LEFT JOIN accounts a ON o.account_id = a.id
           WHERE o.user_id = ?
           ORDER BY o.created_at DESC""",
        (user_id,)
    )
    return [dict(r) for r in rows]


async def get_active_unpaid_order(user_id: int) -> dict | None:
    """Check if user has an active unpaid order (prevent multiple simultaneous orders)."""
    db = await get_db()
    rows = await db.execute_fetchall(
        """SELECT * FROM orders WHERE user_id = ?
           AND status IN ('created', 'pending_payment', 'payment_submitted', 'under_review')
           LIMIT 1""",
        (user_id,)
    )
    return dict(rows[0]) if rows else None


async def save_screenshot(order_id: int, file_id: str, file_path: str) -> None:
    """Save payment screenshot and update order status."""
    db = await get_db()
    await db.execute(
        """UPDATE orders SET payment_screenshot_file_id = ?, payment_screenshot_path = ?,
           status = 'payment_submitted', updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
        (file_id, file_path, order_id)
    )
    await db.commit()


async def cancel_order(order_id: int) -> dict:
    """Cancel an unpaid order. Restores hybrid balance if needed."""
    db = await get_db()
    order = await get_order_by_id(order_id)
    if not order:
        raise ValueError("Order not found")
    if order["status"] not in ("created", "pending_payment"):
        raise ValueError("Cannot cancel order in current status")

    # Restore hybrid balance if applicable
    if order["payment_method"] == "hybrid" and order["balance_used_uzs"] > 0:
        await wallet_service.add_wallet_balance(
            user_id=order["user_id"],
            amount=order["balance_used_uzs"],
            tx_type="refund",
            order_id=order_id,
            description=f"Refund for cancelled order #{order_id}"
        )

    # Release reserved account if any
    if order["account_id"]:
        await account_service.release_account(order["account_id"])

    await db.execute(
        """UPDATE orders SET status = 'cancelled', cancelled_at = CURRENT_TIMESTAMP,
           updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
        (order_id,)
    )
    await db.commit()
    return await get_order_by_id(order_id)


async def auto_deliver_order(order_id: int) -> dict:
    """Auto-deliver a balance-only order: deduct balance, assign account, deliver."""
    db = await get_db()
    order = await get_order_by_id(order_id)
    if not order:
        raise ValueError("Order not found")

    # Deduct balance
    await wallet_service.pay_with_wallet(
        order["user_id"], order["price_original_uzs"], order_id
    )

    # Reserve and assign account atomically
    account = await account_service.reserve_account(order["plan_id"], order_id)
    if not account:
        # Refund balance if no stock
        await wallet_service.add_wallet_balance(
            user_id=order["user_id"],
            amount=order["price_original_uzs"],
            tx_type="refund",
            order_id=order_id,
            description="Refund - no stock available"
        )
        await db.execute(
            "UPDATE orders SET status = 'failed', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
            (order_id,)
        )
        await db.commit()
        raise ValueError("No stock available")

    await account_service.assign_account(account["id"], order_id, order["user_id"])

    # Update order
    await db.execute(
        """UPDATE orders SET account_id = ?, status = 'delivered',
           delivered_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
        (account["id"], order_id)
    )
    await db.commit()
    return await get_order_by_id(order_id)


async def approve_order(order_id: int, admin_id: int) -> dict:
    """Admin approves a screenshot-based order. Assigns account and delivers."""
    db = await get_db()
    order = await get_order_by_id(order_id)
    if not order:
        raise ValueError("Order not found")
    if order["status"] not in ("payment_submitted", "under_review"):
        raise ValueError("Order not in reviewable status")

    account_id = order.get("account_id")
    if not account_id:
        # Reserve and assign account if somehow not reserved yet
        account = await account_service.reserve_account(order["plan_id"], order_id)
        if not account:
            raise ValueError("No stock available for this plan")
        account_id = account["id"]

    await account_service.assign_account(account_id, order_id, order["user_id"])

    # Finalize hybrid balance spend
    if order["payment_method"] == "hybrid" and order["balance_used_uzs"] > 0:
        await wallet_service.add_wallet_balance(
            user_id=order["user_id"],
            amount=0,
            tx_type="purchase",
            order_id=order_id,
            description=f"Wallet spend finalized for hybrid order #{order_id}"
        )

    # Update order
    await db.execute(
        """UPDATE orders SET account_id = ?, status = 'delivered', approved_by_admin_id = ?,
           approved_at = CURRENT_TIMESTAMP, delivered_at = CURRENT_TIMESTAMP,
           updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
        (account_id, admin_id, order_id)
    )
    await db.commit()
    return await get_order_by_id(order_id)


async def reject_order(order_id: int, admin_id: int,
                       reason_code: str | None = None, note: str | None = None) -> dict:
    """Admin rejects an order. Restores hybrid balance if applicable."""
    db = await get_db()
    order = await get_order_by_id(order_id)
    if not order:
        raise ValueError("Order not found")
    if order["status"] not in ("payment_submitted", "under_review"):
        raise ValueError("Order not in reviewable status")

    # Restore hybrid balance
    if order["payment_method"] == "hybrid" and order["balance_used_uzs"] > 0:
        await wallet_service.add_wallet_balance(
            user_id=order["user_id"],
            amount=order["balance_used_uzs"],
            tx_type="refund",
            order_id=order_id,
            description=f"Refund for rejected hybrid order #{order_id}"
        )

    # Release any reserved account
    if order["account_id"]:
        await account_service.release_account(order["account_id"])

    await db.execute(
        """UPDATE orders SET status = 'rejected', approved_by_admin_id = ?,
           rejection_reason_code = ?, rejection_note = ?,
           rejected_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE id = ?""",
        (admin_id, reason_code, note, order_id)
    )
    await db.commit()
    return await get_order_by_id(order_id)


async def get_all_orders(status: str | None = None, payment_method: str | None = None,
                         platform_id: int | None = None,
                         limit: int = 50, offset: int = 0) -> list[dict]:
    """Get paginated orders for admin."""
    db = await get_db()
    conditions = []
    params = []
    if status:
        conditions.append("o.status = ?")
        params.append(status)
    if payment_method:
        conditions.append("o.payment_method = ?")
        params.append(payment_method)
    if platform_id:
        conditions.append("o.platform_id = ?")
        params.append(platform_id)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = await db.execute_fetchall(
        f"""SELECT o.*, p.name as plan_name, pl.name as platform_name,
            u.telegram_id, u.telegram_username, u.first_name as user_first_name
            FROM orders o
            JOIN plans p ON o.plan_id = p.id
            JOIN platforms pl ON o.platform_id = pl.id
            JOIN users u ON o.user_id = u.id
            {where}
            ORDER BY o.created_at DESC LIMIT ? OFFSET ?""",
        params + [limit, offset]
    )
    return [dict(r) for r in rows]


async def get_orders_count(status: str | None = None, payment_method: str | None = None,
                           platform_id: int | None = None) -> int:
    """Get total order count, optionally filtered by status, payment_method, and platform_id."""
    db = await get_db()
    conditions = []
    params = []
    if status:
        conditions.append("status = ?")
        params.append(status)
    if payment_method:
        conditions.append("payment_method = ?")
        params.append(payment_method)
    if platform_id:
        conditions.append("platform_id = ?")
        params.append(platform_id)
    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    rows = await db.execute_fetchall(
        f"SELECT COUNT(*) as cnt FROM orders {where}", params
    )
    return rows[0]["cnt"]


async def get_expired_pending_orders(timeout_minutes: int = 15) -> list[dict]:
    """Get all pending_payment orders older than timeout_minutes (in UTC)."""
    db = await get_db()
    rows = await db.execute_fetchall(
        """SELECT o.id, o.public_order_id, o.user_id, u.telegram_id, u.language_code
           FROM orders o
           JOIN users u ON o.user_id = u.id
           WHERE o.status = 'pending_payment'
           AND o.created_at <= datetime('now', ?)""",
        (f"-{timeout_minutes} minutes",)
    )
    return [dict(r) for r in rows]


async def check_and_cancel_expired_orders_loop(timeout_minutes: int = 15) -> None:
    """Background task to run every minute and cancel expired reservations."""
    import asyncio
    import logging
    from src.bot.bot import get_bot
    from src.bot.texts import get_text
    
    logger = logging.getLogger("subhub.reservation_checker")
    
    while True:
        try:
            await asyncio.sleep(60)  # Check every minute
            expired_orders = await get_expired_pending_orders(timeout_minutes)
            if expired_orders:
                logger.info(f"Found {len(expired_orders)} expired pending orders.")
                bot = get_bot()
                for o in expired_orders:
                    try:
                        # Cancel order (restores hybrid balance, releases reserved account, sets status to 'cancelled')
                        await cancel_order(o["id"])
                        logger.info(f"Cancelled expired order #{o['public_order_id']} for user {o['user_id']}")
                        
                        # Send Telegram notification
                        lang = o.get("language_code", "uz")
                        msg = get_text("reservation_expired", lang).format(order_id=o["public_order_id"])
                        await bot.send_message(chat_id=o["telegram_id"], text=msg, parse_mode="HTML")
                    except Exception as e:
                        logger.error(f"Error cancelling expired order {o['id']}: {e}")
        except asyncio.CancelledError:
            break
        except Exception as e:
            logger.error(f"Error in reservation expiration loop: {e}", exc_info=True)


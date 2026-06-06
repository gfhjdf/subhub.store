"""Admin API routes — full CRUD for the SubHub.store admin panel."""
import logging
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from pydantic import BaseModel
from passlib.hash import bcrypt

from src.database.connection import get_db
from src.api.dependencies import create_access_token, get_current_admin
from src.services import (
    user_service,
    catalog_service,
    account_service,
    order_service,
    balance_service,
    referral_service,
    settings_service,
    audit_service,
    points_service,
    rewards_service,
    wallet_service,
)

logger = logging.getLogger("subhub.admin")

router = APIRouter(prefix="/api/admin", tags=["admin"])


# ─── Pydantic Models ────────────────────────────────────────

class LoginRequest(BaseModel):
    username: str
    password: str


class AdminUpdateCredentials(BaseModel):
    new_username: Optional[str] = None
    new_password: Optional[str] = None
    current_password: str


class PlatformCreate(BaseModel):
    name: str
    slug: str
    custom_emoji_code: Optional[str] = None
    is_active: bool = True
    sort_order: int = 0


class PlatformUpdate(BaseModel):
    name: Optional[str] = None
    slug: Optional[str] = None
    custom_emoji_code: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None


class PlanCreate(BaseModel):
    platform_id: int
    name: str
    price_uzs: int
    description_uz: str = ""
    description_ru: str = ""
    faq_uz: str = ""
    faq_ru: str = ""
    is_active: bool = True
    sort_order: int = 0
    plan_type: str = "regular"


class PlanUpdate(BaseModel):
    platform_id: Optional[int] = None
    name: Optional[str] = None
    price_uzs: Optional[int] = None
    description_uz: Optional[str] = None
    description_ru: Optional[str] = None
    faq_uz: Optional[str] = None
    faq_ru: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    plan_type: Optional[str] = None


class AccountCreate(BaseModel):
    plan_id: int
    login: str
    password: str
    notes: Optional[str] = None


class AccountBulk(BaseModel):
    plan_id: int
    accounts: list[dict]


class AccountUpdate(BaseModel):
    login: Optional[str] = None
    password: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None


class OrderAction(BaseModel):
    reason_code: Optional[str] = None
    note: Optional[str] = None


class SettingsUpdate(BaseModel):
    settings: dict


class BalanceAdjustment(BaseModel):
    amount: int
    comment: Optional[str] = None


class RewardCreate(BaseModel):
    name: str
    description_uz: str = ""
    description_ru: str = ""
    points_required: int
    plan_id: Optional[int] = None
    is_active: bool = True


class RewardUpdate(BaseModel):
    name: Optional[str] = None
    description_uz: Optional[str] = None
    description_ru: Optional[str] = None
    points_required: Optional[int] = None
    plan_id: Optional[int] = None
    is_active: Optional[bool] = None


class RedemptionProcess(BaseModel):
    status: str
    rejection_note: Optional[str] = None


class PointsAdjustment(BaseModel):
    amount: int
    description: Optional[str] = None


class WalletTopupProcess(BaseModel):
    status: str
    amount_approved: Optional[int] = None
    rejection_note: Optional[str] = None



# ─── AUTH ────────────────────────────────────────────────────

@router.post("/auth/login")
async def admin_login(req: LoginRequest):
    """Verify admin credentials and return JWT."""
    db = await get_db()
    rows = await db.execute_fetchall(
        "SELECT * FROM admin_users WHERE username = ? AND is_active = 1",
        (req.username,),
    )
    if not rows:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    admin = dict(rows[0])
    if not bcrypt.verify(req.password, admin["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    token = create_access_token({
        "admin_id": admin["id"],
        "username": admin["username"],
    })
    await audit_service.log_action(
        "admin", "admin_login", "admin_user", admin["id"],
        admin_id=admin["id"],
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "admin": {"id": admin["id"], "username": admin["username"]},
    }


@router.post("/auth/logout")
async def admin_logout(admin: dict = Depends(get_current_admin)):
    """Client-side token removal. Server acknowledges."""
    return {"message": "Logged out successfully"}


@router.get("/auth/me")
async def get_me(admin: dict = Depends(get_current_admin)):
    """Return current admin info from JWT."""
    return {
        "admin_id": admin["admin_id"],
        "username": admin["username"],
    }


@router.put("/auth/me")
async def update_admin_credentials(
    body: AdminUpdateCredentials,
    admin: dict = Depends(get_current_admin)
):
    db = await get_db()
    admin_id = admin["admin_id"]
    
    # Fetch admin details
    rows = await db.execute_fetchall("SELECT * FROM admin_users WHERE id = ?", (admin_id,))
    if not rows:
        raise HTTPException(status_code=404, detail="Admin user not found")
        
    admin_db = dict(rows[0])
    
    # Verify current password
    if not bcrypt.verify(body.current_password, admin_db["password_hash"]):
        raise HTTPException(status_code=400, detail="Неверный текущий пароль")
        
    updates = {}
    if body.new_username:
        new_user = body.new_username.strip()
        if not new_user:
            raise HTTPException(status_code=400, detail="Имя пользователя не может быть пустым")
        # Check uniqueness
        existing = await db.execute_fetchall(
            "SELECT id FROM admin_users WHERE username = ? AND id != ?",
            (new_user, admin_id)
        )
        if existing:
            raise HTTPException(status_code=400, detail="Имя пользователя уже занято")
        updates["username"] = new_user
        
    if body.new_password:
        new_pass = body.new_password.strip()
        if len(new_pass) < 6:
            raise HTTPException(status_code=400, detail="Пароль должен состоять минимум из 6 символов")
        updates["password_hash"] = bcrypt.hash(new_pass)
        
    if not updates:
        raise HTTPException(status_code=400, detail="Не указано имя пользователя или новый пароль для изменения")
        
    set_clause = ", ".join(f"{k} = ?" for k in updates)
    values = list(updates.values()) + [admin_id]
    
    await db.execute(
        f"UPDATE admin_users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        values
    )
    await db.commit()
    
    await audit_service.log_action(
        actor_type="admin",
        action="admin_credentials_updated",
        entity_type="admin_user",
        entity_id=admin_id,
        admin_id=admin_id,
        meta={"username_changed": bool(body.new_username), "password_changed": bool(body.new_password)}
    )
    
    return {"message": "Данные входа успешно обновлены"}


# ─── DASHBOARD ───────────────────────────────────────────────

@router.get("/dashboard/summary")
async def dashboard_summary(admin: dict = Depends(get_current_admin)):
    """Aggregate KPI data for the dashboard."""
    db = await get_db()

    # Order counts — only real paid sales (delivered), NOT gifts/cancelled/pending
    total_orders = await order_service.get_orders_count(status="delivered")
    pending_orders = await order_service.get_orders_count(status="payment_submitted")
    rejected_orders = await order_service.get_orders_count(status="rejected")

    # Revenue calculation — two genuine cash sources:
    # 1. Card orders: money came in when user paid by card (full_card, delivered)
    card_rev_rows = await db.execute_fetchall(
        "SELECT COALESCE(SUM(price_original_uzs), 0) as total FROM orders "
        "WHERE status = 'delivered' AND payment_method = 'full_card'"
    )
    card_revenue = card_rev_rows[0]["total"]

    # 2. Wallet top-ups: money came in when user topped up their wallet
    #    (wallet purchases just move balance — the cash arrived at top-up time)
    wallet_rev_rows = await db.execute_fetchall(
        "SELECT COALESCE(SUM(amount_approved), 0) as total FROM wallet_topups WHERE status = 'approved'"
    )
    wallet_revenue = wallet_rev_rows[0]["total"]

    total_revenue = card_revenue + wallet_revenue

    # Gifts given — completed redemptions from the gifts system (separate from sales)
    gifts_rows = await db.execute_fetchall(
        "SELECT COUNT(*) as cnt FROM redemptions WHERE status IN ('completed', 'approved')"
    )
    gifts_given = gifts_rows[0]["cnt"]

    # User count
    user_count = await user_service.get_users_count()

    # Stock
    stock_summary = await account_service.get_stock_summary()
    total_available = sum(s.get("available", 0) or 0 for s in stock_summary)
    total_sold = sum(s.get("sold", 0) or 0 for s in stock_summary)

    # Low stock warnings
    threshold_val = await settings_service.get_setting("low_stock_threshold")
    threshold = int(threshold_val) if threshold_val else 5
    low_stock = [s for s in stock_summary if (s.get("available", 0) or 0) < threshold]

    # Referral stats
    ref_rows = await db.execute_fetchall(
        "SELECT COUNT(*) as cnt, COALESCE(SUM(reward_uzs), 0) as total FROM referrals WHERE status = 'credited'"
    )
    referral_count = ref_rows[0]["cnt"]
    referral_total = ref_rows[0]["total"]

    # Alerts
    alert_rows = await db.execute_fetchall(
        "SELECT COUNT(*) as cnt FROM system_alerts WHERE status = 'new'"
    )
    alerts_count = alert_rows[0]["cnt"]

    # Pending redemptions count
    pending_redemptions_count = await rewards_service.get_redemptions_count(status="pending")

    # Pending wallet topups count
    topup_rows = await db.execute_fetchall(
        "SELECT COUNT(*) as cnt FROM wallet_topups WHERE status = 'pending'"
    )
    pending_topups_count = topup_rows[0]["cnt"]

    # Recent orders — only delivered (real sales), gifts are invisible here
    recent_orders = await order_service.get_all_orders(status="delivered", limit=10, offset=0)

    # Pending orders list
    pending_list = await order_service.get_all_orders(status="payment_submitted", limit=20)

    return {
        "total_orders": total_orders,        # delivered paid orders only, no gifts
        "pending_orders": pending_orders,
        "rejected_orders": rejected_orders,
        "total_revenue": total_revenue,       # card_revenue + wallet_revenue (real cash only)
        "card_revenue": card_revenue,         # revenue from full_card delivered orders
        "wallet_revenue": wallet_revenue,     # revenue from approved wallet top-ups
        "gifts_given": gifts_given,           # completed gift redemptions (separate system)
        "user_count": user_count,
        "total_available_stock": total_available,
        "total_sold_stock": total_sold,
        "low_stock_warnings": low_stock,
        "referral_count": referral_count,
        "referral_total_paid": referral_total,
        "alerts_count": alerts_count,
        "pending_redemptions_count": pending_redemptions_count,
        "pending_topups_count": pending_topups_count,
        "recent_orders": recent_orders,
        "pending_list": pending_list,
    }


# ─── ORDERS ──────────────────────────────────────────────────

@router.get("/orders")
async def list_orders(
    status: Optional[str] = None,
    payment_method: Optional[str] = None,
    platform_id: Optional[int] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: dict = Depends(get_current_admin),
):
    orders = await order_service.get_all_orders(
        status=status, payment_method=payment_method,
        platform_id=platform_id, limit=limit, offset=offset,
    )
    total = await order_service.get_orders_count(
        status=status, payment_method=payment_method, platform_id=platform_id
    )
    return {"orders": orders, "total": total, "limit": limit, "offset": offset}


@router.get("/orders/{order_id}")
async def get_order(order_id: int, admin: dict = Depends(get_current_admin)):
    order = await order_service.get_order_by_id(order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # Attach user info
    user = await user_service.get_user_by_id(order["user_id"])
    return {"order": order, "user": user}


@router.post("/orders/{order_id}/approve")
async def approve_order(order_id: int, admin: dict = Depends(get_current_admin)):
    """Approve order, assign account, notify user via Telegram."""
    try:
        order = await order_service.approve_order(order_id, admin["admin_id"])
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await audit_service.log_action(
        "admin", "order_approved", "order", order_id,
        admin_id=admin["admin_id"],
        meta={"public_id": order.get("public_order_id")},
    )

    # Send Telegram notification
    user = await user_service.get_user_by_id(order["user_id"])
    if user:
        try:
            from src.bot.bot import get_bot
            bot = get_bot()
            lang = user.get("language_code", "uz")
            if lang == "uz":
                msg = (
                    f"✅ Buyurtmangiz #{order['public_order_id']} tasdiqlandi!\n\n"
                    f"📦 {order.get('platform_name', '')} — {order.get('plan_name', '')}\n"
                    f"👤 Login: <code>{order.get('account_login', 'N/A')}</code>\n"
                    f"🔑 Parol: <code>{order.get('account_password', 'N/A')}</code>\n\n"
                    f"7 kun kafolat bilan. Muammo bo'lsa /support buyrug'ini yuboring."
                )
            else:
                msg = (
                    f"✅ Заказ #{order['public_order_id']} подтверждён!\n\n"
                    f"📦 {order.get('platform_name', '')} — {order.get('plan_name', '')}\n"
                    f"👤 Логин: <code>{order.get('account_login', 'N/A')}</code>\n"
                    f"🔑 Пароль: <code>{order.get('account_password', 'N/A')}</code>\n\n"
                    f"Гарантия 7 дней. При проблемах используйте /support."
                )
            await bot.send_message(chat_id=user["telegram_id"], text=msg)
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")

    return {"message": "Order approved", "order": order}


@router.post("/orders/{order_id}/reject")
async def reject_order(
    order_id: int,
    body: OrderAction = None,
    admin: dict = Depends(get_current_admin),
):
    """Reject order, restore balance, notify user via Telegram."""
    reason_code = body.reason_code if body else None
    note = body.note if body else None

    try:
        order = await order_service.reject_order(
            order_id, admin["admin_id"], reason_code=reason_code, note=note
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await audit_service.log_action(
        "admin", "order_rejected", "order", order_id,
        admin_id=admin["admin_id"],
        meta={"public_id": order.get("public_order_id"), "reason": reason_code, "note": note},
    )

    # Send Telegram notification
    user = await user_service.get_user_by_id(order["user_id"])
    if user:
        try:
            from src.bot.bot import get_bot
            bot = get_bot()
            lang = user.get("language_code", "uz")
            reason_text = note or reason_code or ""
            if lang == "uz":
                msg = (
                    f"❌ Buyurtmangiz #{order['public_order_id']} rad etildi.\n"
                )
                if reason_text:
                    msg += f"📝 Sabab: {reason_text}\n"
                msg += "\nIltimos, to'lov ma'lumotlarini tekshirib, qaytadan urinib ko'ring."
            else:
                msg = (
                    f"❌ Заказ #{order['public_order_id']} отклонён.\n"
                )
                if reason_text:
                    msg += f"📝 Причина: {reason_text}\n"
                msg += "\nПожалуйста, проверьте данные оплаты и попробуйте снова."
            await bot.send_message(chat_id=user["telegram_id"], text=msg)
        except Exception as e:
            logger.error(f"Failed to send Telegram notification: {e}")

    return {"message": "Order rejected", "order": order}


# ─── PLATFORMS ───────────────────────────────────────────────

@router.get("/platforms")
async def list_platforms(admin: dict = Depends(get_current_admin)):
    platforms = await catalog_service.get_all_platforms()
    return {"platforms": platforms}


@router.post("/platforms")
async def create_platform(body: PlatformCreate, admin: dict = Depends(get_current_admin)):
    platform = await catalog_service.create_platform(
        name=body.name, slug=body.slug, custom_emoji_code=body.custom_emoji_code,
        is_active=body.is_active, sort_order=body.sort_order,
    )
    await audit_service.log_action(
        "admin", "platform_created", "platform", platform["id"],
        admin_id=admin["admin_id"], meta={"name": body.name},
    )
    return {"platform": platform}


@router.put("/platforms/{platform_id}")
async def update_platform(
    platform_id: int,
    body: PlatformUpdate,
    admin: dict = Depends(get_current_admin),
):
    platform = await catalog_service.update_platform(
        platform_id, **body.model_dump(exclude_none=True)
    )
    if not platform:
        raise HTTPException(status_code=404, detail="Platform not found")
    await audit_service.log_action(
        "admin", "platform_updated", "platform", platform_id,
        admin_id=admin["admin_id"],
    )
    return {"platform": platform}


@router.delete("/platforms/{platform_id}")
async def delete_platform(platform_id: int, admin: dict = Depends(get_current_admin)):
    await catalog_service.delete_platform(platform_id)
    await audit_service.log_action(
        "admin", "platform_deleted", "platform", platform_id,
        admin_id=admin["admin_id"],
    )
    return {"message": "Platform deleted"}


# ─── PLANS ───────────────────────────────────────────────────

@router.get("/plans")
async def list_plans(
    platform_id: Optional[int] = None,
    admin: dict = Depends(get_current_admin),
):
    plans = await catalog_service.get_all_plans(platform_id=platform_id)
    return {"plans": plans}


@router.post("/plans")
async def create_plan(body: PlanCreate, admin: dict = Depends(get_current_admin)):
    plan = await catalog_service.create_plan(
        platform_id=body.platform_id, name=body.name, price_uzs=body.price_uzs,
        description_uz=body.description_uz, description_ru=body.description_ru,
        faq_uz=body.faq_uz, faq_ru=body.faq_ru,
        is_active=body.is_active, sort_order=body.sort_order,
        plan_type=body.plan_type
    )
    await audit_service.log_action(
        "admin", "plan_created", "plan", plan["id"],
        admin_id=admin["admin_id"], meta={"name": body.name},
    )
    return {"plan": plan}


@router.put("/plans/{plan_id}")
async def update_plan(
    plan_id: int,
    body: PlanUpdate,
    admin: dict = Depends(get_current_admin),
):
    plan = await catalog_service.update_plan(
        plan_id, **body.model_dump(exclude_none=True)
    )
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    await audit_service.log_action(
        "admin", "plan_updated", "plan", plan_id,
        admin_id=admin["admin_id"],
    )
    return {"plan": plan}


@router.delete("/plans/{plan_id}")
async def delete_plan(plan_id: int, admin: dict = Depends(get_current_admin)):
    try:
        await catalog_service.delete_plan(plan_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    await audit_service.log_action(
        "admin", "plan_deleted", "plan", plan_id,
        admin_id=admin["admin_id"],
    )
    return {"message": "Plan deleted"}


# ─── ACCOUNTS ────────────────────────────────────────────────

@router.get("/accounts")
async def list_accounts(
    plan_id: Optional[int] = None,
    status: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    admin: dict = Depends(get_current_admin),
):
    accounts = await account_service.get_accounts(
        plan_id=plan_id, status=status, limit=limit, offset=offset,
    )
    return {"accounts": accounts, "limit": limit, "offset": offset}


@router.post("/accounts")
async def add_account(body: AccountCreate, admin: dict = Depends(get_current_admin)):
    account = await account_service.add_account(
        plan_id=body.plan_id, login=body.login,
        password=body.password, notes=body.notes,
    )
    await audit_service.log_action(
        "admin", "account_added", "account", account["id"],
        admin_id=admin["admin_id"],
    )
    return {"account": account}


@router.post("/accounts/bulk")
async def bulk_add_accounts(body: AccountBulk, admin: dict = Depends(get_current_admin)):
    count = await account_service.bulk_add_accounts(body.plan_id, body.accounts)
    await audit_service.log_action(
        "admin", "accounts_bulk_added", "account", None,
        admin_id=admin["admin_id"], meta={"plan_id": body.plan_id, "count": count},
    )
    return {"message": f"Added {count} accounts", "count": count}


@router.put("/accounts/{account_id}")
async def update_account(
    account_id: int,
    body: AccountUpdate,
    admin: dict = Depends(get_current_admin),
):
    account = await account_service.update_account(
        account_id, **body.model_dump(exclude_none=True)
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    await audit_service.log_action(
        "admin", "account_updated", "account", account_id,
        admin_id=admin["admin_id"],
    )
    return {"account": account}


@router.get("/accounts/stock-summary")
async def stock_summary(admin: dict = Depends(get_current_admin)):
    summary = await account_service.get_stock_summary()
    return {"summary": summary}


# ─── USERS ───────────────────────────────────────────────────

@router.get("/users")
async def list_users(
    search: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: dict = Depends(get_current_admin),
):
    users = await user_service.get_all_users(limit=limit, offset=offset, search=search)
    total = await user_service.get_users_count(search=search)
    return {"users": users, "total": total, "limit": limit, "offset": offset}


@router.get("/users/{user_id}")
async def get_user(user_id: int, admin: dict = Depends(get_current_admin)):
    user = await user_service.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    referral_info = await referral_service.get_referral_info(user_id)
    return {"user": user, "referral_info": referral_info}


@router.get("/users/{user_id}/orders")
async def get_user_orders(user_id: int, admin: dict = Depends(get_current_admin)):
    orders = await order_service.get_user_orders(user_id)
    return {"orders": orders}


@router.get("/users/{user_id}/balance-transactions")
async def get_user_balance_transactions(
    user_id: int,
    limit: int = Query(50, ge=1, le=200),
    admin: dict = Depends(get_current_admin),
):
    transactions = await balance_service.get_transactions(user_id, limit=limit)
    return {"transactions": transactions}


@router.post("/users/{user_id}/adjust-balance")
async def adjust_user_balance(
    user_id: int,
    body: BalanceAdjustment,
    admin: dict = Depends(get_current_admin),
):
    """Adjust user balance manually."""
    try:
        new_balance = await wallet_service.add_wallet_balance(
            user_id=user_id,
            amount=body.amount,
            tx_type="manual_adjustment",
            description=body.comment or "Manual adjustment by admin",
        )
        await audit_service.log_action(
            actor_type="admin",
            action="balance_adjusted",
            entity_type="user",
            entity_id=user_id,
            admin_id=admin["admin_id"],
            meta={"amount": body.amount, "new_balance": new_balance},
        )
        return {"message": "Balance adjusted", "new_balance": new_balance}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/users/{user_id}/wallet-transactions")
async def get_user_wallet_transactions(
    user_id: int,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: dict = Depends(get_current_admin),
):
    transactions = await wallet_service.get_wallet_transactions(user_id, limit=limit, offset=offset)
    return {"transactions": transactions}


@router.get("/users/{user_id}/points-transactions")
async def get_user_points_transactions(
    user_id: int,
    limit: int = Query(50, ge=1, le=200),
    admin: dict = Depends(get_current_admin),
):
    transactions = await points_service.get_points_transactions(user_id, limit=limit)
    return {"transactions": transactions}


@router.post("/users/{user_id}/adjust-points")
async def adjust_user_points(
    user_id: int,
    body: PointsAdjustment,
    admin: dict = Depends(get_current_admin),
):
    """Adjust user points manually."""
    try:
        new_balance = await points_service.add_points(
            user_id=user_id,
            amount=body.amount,
            tx_type="manual_adjustment",
            description=body.description or "Manual adjustment by admin",
        )
        await audit_service.log_action(
            actor_type="admin",
            action="points_adjusted",
            entity_type="user",
            entity_id=user_id,
            admin_id=admin["admin_id"],
            meta={"amount": body.amount, "new_points": new_balance},
        )
        return {"message": "Points adjusted", "new_points": new_balance}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))



# ─── WALLET TOPUPS ───────────────────────────────────────────

@router.get("/wallet/topups")
async def list_wallet_topups(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: dict = Depends(get_current_admin),
):
    topups = await wallet_service.get_all_topups(status=status, limit=limit, offset=offset)
    # Get counts of pending
    db = await get_db()
    pending_rows = await db.execute_fetchall(
        "SELECT COUNT(*) as cnt FROM wallet_topups WHERE status = 'pending'"
    )
    pending_count = pending_rows[0]["cnt"]
    return {"topups": topups, "pending_count": pending_count}


@router.post("/wallet/topups/{topup_id}/process")
async def process_wallet_topup(
    topup_id: int,
    body: WalletTopupProcess,
    admin: dict = Depends(get_current_admin),
):
    try:
        topup = await wallet_service.process_topup(
            topup_id=topup_id,
            status=body.status,
            amount_approved=body.amount_approved,
            rejection_note=body.rejection_note,
            admin_id=admin["admin_id"],
        )
        
        # Notify user via Telegram Bot
        try:
            from src.bot.bot import get_bot
            bot = get_bot()
            lang = topup.get("language_code", "uz")
            
            if body.status == "approved":
                cur_bal = await wallet_service.get_wallet_balance(topup["user_id"])
                if lang == "uz":
                    msg = (
                        f"✅ <b>Hamyon to'ldirildi!</b>\n\n"
                        f"Sizning hamyonni to'ldirish so'rovingiz <code>#{topup['public_topup_id']}</code> tasdiqlandi.\n"
                        f"Hisobingizga <b>{body.amount_approved:,} UZS</b> qo'shildi.\n"
                        f"Joriy balansingiz: <b>{cur_bal:,} UZS</b>."
                    )
                else:
                    msg = (
                        f"✅ <b>Кошелек пополнен!</b>\n\n"
                        f"Ваш запрос на пополнение кошелька <code>#{topup['public_topup_id']}</code> одобрен.\n"
                        f"На ваш баланс зачислено <b>{body.amount_approved:,} UZS</b>.\n"
                        f"Текущий баланс: <b>{cur_bal:,} UZS</b>."
                    )
            else:
                reason = body.rejection_note or "—"
                if lang == "uz":
                    msg = (
                        f"❌ <b>Hamyonni to'ldirish so'rovi rad etildi</b>\n\n"
                        f"Sizning hamyonni to'ldirish so'rovingiz <code>#{topup['public_topup_id']}</code> rad etildi.\n"
                        f"📝 Sabab: <code>{reason}</code>"
                    )
                else:
                    msg = (
                        f"❌ <b>Запрос на пополнение кошелька отклонён</b>\n\n"
                        f"Ваш запрос на пополнение кошелька <code>#{topup['public_topup_id']}</code> отклонён.\n"
                        f"📝 Причина: <code>{reason}</code>"
                    )
            
            await bot.send_message(chat_id=topup["telegram_id"], text=msg, parse_mode="HTML")
        except Exception as e:
            logger.error(f"Failed to send top-up Telegram notification: {e}")

        # Log action
        await audit_service.log_action(
            actor_type="admin",
            action=f"wallet_topup_{body.status}",
            entity_type="wallet_topup",
            entity_id=topup_id,
            admin_id=admin["admin_id"],
            meta={"amount_requested": topup["amount_requested"], "amount_approved": body.amount_approved, "rejection_note": body.rejection_note},
        )
        return {"message": f"Top-up request processed: {body.status}", "topup": topup}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ─── REFERRALS ───────────────────────────────────────────────

@router.get("/referrals")
async def list_referrals(
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    admin: dict = Depends(get_current_admin),
):
    referrals = await referral_service.get_all_referrals(limit=limit, offset=offset)
    return {"referrals": referrals}


@router.get("/alerts")
async def list_alerts(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    admin: dict = Depends(get_current_admin),
):
    alerts = await referral_service.get_system_alerts(status=status, limit=limit)
    return {"alerts": alerts}


# ─── REWARDS ──────────────────────────────────────────────────

@router.get("/rewards")
async def list_rewards(admin: dict = Depends(get_current_admin)):
    rewards = await rewards_service.get_all_rewards()
    return {"rewards": rewards}


@router.post("/rewards")
async def create_reward(body: RewardCreate, admin: dict = Depends(get_current_admin)):
    reward = await rewards_service.create_reward(
        name=body.name,
        description_uz=body.description_uz,
        description_ru=body.description_ru,
        points_required=body.points_required,
        plan_id=body.plan_id,
        is_active=body.is_active,
    )
    await audit_service.log_action(
        actor_type="admin",
        action="reward_created",
        entity_type="reward",
        entity_id=reward["id"],
        admin_id=admin["admin_id"],
        meta={"name": body.name},
    )
    return {"reward": reward}


@router.put("/rewards/{reward_id}")
async def update_reward(
    reward_id: int,
    body: RewardUpdate,
    admin: dict = Depends(get_current_admin),
):
    reward = await rewards_service.update_reward(
        reward_id, **body.model_dump(exclude_unset=True)
    )
    if not reward:
        raise HTTPException(status_code=404, detail="Reward not found")
    await audit_service.log_action(
        actor_type="admin",
        action="reward_updated",
        entity_type="reward",
        entity_id=reward_id,
        admin_id=admin["admin_id"],
    )
    return {"reward": reward}


@router.delete("/rewards/{reward_id}")
async def delete_reward(reward_id: int, admin: dict = Depends(get_current_admin)):
    await rewards_service.delete_reward(reward_id)
    await audit_service.log_action(
        actor_type="admin",
        action="reward_deleted",
        entity_type="reward",
        entity_id=reward_id,
        admin_id=admin["admin_id"],
    )
    return {"message": "Reward deleted"}


# ─── REDEMPTIONS ──────────────────────────────────────────────

@router.get("/redemptions")
async def list_redemptions(
    status: Optional[str] = None,
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    admin: dict = Depends(get_current_admin),
):
    redemptions = await rewards_service.get_all_redemptions(status=status, limit=limit, offset=offset)
    total = await rewards_service.get_redemptions_count(status=status)
    return {"redemptions": redemptions, "total": total, "limit": limit, "offset": offset}


@router.post("/redemptions/{redemption_id}/process")
async def process_redemption(
    redemption_id: int,
    body: RedemptionProcess,
    admin: dict = Depends(get_current_admin),
):
    try:
        redemption = await rewards_service.process_redemption(
            redemption_id=redemption_id,
            status=body.status,
            admin_id=admin["admin_id"],
            rejection_note=body.rejection_note,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    await audit_service.log_action(
        actor_type="admin",
        action=f"redemption_{body.status}",
        entity_type="redemption",
        entity_id=redemption_id,
        admin_id=admin["admin_id"],
        meta={"public_id": redemption.get("public_redemption_id"), "rejection_note": body.rejection_note},
    )

    # Notify Telegram user
    user = await user_service.get_user_by_id(redemption["user_id"])
    if user:
        try:
            from src.bot.bot import get_bot
            bot = get_bot()
            lang = user.get("language_code", "uz")
            public_id = redemption["public_redemption_id"]
            reward_name = redemption.get("reward_name", "")

            if body.status == "approved":
                if lang == "uz":
                    msg = (
                        f"🎉 <b>Tabriklaymiz!</b>\n\n"
                        f"Sizning sovg'a <b>{reward_name}</b> uchun so'rovingiz <code>#{public_id}</code> tasdiqlandi.\n"
                        f"Tez orada adminlar siz bilan bog'lanishadi yoki sovg'ani yetkazishadi!"
                    )
                else:
                    msg = (
                        f"🎉 <b>Поздравляем!</b>\n\n"
                        f"Ваш запрос на подарок <b>{reward_name}</b> <code>#{public_id}</code> одобрен.\n"
                        f"Скоро администраторы свяжутся с вами или доставят подарок!"
                    )
            elif body.status == "rejected":
                reason = body.rejection_note or "—"
                points_returned = redemption["points_spent"]
                if lang == "uz":
                    msg = (
                        f"❌ <b>Sovg'a so'rovi rad etildi</b>\n\n"
                        f"Sizning sovg'a <b>{reward_name}</b> uchun so'rovingiz <code>#{public_id}</code> rad etildi.\n"
                        f"📝 Sabab: <code>{reason}</code>\n"
                        f"🔄 <b>{points_returned} ball</b> balansingizga qaytarildi."
                    )
                else:
                    msg = (
                        f"❌ <b>Запрос на подарок отклонён</b>\n\n"
                        f"Ваш запрос на подарок <b>{reward_name}</b> <code>#{public_id}</code> отклонён.\n"
                        f"📝 Причина: <code>{reason}</code>\n"
                        f"🔄 <b>{points_returned} баллов</b> возвращено на ваш баланс."
                    )
            elif body.status == "completed":
                if lang == "uz":
                    msg = (
                        f"🎁 <b>Sovg'a topshirildi!</b>\n\n"
                        f"Sizning sovg'a <b>{reward_name}</b> uchun so'rovingiz <code>#{public_id}</code> muvaffaqiyatli yakunlandi.\n"
                        f"Bizni tanlaganingiz uchun rahmat!"
                    )
                else:
                    msg = (
                        f"🎁 <b>Подарок вручен!</b>\n\n"
                        f"Ваш запрос на подарок <b>{reward_name}</b> <code>#{public_id}</code> успешно завершен.\n"
                        f"Спасибо, что вы с нами!"
                    )
            else:
                msg = None

            if msg:
                await bot.send_message(chat_id=user["telegram_id"], text=msg)
        except Exception as e:
            logger.error(f"Failed to send redemption Telegram notification: {e}")

    return {"message": f"Redemption status updated to {body.status}", "redemption": redemption}


# ─── SETTINGS ────────────────────────────────────────────────

@router.get("/settings")
async def get_settings(admin: dict = Depends(get_current_admin)):
    settings = await settings_service.get_all_settings()
    return {"settings": settings}


@router.put("/settings")
async def update_settings(body: SettingsUpdate, admin: dict = Depends(get_current_admin)):
    await settings_service.update_settings(body.settings)
    await audit_service.log_action(
        "admin", "settings_updated", "settings", None,
        admin_id=admin["admin_id"],
        meta={"keys": list(body.settings.keys())},
    )
    return {"message": "Settings updated"}


# ─── AUDIT LOGS ──────────────────────────────────────────────

@router.get("/audit-logs")
async def list_audit_logs(
    entity_type: Optional[str] = None,
    action: Optional[str] = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0),
    admin: dict = Depends(get_current_admin),
):
    logs = await audit_service.get_audit_logs(
        limit=limit, offset=offset,
        entity_type=entity_type, action=action,
    )
    return {"logs": logs}


# ─── REPORTS ─────────────────────────────────────────────────

@router.get("/reports/orders")
async def report_orders(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    admin: dict = Depends(get_current_admin),
):
    """Order stats with optional date range filter."""
    db = await get_db()
    date_filter = ""
    params = []
    if start_date:
        date_filter += " AND o.created_at >= ?"
        params.append(start_date)
    if end_date:
        date_filter += " AND o.created_at <= ?"
        params.append(end_date + " 23:59:59")

    # Orders by status
    rows = await db.execute_fetchall(
        f"SELECT status, COUNT(*) as count FROM orders o WHERE 1=1 {date_filter} GROUP BY status",
        params,
    )
    by_status = {r["status"]: r["count"] for r in rows}

    # Orders by payment method
    rows = await db.execute_fetchall(
        f"SELECT payment_method, COUNT(*) as count FROM orders o WHERE 1=1 {date_filter} GROUP BY payment_method",
        params,
    )
    by_payment = {r["payment_method"]: r["count"] for r in rows}

    # Orders over time (daily)
    rows = await db.execute_fetchall(
        f"""SELECT DATE(o.created_at) as date, COUNT(*) as count
            FROM orders o WHERE 1=1 {date_filter}
            GROUP BY DATE(o.created_at) ORDER BY date""",
        params,
    )
    over_time = [{"date": r["date"], "count": r["count"]} for r in rows]

    # Top platforms
    rows = await db.execute_fetchall(
        f"""SELECT pl.name as platform, COUNT(*) as count
            FROM orders o JOIN platforms pl ON o.platform_id = pl.id
            WHERE 1=1 {date_filter}
            GROUP BY o.platform_id ORDER BY count DESC LIMIT 10""",
        params,
    )
    top_platforms = [{"platform": r["platform"], "count": r["count"]} for r in rows]

    return {
        "by_status": by_status,
        "by_payment_method": by_payment,
        "over_time": over_time,
        "top_platforms": top_platforms,
    }


@router.get("/reports/revenue")
async def report_revenue(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    admin: dict = Depends(get_current_admin),
):
    """Revenue stats with optional date range filter."""
    db = await get_db()
    date_filter = ""
    params = []
    if start_date:
        date_filter += " AND o.created_at >= ?"
        params.append(start_date)
    if end_date:
        date_filter += " AND o.created_at <= ?"
        params.append(end_date + " 23:59:59")

    # Total revenue
    rows = await db.execute_fetchall(
        f"SELECT COALESCE(SUM(price_original_uzs), 0) as total FROM orders o WHERE status = 'delivered' {date_filter}",
        params,
    )
    total_revenue = rows[0]["total"]

    # Revenue over time (daily)
    rows = await db.execute_fetchall(
        f"""SELECT DATE(o.created_at) as date, SUM(price_original_uzs) as revenue, COUNT(*) as orders
            FROM orders o WHERE o.status = 'delivered' {date_filter}
            GROUP BY DATE(o.created_at) ORDER BY date""",
        params,
    )
    over_time = [{"date": r["date"], "revenue": r["revenue"], "orders": r["orders"]} for r in rows]

    # Revenue by platform
    rows = await db.execute_fetchall(
        f"""SELECT pl.name as platform, SUM(o.price_original_uzs) as revenue
            FROM orders o JOIN platforms pl ON o.platform_id = pl.id
            WHERE o.status = 'delivered' {date_filter}
            GROUP BY o.platform_id ORDER BY revenue DESC""",
        params,
    )
    by_platform = [{"platform": r["platform"], "revenue": r["revenue"]} for r in rows]

    # Order count (delivered)
    delivered_count_rows = await db.execute_fetchall(
        f"SELECT COUNT(*) as cnt FROM orders o WHERE status = 'delivered' {date_filter}",
        params,
    )
    delivered_count = delivered_count_rows[0]["cnt"]

    avg_order_value = total_revenue // delivered_count if delivered_count > 0 else 0

    return {
        "total_revenue": total_revenue,
        "delivered_count": delivered_count,
        "avg_order_value": avg_order_value,
        "over_time": over_time,
        "by_platform": by_platform,
    }


@router.get("/reports/referrals")
async def report_referrals(admin: dict = Depends(get_current_admin)):
    """Referral stats."""
    db = await get_db()

    # Total referrals
    rows = await db.execute_fetchall(
        """SELECT COUNT(*) as total, SUM(CASE WHEN status = 'credited' THEN 1 ELSE 0 END) as credited,
           SUM(CASE WHEN status = 'flagged' THEN 1 ELSE 0 END) as flagged,
           COALESCE(SUM(CASE WHEN status = 'credited' THEN reward_uzs ELSE 0 END), 0) as total_paid
           FROM referrals"""
    )
    stats = dict(rows[0])
    
    # Points total paid
    points_rows = await db.execute_fetchall(
        "SELECT COALESCE(SUM(points), 0) as total FROM points_transactions WHERE type = 'referral'"
    )
    stats["total_points_paid"] = points_rows[0]["total"]

    # Referrals over time
    rows = await db.execute_fetchall(
        """SELECT DATE(created_at) as date, COUNT(*) as count
           FROM referrals GROUP BY DATE(created_at) ORDER BY date DESC LIMIT 30"""
    )
    over_time = [{"date": r["date"], "count": r["count"]} for r in rows]

    # Top inviters
    rows = await db.execute_fetchall(
        """SELECT u.telegram_username, u.first_name, u.telegram_id, u.id as user_id,
           COUNT(r.id) as invited_count, COALESCE(SUM(r.reward_uzs), 0) as total_earned
           FROM referrals r JOIN users u ON r.inviter_user_id = u.id
           WHERE r.status = 'credited'
           GROUP BY r.inviter_user_id ORDER BY invited_count DESC LIMIT 10"""
    )
    top_inviters = []
    for r in rows:
        d = dict(r)
        # Query total points earned by this user via referrals
        p_rows = await db.execute_fetchall(
            "SELECT COALESCE(SUM(points), 0) as total FROM points_transactions WHERE user_id = ? AND type = 'referral'",
            (d["user_id"],)
        )
        d["total_points_earned"] = p_rows[0]["total"]
        top_inviters.append(d)

    return {
        "stats": stats,
        "over_time": over_time,
        "top_inviters": top_inviters,
    }

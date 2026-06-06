"""Handler: full purchase flow — payment method, order creation, screenshot handling."""
import logging
import uuid
from pathlib import Path
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message

from src.config import ADMIN_CHAT_ID, UPLOAD_DIR
from src.services import (
    user_service,
    catalog_service,
    order_service,
    wallet_service,
    audit_service,
)
from src.bot.texts import get_text, format_price, TEXTS, format_emoji_for_message
from src.bot import keyboards
from src.bot.bot import get_bot

logger = logging.getLogger("subhub.bot.purchase")
router = Router(name="purchase")


async def _get_user_and_lang(telegram_id: int) -> tuple[dict | None, str]:
    """Get user dict and language."""
    user = await user_service.get_user_by_telegram_id(telegram_id)
    lang = user.get("language_code", "uz") if user else "uz"
    return user, lang


# ── Payment Method Selection ──────────────────────────────────


@router.callback_query(F.data.startswith("buy:"))
async def show_payment_methods(callback: CallbackQuery) -> None:
    """Show payment method selection for a plan."""
    await callback.answer()
    user, lang = await _get_user_and_lang(callback.from_user.id)
    if not user:
        return

    try:
        plan_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.message.edit_text(
            get_text("error_generic", lang),
            reply_markup=keyboards.back_to_menu(lang),
        )
        return

    try:
        # Check for existing unpaid order
        existing = await order_service.get_active_unpaid_order(user["id"])
        if existing:
            text = get_text("existing_order_warning", lang).format(
                order_id=existing["public_order_id"]
            )
            try:
                await callback.message.edit_text(
                    text,
                    reply_markup=keyboards.cancel_order(existing["id"], lang),
                )
            except Exception:
                await callback.message.answer(
                    text,
                    reply_markup=keyboards.cancel_order(existing["id"], lang),
                )
            return

        plan = await catalog_service.get_plan_by_id(plan_id)
        if not plan:
            await callback.message.edit_text(
                get_text("error_not_found", lang),
                reply_markup=keyboards.back_to_menu(lang),
            )
            return

        # Guard: if it's contact admin type, do not allow payment flow, show detail instead
        if plan.get("plan_type") == "contact_admin":
            from src.bot.handlers.products import get_support_username
            support_username = await get_support_username()
            stock = plan.get("stock", 0)
            description = plan.get(f"description_{lang}") or plan.get("description_ru", "")
            emoji_str = format_emoji_for_message(plan.get("platform_emoji_code"))
            platform_name = f"{emoji_str} {plan['platform_name']}".strip() if emoji_str else plan["platform_name"]
            
            text = get_text("plan_detail_contact_admin", lang).format(
                platform=platform_name,
                plan=plan["name"],
                stock=stock,
                description=description,
            )
            faq = plan.get(f"faq_{lang}") or plan.get("faq_ru", "")
            if faq:
                text += get_text("plan_detail_faq", lang).format(faq=faq)
                
            kb = keyboards.plan_detail(
                plan_id=plan_id,
                platform_id=plan["platform_id"],
                has_stock=stock > 0,
                lang=lang,
                plan_type="contact_admin",
                admin_username=support_username,
            )
            await callback.message.edit_text(text, reply_markup=kb)
            return

        stock = plan.get("stock", 0)
        if stock <= 0:
            await callback.message.edit_text(
                get_text("error_no_stock", lang),
                reply_markup=keyboards.back_to_menu(lang),
            )
            return

        balance = await wallet_service.get_wallet_balance(user["id"])
        price = plan["price_uzs"]

        emoji_str = format_emoji_for_message(plan.get("platform_emoji_code"))
        platform_name = f"{emoji_str} {plan['platform_name']}".strip() if emoji_str else plan["platform_name"]

        text = get_text("payment_method_title", lang).format(
            platform=platform_name,
            plan=plan["name"],
            price=format_price(price),
        )

        if balance > 0:
            text += get_text("payment_method_balance_info", lang).format(
                balance=format_price(balance)
            )

        try:
            await callback.message.edit_text(
                text,
                reply_markup=keyboards.payment_methods(balance, price, plan_id, lang),
            )
        except Exception:
            await callback.message.answer(
                text,
                reply_markup=keyboards.payment_methods(balance, price, plan_id, lang),
            )
    except Exception as e:
        logger.error(f"Error showing payment methods: {e}")
        await callback.message.edit_text(
            get_text("error_generic", lang),
            reply_markup=keyboards.back_to_menu(lang),
        )


# ── Order Creation ────────────────────────────────────────────


@router.callback_query(F.data.startswith("pay:"))
async def process_payment(callback: CallbackQuery) -> None:
    """Handle payment method selection and create order."""
    await callback.answer()
    user, lang = await _get_user_and_lang(callback.from_user.id)
    if not user:
        return

    try:
        parts = callback.data.split(":")
        method = parts[1]       # full_card, balance, hybrid
        plan_id = int(parts[2])
    except (ValueError, IndexError):
        await callback.message.edit_text(
            get_text("error_generic", lang),
            reply_markup=keyboards.back_to_menu(lang),
        )
        return

    try:
        # Re-check for existing order
        existing = await order_service.get_active_unpaid_order(user["id"])
        if existing:
            text = get_text("existing_order_warning", lang).format(
                order_id=existing["public_order_id"]
            )
            await callback.message.edit_text(
                text,
                reply_markup=keyboards.cancel_order(existing["id"], lang),
            )
            return

        plan = await catalog_service.get_plan_by_id(plan_id)
        if not plan:
            await callback.message.edit_text(
                get_text("error_not_found", lang),
                reply_markup=keyboards.back_to_menu(lang),
            )
            return

        stock = plan.get("stock", 0)
        if stock <= 0:
            await callback.message.edit_text(
                get_text("error_no_stock", lang),
                reply_markup=keyboards.back_to_menu(lang),
            )
            return

        price = plan["price_uzs"]
        balance = await wallet_service.get_wallet_balance(user["id"])
        balance_used = 0
        card_due = price

        if method == "wallet":
            if balance < price:
                await callback.message.edit_text(
                    get_text("payment_method_wallet_insufficient", lang).format(
                        price=format_price(price),
                        balance=format_price(balance)
                    ),
                    reply_markup=keyboards.back_to_wallet(lang),
                )
                return
            balance_used = price
            card_due = 0
            method_db = "balance"
        elif method == "full_card":
            balance_used = 0
            card_due = price
            method_db = "full_card"
        else:
            await callback.message.edit_text(
                get_text("error_generic", lang),
                reply_markup=keyboards.back_to_menu(lang),
            )
            return

        # Create order
        order = await order_service.create_order(
            user_id=user["id"],
            platform_id=plan["platform_id"],
            plan_id=plan_id,
            payment_method=method_db,
            price=price,
            balance_used=balance_used,
            card_due=card_due,
        )

        await audit_service.log_action(
            actor_type="user",
            action="order_created",
            entity_type="order",
            entity_id=order["id"],
            meta={
                "telegram_id": callback.from_user.id,
                "method": method_db,
                "price": price,
                "balance_used": balance_used,
            },
        )

        if method_db == "balance":
            # Auto-deliver immediately
            try:
                delivered = await order_service.auto_deliver_order(order["id"])
                text = get_text("order_auto_delivered", lang).format(
                    order_id=delivered["public_order_id"],
                    platform=plan["platform_name"],
                    plan=plan["name"],
                    price=format_price(price),
                    login=delivered.get("account_login", "N/A"),
                    password=delivered.get("account_password", "N/A"),
                )
                try:
                    await callback.message.edit_text(
                        text, reply_markup=keyboards.back_to_menu(lang)
                    )
                except Exception:
                    await callback.message.answer(
                        text, reply_markup=keyboards.back_to_menu(lang)
                    )
            except ValueError as e:
                logger.error(f"Auto-delivery failed: {e}")
                # Notify admin about the out-of-stock situation
                try:
                    bot = get_bot()
                    from src.config import ADMIN_CHAT_ID
                    if ADMIN_CHAT_ID:
                        user_name = user.get("first_name") or user.get("telegram_username") or "Unknown"
                        admin_msg = (
                            f"⚠️ <b>Wallet order failed — no stock</b>\n\n"
                            f"🆔 Order: <b>#{order['public_order_id']}</b>\n"
                            f"👤 User: {user_name} (ID: {user['telegram_id']})\n"
                            f"📦 {plan['platform_name']} — {plan['name']}\n"
                            f"💰 Amount: <b>{format_price(price)} UZS</b> (refunded to wallet)\n\n"
                            f"No accounts available. Balance was refunded. Please restock."
                        )
                        await bot.send_message(ADMIN_CHAT_ID, admin_msg, parse_mode="HTML")
                except Exception as notify_err:
                    logger.error(f"Failed to notify admin of out-of-stock: {notify_err}")
                # Show user a polite message — do NOT expose the stock error
                out_of_stock_msg = (
                    "😔 Afsuski, hozirda akkountlar vaqtincha tugagan. Hamyoningizga to'liq summa qaytarildi. "
                    "Tez orada adminlar siz bilan bog'lanadi yoki keyinroq qayta urinib ko'ring."
                    if lang == "uz" else
                    "😔 К сожалению, аккаунты временно закончились. Полная сумма возвращена на ваш кошелек. "
                    "Администраторы скоро свяжутся с вами, или попробуйте позже."
                )
                try:
                    await callback.message.edit_text(
                        out_of_stock_msg, reply_markup=keyboards.back_to_menu(lang)
                    )
                except Exception:
                    await callback.message.answer(
                        out_of_stock_msg, reply_markup=keyboards.back_to_menu(lang)
                    )
        else:
            # Card — show payment instructions
            await _show_payment_instructions(callback, order, plan, lang, method_db, balance_used, card_due)

    except Exception as e:
        logger.error(f"Error processing payment: {e}", exc_info=True)
        await callback.message.edit_text(
            get_text("error_generic", lang),
            reply_markup=keyboards.back_to_menu(lang),
        )


async def _show_payment_instructions(
    callback: CallbackQuery,
    order: dict,
    plan: dict,
    lang: str,
    method: str,
    balance_used: int,
    card_due: int,
) -> None:
    """Show payment instructions and screenshot prompt."""
    from src.services import settings_service

    # Build header
    amount = card_due if method == "hybrid" else order["price_original_uzs"]
    emoji_str = format_emoji_for_message(plan.get("platform_emoji_code"))
    platform_name = f"{emoji_str} {plan['platform_name']}".strip() if emoji_str else plan["platform_name"]

    text = get_text("payment_instructions_header", lang).format(
        order_id=order["public_order_id"],
        platform=platform_name,
        plan=plan["name"],
        amount=format_price(amount),
    )

    if method == "hybrid":
        text += get_text("payment_hybrid_note", lang).format(
            balance_used=format_price(balance_used),
            card_due=format_price(card_due),
        )

    # Add payment instructions from settings
    instructions = await settings_service.get_text("payment_instructions", lang)
    if instructions:
        text += instructions + "\n\n"

    text += get_text("screenshot_prompt", lang)

    try:
        await callback.message.edit_text(
            text,
            reply_markup=keyboards.cancel_order(order["id"], lang),
        )
    except Exception:
        await callback.message.answer(
            text,
            reply_markup=keyboards.cancel_order(order["id"], lang),
        )


# ── Screenshot Handling ───────────────────────────────────────


@router.message(F.photo)
async def handle_photo_screenshot(message: Message) -> None:
    """Handle photo uploads — check if user has an active pending_payment order."""
    user, lang = await _get_user_and_lang(message.from_user.id)
    if not user:
        return

    try:
        active_order = await order_service.get_active_unpaid_order(user["id"])
        if not active_order or active_order["status"] not in ("pending_payment",):
            await message.answer(
                get_text("screenshot_no_order", lang),
                reply_markup=keyboards.back_to_menu(lang),
            )
            return

        # Get the highest resolution photo
        photo = message.photo[-1]
        file_id = photo.file_id

        # Download and save screenshot locally
        bot = get_bot()
        file = await bot.get_file(file_id)
        
        ext = file.file_path.split('.')[-1] if file.file_path and '.' in file.file_path else 'jpg'
        filename = f"{active_order['id']}_{uuid.uuid4().hex[:8]}.{ext}"
        
        local_dir = UPLOAD_DIR
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = local_dir / filename
        
        await bot.download(file, destination=local_path)
        db_screenshot_path = f"uploads/screenshots/{filename}"

        await order_service.save_screenshot(
            order_id=active_order["id"],
            file_id=file_id,
            file_path=db_screenshot_path,
        )

        await audit_service.log_action(
            actor_type="user",
            action="screenshot_uploaded",
            entity_type="order",
            entity_id=active_order["id"],
            meta={"telegram_id": message.from_user.id, "file_id": file_id},
        )

        # Confirm to user
        # Re-fetch order to get public_order_id
        order = await order_service.get_order_by_id(active_order["id"])
        public_id = order["public_order_id"] if order else active_order.get("public_order_id", "?")

        await message.answer(
            get_text("screenshot_received", lang).format(order_id=public_id),
            reply_markup=keyboards.back_to_menu(lang),
        )

        # Notify admin
        await _notify_admin_screenshot(message, order or active_order, user)

    except Exception as e:
        logger.error(f"Error handling screenshot: {e}", exc_info=True)
        await message.answer(
            get_text("error_generic", lang),
            reply_markup=keyboards.back_to_menu(lang),
        )


@router.message(F.document)
async def handle_document_screenshot(message: Message) -> None:
    """Handle document uploads as screenshots (images sent as files)."""
    user, lang = await _get_user_and_lang(message.from_user.id)
    if not user:
        return

    try:
        active_order = await order_service.get_active_unpaid_order(user["id"])
        if not active_order or active_order["status"] not in ("pending_payment",):
            await message.answer(
                get_text("screenshot_no_order", lang),
                reply_markup=keyboards.back_to_menu(lang),
            )
            return

        # Verify it's an image document
        if message.document.mime_type and not message.document.mime_type.startswith("image/"):
            await message.answer(
                get_text("screenshot_no_order", lang),
                reply_markup=keyboards.back_to_menu(lang),
            )
            return

        file_id = message.document.file_id
        bot = get_bot()
        file = await bot.get_file(file_id)
        
        ext = file.file_path.split('.')[-1] if file.file_path and '.' in file.file_path else 'jpg'
        filename = f"{active_order['id']}_{uuid.uuid4().hex[:8]}.{ext}"
        
        local_dir = UPLOAD_DIR
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = local_dir / filename
        
        await bot.download(file, destination=local_path)
        db_screenshot_path = f"uploads/screenshots/{filename}"

        await order_service.save_screenshot(
            order_id=active_order["id"],
            file_id=file_id,
            file_path=db_screenshot_path,
        )

        await audit_service.log_action(
            actor_type="user",
            action="screenshot_uploaded",
            entity_type="order",
            entity_id=active_order["id"],
            meta={"telegram_id": message.from_user.id, "file_id": file_id},
        )

        order = await order_service.get_order_by_id(active_order["id"])
        public_id = order["public_order_id"] if order else active_order.get("public_order_id", "?")

        await message.answer(
            get_text("screenshot_received", lang).format(order_id=public_id),
            reply_markup=keyboards.back_to_menu(lang),
        )

        await _notify_admin_screenshot(message, order or active_order, user)

    except Exception as e:
        logger.error(f"Error handling document screenshot: {e}", exc_info=True)
        await message.answer(
            get_text("error_generic", lang),
            reply_markup=keyboards.back_to_menu(lang),
        )


async def _notify_admin_screenshot(message: Message, order: dict, user: dict) -> None:
    """Send admin notification about a new payment screenshot."""
    if not ADMIN_CHAT_ID:
        logger.warning("ADMIN_CHAT_ID not configured, skipping admin notification")
        return

    bot = get_bot()

    user_name = user.get("first_name") or user.get("telegram_username") or "Unknown"
    method_labels = {"full_card": "💳 Karta", "hybrid": "💳+💰 Aralash", "balance": "💰 Balans"}
    method_label = method_labels.get(order.get("payment_method", ""), order.get("payment_method", "?"))

    # Determine amount
    if order.get("payment_method") == "hybrid":
        amount = format_price(order.get("card_due_uzs", 0))
    else:
        amount = format_price(order.get("price_original_uzs", 0))

    text = TEXTS["admin_new_screenshot"].format(
        order_id=order.get("public_order_id", "?"),
        db_id=order.get("id", "?"),
        user_name=user_name,
        telegram_id=user.get("telegram_id", "?"),
        platform=order.get("platform_name", "?"),
        plan=order.get("plan_name", "?"),
        amount=amount,
        method=method_label,
    )

    try:
        # Forward the screenshot photo to admin
        file_id = order.get("payment_screenshot_file_id")
        if file_id:
            await bot.send_photo(ADMIN_CHAT_ID, photo=file_id, caption=text)
        else:
            await bot.send_message(ADMIN_CHAT_ID, text)
    except Exception as e:
        logger.error(f"Failed to notify admin: {e}")

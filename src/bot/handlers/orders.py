"""Handler: order history and cancellation."""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery

from src.services import user_service, order_service, audit_service
from src.bot.texts import get_text, format_price, get_status_text, TEXTS
from src.bot import keyboards
from src.bot.bot import get_bot
from src.config import ADMIN_CHAT_ID

logger = logging.getLogger("subhub.bot.orders")
router = Router(name="orders")


async def _get_user_and_lang(telegram_id: int) -> tuple[dict | None, str]:
    """Get user dict and language."""
    user = await user_service.get_user_by_telegram_id(telegram_id)
    lang = user.get("language_code", "uz") if user else "uz"
    return user, lang


@router.callback_query(F.data == "menu:orders")
async def show_orders(callback: CallbackQuery) -> None:
    """Show all user orders in a single message."""
    await callback.answer()
    user, lang = await _get_user_and_lang(callback.from_user.id)
    if not user:
        return

    try:
        orders = await order_service.get_user_orders(user["id"])
        if not orders:
            try:
                await callback.message.edit_text(
                    get_text("no_orders", lang),
                    reply_markup=keyboards.back_to_menu(lang),
                )
            except Exception:
                await callback.message.answer(
                    get_text("no_orders", lang),
                    reply_markup=keyboards.back_to_menu(lang),
                )
            return

        text = get_text("orders_title", lang)

        for order in orders:
            # Format the date
            created = order.get("created_at", "")
            if created:
                # Parse and format: "2026-01-15 12:30:00" -> "15.01.2026 12:30"
                try:
                    from datetime import datetime
                    dt = datetime.fromisoformat(created)
                    date_str = dt.strftime("%d.%m.%Y %H:%M")
                except (ValueError, TypeError):
                    date_str = str(created)[:16]
            else:
                date_str = "—"

            text += get_text("order_item", lang).format(
                order_id=order["public_order_id"],
                platform=order.get("platform_name", "?"),
                plan=order.get("plan_name", "?"),
                price=format_price(order["price_original_uzs"]),
                date=date_str,
                status=get_status_text(order["status"], lang),
            )

            # Show credentials for delivered orders
            if order["status"] == "delivered" and order.get("account_login"):
                text += get_text("order_item_credentials", lang).format(
                    login=order["account_login"],
                    password=order.get("account_password", ""),
                )

        kb = keyboards.order_list_keyboard(orders, lang)

        try:
            await callback.message.edit_text(text, reply_markup=kb)
        except Exception:
            await callback.message.answer(text, reply_markup=kb)

    except Exception as e:
        logger.error(f"Error loading orders: {e}", exc_info=True)
        try:
            await callback.message.edit_text(
                get_text("error_generic", lang),
                reply_markup=keyboards.back_to_menu(lang),
            )
        except Exception:
            await callback.message.answer(
                get_text("error_generic", lang),
                reply_markup=keyboards.back_to_menu(lang),
            )


@router.callback_query(F.data.startswith("cancel_order:"))
async def cancel_order(callback: CallbackQuery) -> None:
    """Cancel an order by its internal ID."""
    await callback.answer()
    user, lang = await _get_user_and_lang(callback.from_user.id)
    if not user:
        return

    try:
        order_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.message.edit_text(
            get_text("error_generic", lang),
            reply_markup=keyboards.back_to_menu(lang),
        )
        return

    try:
        # Verify the order belongs to this user
        order = await order_service.get_order_by_id(order_id)
        if not order or order["user_id"] != user["id"]:
            await callback.message.edit_text(
                get_text("error_not_found", lang),
                reply_markup=keyboards.back_to_menu(lang),
            )
            return

        cancelled = await order_service.cancel_order(order_id)

        await audit_service.log_action(
            actor_type="user",
            action="order_cancelled",
            entity_type="order",
            entity_id=order_id,
            meta={"telegram_id": callback.from_user.id},
        )

        text = get_text("order_cancelled", lang).format(
            order_id=cancelled["public_order_id"]
        )

        try:
            await callback.message.edit_text(
                text, reply_markup=keyboards.back_to_menu(lang)
            )
        except Exception:
            await callback.message.answer(
                text, reply_markup=keyboards.back_to_menu(lang)
            )

        # Notify admin
        if ADMIN_CHAT_ID:
            try:
                bot = get_bot()
                user_name = user.get("first_name") or user.get("telegram_username") or "Unknown"
                admin_text = TEXTS["admin_order_cancelled"].format(
                    order_id=cancelled["public_order_id"],
                    user_name=user_name,
                    telegram_id=user["telegram_id"],
                )
                await bot.send_message(ADMIN_CHAT_ID, admin_text)
            except Exception as e:
                logger.error(f"Failed to notify admin about cancellation: {e}")

    except ValueError:
        try:
            await callback.message.edit_text(
                get_text("order_cancel_failed", lang),
                reply_markup=keyboards.back_to_menu(lang),
            )
        except Exception:
            await callback.message.answer(
                get_text("order_cancel_failed", lang),
                reply_markup=keyboards.back_to_menu(lang),
            )
    except Exception as e:
        logger.error(f"Error cancelling order {order_id}: {e}", exc_info=True)
        try:
            await callback.message.edit_text(
                get_text("error_generic", lang),
                reply_markup=keyboards.back_to_menu(lang),
            )
        except Exception:
            await callback.message.answer(
                get_text("error_generic", lang),
                reply_markup=keyboards.back_to_menu(lang),
            )

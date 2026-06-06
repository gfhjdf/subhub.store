"""Handler: support and warranty checks."""
import logging
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup

from src.config import WARRANTY_DAYS
from src.services import user_service, order_service, settings_service
from src.bot.texts import get_text
from src.bot import keyboards

logger = logging.getLogger("subhub.bot.support")
router = Router(name="support")


async def _get_user_and_lang(telegram_id: int) -> tuple[dict | None, str]:
    """Get user dict and language."""
    user = await user_service.get_user_by_telegram_id(telegram_id)
    lang = user.get("language_code", "uz") if user else "uz"
    return user, lang


async def _get_support_data(user: dict, lang: str) -> tuple[str, InlineKeyboardMarkup]:
    """Prepare support message text and keyboard markup."""
    support_text = await settings_service.get_text("support_text", lang)
    if not support_text:
        support_text = "@Abdulloh_Zokirov"

    text = get_text("support_title", lang).format(support_text=support_text)

    # Show user's delivered orders with warranty check buttons
    orders = await order_service.get_user_orders(user["id"])
    delivered_orders = [
        o for o in orders if o["status"] == "delivered"
    ]

    if delivered_orders:
        from aiogram.utils.keyboard import InlineKeyboardBuilder

        builder = InlineKeyboardBuilder()
        for order in delivered_orders[:10]:  # Limit to 10 most recent
            # Check if warranty is still valid
            delivered_at = order.get("delivered_at")
            is_valid = False
            if delivered_at:
                try:
                    dt = datetime.fromisoformat(delivered_at)
                    is_valid = datetime.utcnow() - dt < timedelta(days=WARRANTY_DAYS)
                except (ValueError, TypeError):
                    pass

            if is_valid:
                label = f"🛡 #{order['public_order_id']}"
            else:
                label = f"⏰ #{order['public_order_id']}"

            builder.button(
                text=label,
                callback_data=f"support:order:{order['id']}",
            )
        builder.button(
            text=get_text("btn_back_to_menu", lang), callback_data="menu:main"
        )
        builder.adjust(1)
        kb = builder.as_markup()
    else:
        kb = keyboards.back_to_menu(lang)
    return text, kb


@router.callback_query(F.data == "menu:support")
async def show_support(callback: CallbackQuery) -> None:
    """Show support information with admin contact via callback."""
    await callback.answer()
    user, lang = await _get_user_and_lang(callback.from_user.id)
    if not user:
        return

    try:
        text, kb = await _get_support_data(user, lang)
        try:
            await callback.message.edit_text(text, reply_markup=kb)
        except Exception:
            await callback.message.answer(text, reply_markup=kb)
    except Exception as e:
        logger.error(f"Error showing support callback: {e}", exc_info=True)
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


@router.message(Command("support"))
async def cmd_support(message: Message) -> None:
    """Show support information with admin contact via /support command."""
    user, lang = await _get_user_and_lang(message.from_user.id)
    if not user:
        return

    try:
        text, kb = await _get_support_data(user, lang)
        await message.answer(text, reply_markup=kb)
    except Exception as e:
        logger.error(f"Error showing support command: {e}", exc_info=True)
        await message.answer(
            get_text("error_generic", lang),
            reply_markup=keyboards.back_to_menu(lang),
        )


@router.callback_query(F.data.startswith("support:order:"))
async def check_warranty(callback: CallbackQuery) -> None:
    """Check warranty status for a specific order."""
    await callback.answer()
    user, lang = await _get_user_and_lang(callback.from_user.id)
    if not user:
        return

    try:
        order_id = int(callback.data.split(":")[2])
    except (ValueError, IndexError):
        await callback.message.edit_text(
            get_text("error_generic", lang),
            reply_markup=keyboards.back_to_menu(lang),
        )
        return

    try:
        order = await order_service.get_order_by_id(order_id)
        if not order or order["user_id"] != user["id"]:
            try:
                await callback.message.edit_text(
                    get_text("error_not_found", lang),
                    reply_markup=keyboards.back_to_menu(lang),
                )
            except Exception:
                await callback.message.answer(
                    get_text("error_not_found", lang),
                    reply_markup=keyboards.back_to_menu(lang),
                )
            return

        # Check warranty
        delivered_at = order.get("delivered_at")
        warranty_valid = False
        if delivered_at:
            try:
                dt = datetime.fromisoformat(delivered_at)
                warranty_valid = datetime.utcnow() - dt < timedelta(days=WARRANTY_DAYS)
            except (ValueError, TypeError):
                pass

        if warranty_valid:
            # Warranty valid — show contact admin text
            support_text = await settings_service.get_text("support_text", lang)
            if not support_text:
                support_text = "@Abdulloh_Zokirov"

            text = get_text("warranty_valid", lang).format(
                order_id=order["public_order_id"]
            ) + f"\n\n{support_text}"
        else:
            # Warranty expired
            expired_text = await settings_service.get_text("warranty_expired", lang)
            if expired_text:
                text = expired_text
            else:
                text = get_text("warranty_expired", lang).format(
                    order_id=order["public_order_id"]
                )

        try:
            await callback.message.edit_text(
                text, reply_markup=keyboards.back_to_menu(lang)
            )
        except Exception:
            await callback.message.answer(
                text, reply_markup=keyboards.back_to_menu(lang)
            )

    except Exception as e:
        logger.error(f"Error checking warranty for order {order_id}: {e}", exc_info=True)
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

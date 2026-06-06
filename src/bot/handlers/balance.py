"""Handler: balance display and referral program info."""
import logging
import uuid
from pathlib import Path
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

from src.config import ADMIN_CHAT_ID, UPLOAD_DIR
from src.services import (
    user_service,
    wallet_service,
    referral_service,
    points_service,
    rewards_service,
    settings_service,
    audit_service,
)
from src.bot.texts import get_text, format_price, STATUS_MAP
from src.bot import keyboards
from src.bot.bot import get_bot

logger = logging.getLogger("subhub.bot.balance")
router = Router(name="balance")


class WalletStates(StatesGroup):
    waiting_for_amount = State()
    waiting_for_screenshot = State()


async def _get_user_and_lang(telegram_id: int) -> tuple[dict | None, str]:
    """Get user dict and language."""
    user = await user_service.get_user_by_telegram_id(telegram_id)
    lang = user.get("language_code", "uz") if user else "uz"
    return user, lang


@router.callback_query(F.data == "menu:balance")
async def show_balance(callback: CallbackQuery, state: FSMContext) -> None:
    """Show user's current wallet balance and operations."""
    await callback.answer()
    await state.clear()  # Clear state if any
    user, lang = await _get_user_and_lang(callback.from_user.id)
    if not user:
        return

    try:
        balance = await wallet_service.get_wallet_balance(user["id"])

        text = get_text("wallet_menu", lang).format(
            balance=format_price(balance),
        )

        try:
            await callback.message.edit_text(
                text, reply_markup=keyboards.wallet_menu_keyboard(lang)
            )
        except Exception:
            await callback.message.answer(
                text, reply_markup=keyboards.wallet_menu_keyboard(lang)
            )
    except Exception as e:
        logger.error(f"Error showing wallet menu: {e}")
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


@router.callback_query(F.data == "wallet:topup")
async def wallet_topup_start(callback: CallbackQuery, state: FSMContext) -> None:
    """Prompt user for top-up amount."""
    await callback.answer()
    user, lang = await _get_user_and_lang(callback.from_user.id)
    if not user:
        return

    # Check if wallet system is enabled
    enabled_val = await settings_service.get_setting("wallet_enabled")
    if enabled_val == "false":
        await callback.message.edit_text(
            get_text("wallet_disabled_error", lang),
            reply_markup=keyboards.back_to_wallet(lang),
        )
        return

    min_val = await settings_service.get_setting("wallet_min_topup")
    max_val = await settings_service.get_setting("wallet_max_topup")

    min_topup = int(min_val) if min_val else 5000
    max_topup = int(max_val) if max_val else 1000000

    text = get_text("wallet_topup_amount_prompt", lang).format(
        min_topup=format_price(min_topup),
        max_topup=format_price(max_topup),
    )

    await callback.message.edit_text(
        text,
        reply_markup=keyboards.back_to_wallet(lang),
    )
    await state.set_state(WalletStates.waiting_for_amount)


@router.message(WalletStates.waiting_for_amount)
async def wallet_topup_amount_received(message: Message, state: FSMContext) -> None:
    """Handle custom top-up amount input."""
    user, lang = await _get_user_and_lang(message.from_user.id)
    if not user:
        return

    amount_str = message.text.strip()
    if not amount_str.isdigit():
        await message.answer(
            get_text("wallet_topup_invalid_amount", lang),
            reply_markup=keyboards.back_to_wallet(lang),
        )
        return

    amount = int(amount_str)

    min_val = await settings_service.get_setting("wallet_min_topup")
    max_val = await settings_service.get_setting("wallet_max_topup")

    min_topup = int(min_val) if min_val else 5000
    max_topup = int(max_val) if max_val else 1000000

    if amount < min_topup or amount > max_topup:
        await message.answer(
            get_text("wallet_topup_limit_error", lang).format(
                min_topup=format_price(min_topup),
                max_topup=format_price(max_topup),
            ),
            reply_markup=keyboards.back_to_wallet(lang),
        )
        return

    await state.update_data(amount=amount)
    await state.set_state(WalletStates.waiting_for_screenshot)

    card_number = await settings_service.get_setting("card_number") or "9860606756718767"
    card_holder = await settings_service.get_setting("card_holder") or "Abdulloh Zokirov"

    text = get_text("wallet_topup_screenshot_prompt", lang).format(
        amount=format_price(amount),
        card_number=card_number,
        card_holder=card_holder,
    )

    await message.answer(
        text,
        reply_markup=keyboards.back_to_wallet(lang),
    )


@router.message(WalletStates.waiting_for_screenshot, F.photo)
async def wallet_topup_photo_received(message: Message, state: FSMContext) -> None:
    """Handle top-up screenshot upload (photo)."""
    await _process_topup_screenshot(message, state, message.photo[-1].file_id)


@router.message(WalletStates.waiting_for_screenshot, F.document)
async def wallet_topup_document_received(message: Message, state: FSMContext) -> None:
    """Handle top-up screenshot upload (document)."""
    user, lang = await _get_user_and_lang(message.from_user.id)
    if not user:
        return

    if message.document.mime_type and not message.document.mime_type.startswith("image/"):
        await message.answer(
            get_text("error_generic", lang),
            reply_markup=keyboards.back_to_wallet(lang),
        )
        return

    await _process_topup_screenshot(message, state, message.document.file_id)


async def _process_topup_screenshot(message: Message, state: FSMContext, file_id: str) -> None:
    """Common logic to download screenshot and save pending topup request."""
    user, lang = await _get_user_and_lang(message.from_user.id)
    if not user:
        return

    data = await state.get_data()
    amount = data.get("amount")
    if not amount:
        # Fallback if state is lost
        await state.clear()
        await message.answer(
            get_text("error_generic", lang),
            reply_markup=keyboards.back_to_wallet(lang),
        )
        return

    try:
        # Download photo
        bot = get_bot()
        file = await bot.get_file(file_id)
        
        ext = file.file_path.split('.')[-1] if file.file_path and '.' in file.file_path else 'jpg'
        filename = f"topup_{user['id']}_{uuid.uuid4().hex[:8]}.{ext}"
        
        local_dir = UPLOAD_DIR
        local_dir.mkdir(parents=True, exist_ok=True)
        local_path = local_dir / filename
        
        await bot.download(file, destination=local_path)
        db_screenshot_path = f"uploads/screenshots/{filename}"

        # Create top-up request
        topup = await wallet_service.create_topup_request(
            user_id=user["id"],
            amount_requested=amount,
            screenshot_path=db_screenshot_path,
            screenshot_file_id=file_id,
        )

        await audit_service.log_action(
            actor_type="user",
            action="wallet_topup_requested",
            entity_type="wallet_topup",
            entity_id=topup["id"],
            meta={"telegram_id": message.from_user.id, "amount_requested": amount},
        )

        await state.clear()

        # Confirm to user
        await message.answer(
            get_text("wallet_topup_submitted", lang).format(
                topup_id=topup["public_topup_id"],
                amount=format_price(amount),
            ),
            reply_markup=keyboards.back_to_wallet(lang),
        )

        # Notify admin
        await _notify_admin_topup(topup, user)

    except Exception as e:
        logger.error(f"Error handling top-up screenshot: {e}", exc_info=True)
        await message.answer(
            get_text("error_generic", lang),
            reply_markup=keyboards.back_to_wallet(lang),
        )


async def _notify_admin_topup(topup: dict, user: dict) -> None:
    """Send admin notification about a new wallet top-up request."""
    if not ADMIN_CHAT_ID:
        logger.warning("ADMIN_CHAT_ID not configured, skipping admin notification")
        return

    bot = get_bot()
    user_name = user.get("first_name") or user.get("telegram_username") or "Unknown"

    text = get_text("admin_new_topup", "ru").format(
        topup_id=topup.get("public_topup_id", "?"),
        db_id=topup.get("id", "?"),
        user_name=user_name,
        telegram_id=user.get("telegram_id", "?"),
        amount=format_price(topup.get("amount_requested", 0)),
    )

    try:
        file_id = topup.get("screenshot_file_id")
        if file_id:
            await bot.send_photo(ADMIN_CHAT_ID, photo=file_id, caption=text)
        else:
            await bot.send_message(ADMIN_CHAT_ID, text)
    except Exception as e:
        logger.error(f"Failed to notify admin of topup: {e}")


@router.callback_query(F.data == "wallet:history")
async def wallet_history(callback: CallbackQuery) -> None:
    """Show user's wallet transactions history."""
    await callback.answer()
    user, lang = await _get_user_and_lang(callback.from_user.id)
    if not user:
        return

    try:
        transactions = await wallet_service.get_wallet_transactions(user["id"], limit=15)
        if not transactions:
            await callback.message.edit_text(
                get_text("wallet_history_empty", lang),
                reply_markup=keyboards.back_to_wallet(lang),
            )
            return

        lines = []
        for tx in transactions:
            # Format date: YYYY-MM-DD HH:MM
            date_str = tx["created_at"][:16] if tx["created_at"] else "—"
            
            # Map type to label
            type_key = f"wallet_tx_type_{tx['type']}"
            type_label = get_text(type_key, lang)
            
            # Format amount with sign
            amt = tx["amount"]
            sign = "+" if amt >= 0 else ""
            amt_str = f"{sign}{format_price(amt)}"

            desc = tx["description"] or "—"
            item_text = get_text("wallet_history_item", lang).format(
                date=date_str,
                type=type_label,
                amount=amt_str,
                description=desc,
            )
            lines.append(item_text)

        text = "\n".join(lines)
        if len(text) > 4000:
            text = text[:3900] + "\n..."

        await callback.message.edit_text(
            text,
            reply_markup=keyboards.back_to_wallet(lang),
        )
    except Exception as e:
        logger.error(f"Error showing wallet history: {e}")
        await callback.message.edit_text(
            get_text("error_generic", lang),
            reply_markup=keyboards.back_to_wallet(lang),
        )


@router.callback_query(F.data == "menu:referral")
async def show_referral(callback: CallbackQuery) -> None:
    """Show points balance and referral link/actions."""
    if isinstance(callback, CallbackQuery):
        await callback.answer()
        message = callback.message
        user_id = callback.from_user.id
    else:
        # Allow calling from other handlers with message
        message = callback
        user_id = message.chat.id

    user, lang = await _get_user_and_lang(user_id)
    if not user:
        return

    try:
        ref_info = await referral_service.get_referral_info(user["id"])
        points_balance = await points_service.get_points_balance(user["id"])

        # Build the referral link using bot username
        bot = get_bot()
        bot_info = await bot.get_me()
        ref_link = f"https://t.me/{bot_info.username}?start=ref_{ref_info['code']}"

        # Get settings points amount
        points_val = await settings_service.get_setting("points_per_referral")
        points_per_ref = int(points_val) if points_val else 1

        text = get_text("points_rewards_menu", lang).format(
            points_balance=points_balance,
            link=ref_link,
            invited_count=ref_info["invited_count"],
            referral_points=ref_info["total_points_earned"],
            points_per_ref=points_per_ref,
        )

        try:
            await message.edit_text(
                text, reply_markup=keyboards.points_menu_keyboard(lang)
            )
        except Exception:
            await message.answer(
                text, reply_markup=keyboards.points_menu_keyboard(lang)
            )
    except Exception as e:
        logger.error(f"Error showing points menu: {e}")
        try:
            await message.edit_text(
                get_text("error_generic", lang),
                reply_markup=keyboards.back_to_menu(lang),
            )
        except Exception:
            await message.answer(
                get_text("error_generic", lang),
                reply_markup=keyboards.back_to_menu(lang),
            )


@router.callback_query(F.data == "points:checkin")
async def process_daily_checkin(callback: CallbackQuery) -> None:
    """Process daily check-in for the user."""
    user, lang = await _get_user_and_lang(callback.from_user.id)
    if not user:
        await callback.answer()
        return

    try:
        success, points_rewarded, status_code = await points_service.claim_daily_checkin(user["id"])
        
        if success:
            new_balance = await points_service.get_points_balance(user["id"])
            await callback.answer(
                get_text("daily_checkin_success", lang).format(points=points_rewarded, balance=new_balance),
                show_alert=True
            )
            # Refresh referral/points menu
            await show_referral(callback)
        elif status_code == "already_claimed":
            await callback.answer(get_text("daily_checkin_already_claimed", lang), show_alert=True)
        else:
            await callback.answer(get_text("error_generic", lang), show_alert=True)
    except Exception as e:
        logger.error(f"Error processing check-in: {e}")
        await callback.answer(get_text("error_generic", lang), show_alert=True)


@router.callback_query(F.data == "points:catalog")
async def show_rewards_catalog(callback: CallbackQuery) -> None:
    """List active rewards in the catalog."""
    await callback.answer()
    user, lang = await _get_user_and_lang(callback.from_user.id)
    if not user:
        return

    try:
        rewards = await rewards_service.get_active_rewards()
        if not rewards:
            await callback.message.edit_text(
                get_text("no_active_rewards", lang),
                reply_markup=keyboards.back_to_points_rewards(lang)
            )
            return

        text = get_text("rewards_catalog_title", lang)
        await callback.message.edit_text(
            text,
            reply_markup=keyboards.rewards_catalog_keyboard(rewards, lang)
        )
    except Exception as e:
        logger.error(f"Error showing rewards catalog: {e}")
        await callback.message.edit_text(
            get_text("error_generic", lang),
            reply_markup=keyboards.back_to_points_rewards(lang)
        )


@router.callback_query(F.data.startswith("reward:view:"))
async def view_reward_detail(callback: CallbackQuery) -> None:
    """View details of a specific reward."""
    await callback.answer()
    user, lang = await _get_user_and_lang(callback.from_user.id)
    if not user:
        return

    try:
        reward_id = int(callback.data.split(":")[-1])
        reward = await rewards_service.get_reward_by_id(reward_id)
        if not reward or not reward["is_active"]:
            await callback.message.edit_text(
                get_text("error_not_found", lang),
                reply_markup=keyboards.back_to_points_rewards(lang)
            )
            return

        user_points = await points_service.get_points_balance(user["id"])
        
        desc = reward["description_uz"] if lang == "uz" else reward["description_ru"]
        text = get_text("reward_detail", lang).format(
            name=reward["name"],
            points_required=reward["points_required"],
            description=desc or "—",
            user_points=user_points
        )

        await callback.message.edit_text(
            text,
            reply_markup=keyboards.reward_detail_keyboard(
                reward_id=reward["id"],
                user_points=user_points,
                points_required=reward["points_required"],
                lang=lang
            )
        )
    except Exception as e:
        logger.error(f"Error viewing reward detail: {e}")
        await callback.message.edit_text(
            get_text("error_generic", lang),
            reply_markup=keyboards.back_to_points_rewards(lang)
        )


@router.callback_query(F.data.startswith("reward:redeem:"))
async def redeem_reward(callback: CallbackQuery) -> None:
    """Redeem a reward using points."""
    await callback.answer()
    user, lang = await _get_user_and_lang(callback.from_user.id)
    if not user:
        return

    try:
        reward_id = int(callback.data.split(":")[-1])
        try:
            redemption = await rewards_service.create_redemption(
                user_id=user["id"],
                reward_id=reward_id
            )
            
            if redemption.get("status") == "completed":
                text = get_text("redemption_success_auto", lang).format(
                    public_id=redemption["public_redemption_id"],
                    points_spent=redemption["points_spent"],
                    login=redemption.get("account_login") or "—",
                    password=redemption.get("account_password") or "—",
                    notes=redemption.get("account_notes") or "—"
                )
            else:
                text = get_text("redemption_success", lang).format(
                    public_id=redemption["public_redemption_id"],
                    points_spent=redemption["points_spent"]
                )

            await callback.message.edit_text(
                text,
                reply_markup=keyboards.back_to_points_rewards(lang)
            )
        except ValueError as val_err:
            error_str = str(val_err)
            if "Insufficient points" in error_str:
                await callback.message.edit_text(
                    get_text("redemption_failed_insufficient_points", lang),
                    reply_markup=keyboards.back_to_points_rewards(lang)
                )
            elif "out_of_stock" in error_str:
                out_of_stock_msg = (
                    "😔 Kechirasiz, ushbu sovg'a uchun mavjud akkauntlar vaqtincha tugagan. Iltimos, keyinroq qayta urunib ko'ring yoki qo'llab-quvvatlash xizmatiga murojaat qiling."
                    if lang == "uz" else
                    "😔 Извините, доступные аккаунты для этого подарка временно закончились. Пожалуйста, попробуйте позже или обратитесь в поддержку."
                )
                await callback.message.edit_text(
                    out_of_stock_msg,
                    reply_markup=keyboards.back_to_points_rewards(lang)
                )
            else:
                await callback.message.edit_text(
                    f"❌ {error_str}",
                    reply_markup=keyboards.back_to_points_rewards(lang)
                )
    except Exception as e:
        logger.error(f"Error redeeming reward: {e}")
        await callback.message.edit_text(
            get_text("error_generic", lang),
            reply_markup=keyboards.back_to_points_rewards(lang)
        )


@router.callback_query(F.data == "points:redemptions")
async def show_my_redemptions(callback: CallbackQuery) -> None:
    """Show redemption history of the user."""
    await callback.answer()
    user, lang = await _get_user_and_lang(callback.from_user.id)
    if not user:
        return

    try:
        redemptions = await rewards_service.get_user_redemptions(user["id"])
        if not redemptions:
            await callback.message.edit_text(
                get_text("no_redemptions", lang),
                reply_markup=keyboards.back_to_points_rewards(lang)
            )
            return

        lines = [get_text("my_redemptions_title", lang)]
        
        for r in redemptions:
            status_text = get_text(STATUS_MAP.get(r["status"], "status_created"), lang)
            item_text = get_text("redemption_item", lang).format(
                public_id=r["public_redemption_id"],
                reward_name=r["reward_name"],
                points_spent=r["points_spent"],
                status_text=status_text,
                date=r["created_at"][:16]  # YYYY-MM-DD HH:MM
            )
            if r["status"] == "rejected" and r["rejection_note"]:
                item_text += get_text("redemption_rejection_note", lang).format(note=r["rejection_note"])
            elif r["status"] == "completed" and r.get("account_login"):
                item_text += get_text("redemption_item_credentials", lang).format(
                    login=r["account_login"],
                    password=r["account_password"],
                    notes=r["account_notes"] or "—"
                )
            lines.append(item_text)

        text = "\n".join(lines)
        if len(text) > 4000:
            text = text[:3900] + "\n..."
            
        await callback.message.edit_text(
            text,
            reply_markup=keyboards.back_to_points_rewards(lang)
        )
    except Exception as e:
        logger.error(f"Error showing user redemptions: {e}")
        await callback.message.edit_text(
            get_text("error_generic", lang),
            reply_markup=keyboards.back_to_points_rewards(lang)
        )

"""Handler: /start command — registration, referral, language selection, main menu."""
import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart, CommandObject
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.services import user_service, referral_service, catalog_service, settings_service
from src.bot.texts import get_text
from src.bot import keyboards


async def is_user_subscribed(bot, user_id: int) -> bool:
    """Check if the user is subscribed to the required channel."""
    sub_enabled_str = await settings_service.get_setting("sub_check_enabled")
    sub_enabled = (sub_enabled_str == "true" or sub_enabled_str is True)
    if not sub_enabled:
        return True

    channel = await settings_service.get_setting("sub_channel_username")
    if not channel:
        return True

    channel_id = channel.strip()
    if "/" in channel_id:
        parts = channel_id.split("/")
        channel_id = "@" + parts[-1]
    elif not channel_id.startswith("@") and not channel_id.startswith("-"):
        channel_id = "@" + channel_id

    try:
        member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
        if member.status in ["creator", "administrator", "member"] or (member.status == "restricted"):
            return True
    except Exception as e:
        logger.warning(f"Handler subscription check failed for user {user_id} in {channel_id}: {e}")
        return False
    return False


async def send_subscription_prompt(message_or_callback, lang: str) -> None:
    """Send subscription instructions to the user."""
    channel = await settings_service.get_setting("sub_channel_username")
    custom_msg = await settings_service.get_text("sub_message", lang)
    if not custom_msg:
        if lang == "uz":
            custom_msg = "⚠️ Botdan foydalanish uchun rasmiy kanalimizga a'zo bo'ling."
        else:
            custom_msg = "⚠️ Для использования бота подпишитесь на наш официальный канал."

    link = channel.strip() if channel else "@subhub_uz"
    if not link.startswith("http"):
        clean_username = link.replace("@", "")
        link = f"https://t.me/{clean_username}"

    kb_builder = InlineKeyboardBuilder()
    btn_sub_text = "📢 A'zo bo'lish / Подписаться" if lang == "uz" else "📢 Подписаться на канал"
    btn_check_text = "✅ Tekshirish / Проверить" if lang == "uz" else "✅ Проверить подписку"
    
    kb_builder.button(text=btn_sub_text, url=link)
    kb_builder.button(text=btn_check_text, callback_data="sub_check")
    kb_builder.adjust(1)
    kb = kb_builder.as_markup()

    if isinstance(message_or_callback, Message):
        await message_or_callback.answer(custom_msg, reply_markup=kb)
    else:
        try:
            await message_or_callback.message.edit_text(custom_msg, reply_markup=kb)
        except Exception:
            await message_or_callback.message.answer(custom_msg, reply_markup=kb)

logger = logging.getLogger("subhub.bot.start")
router = Router(name="start")


@router.message(CommandStart(deep_link=True))
async def cmd_start_deeplink(message: Message, command: CommandObject) -> None:
    """Handle /start with a deep-link parameter (e.g., ref_CODE)."""
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    # Register or update user
    user = await user_service.register_or_update_user(
        telegram_id, username, first_name, last_name
    )

    # Process referral deep-link: format is ref_CODE
    deep_link = command.args
    if deep_link and deep_link.startswith("ref_"):
        referral_code = deep_link[4:]  # Strip "ref_" prefix
        if user.get("referred_by_user_id") is None:
            try:
                result = await referral_service.apply_referral(referral_code, telegram_id)
                if result.get("suspicious"):
                    logger.warning(
                        f"Suspicious referral detected: code={referral_code}, "
                        f"invited={telegram_id}"
                    )
            except Exception as e:
                logger.error(f"Referral apply error: {e}")

    lang = user.get("language_code") or "uz"
 
    # If user has no language set explicitly, show language picker
    if not user.get("language_code"):
        await message.answer(
            get_text("choose_language", lang),
            reply_markup=keyboards.language_select(),
        )
        return

    # Check subscription
    if not await is_user_subscribed(message.bot, telegram_id):
        await send_subscription_prompt(message, lang)
        return
 
    platforms = await catalog_service.get_active_platforms()
    await message.answer(
        get_text("welcome", lang),
        reply_markup=keyboards.main_menu(platforms, lang),
    )


@router.message(CommandStart())
async def cmd_start(message: Message) -> None:
    """Handle plain /start command (no deep-link)."""
    telegram_id = message.from_user.id
    username = message.from_user.username
    first_name = message.from_user.first_name
    last_name = message.from_user.last_name

    user = await user_service.register_or_update_user(
        telegram_id, username, first_name, last_name
    )

    lang = user.get("language_code") or "uz"
 
    if not user.get("language_code"):
        await message.answer(
            get_text("choose_language", lang),
            reply_markup=keyboards.language_select(),
        )
        return

    # Check subscription
    if not await is_user_subscribed(message.bot, telegram_id):
        await send_subscription_prompt(message, lang)
        return
 
    platforms = await catalog_service.get_active_platforms()
    await message.answer(
        get_text("welcome", lang),
        reply_markup=keyboards.main_menu(platforms, lang),
    )


@router.callback_query(F.data == "sub_check")
async def handle_sub_check(callback: CallbackQuery) -> None:
    """Verify subscription on click and unlock bot features."""
    telegram_id = callback.from_user.id
    user = await user_service.get_user_by_telegram_id(telegram_id)
    lang = user.get("language_code", "uz") if user else "uz"
    
    if await is_user_subscribed(callback.bot, telegram_id):
        success_msg = "✅ A'zolik tasdiqlandi!" if lang == "uz" else "✅ Подписка подтверждена!"
        await callback.answer(success_msg, show_alert=True)
        
        platforms = await catalog_service.get_active_platforms()
        try:
            await callback.message.edit_text(
                get_text("main_menu", lang),
                reply_markup=keyboards.main_menu(platforms, lang),
            )
        except Exception:
            await callback.message.answer(
                get_text("main_menu", lang),
                reply_markup=keyboards.main_menu(platforms, lang),
            )
    else:
        error_msg = "❌ Iltimos, avval kanalga a'zo bo'ling." if lang == "uz" else "❌ Пожалуйста, сначала подпишитесь на канал."
        await callback.answer(error_msg, show_alert=True)

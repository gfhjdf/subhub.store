"""Handler: language selection — lang:uz / lang:ru callbacks."""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery

from src.services import user_service, catalog_service
from src.bot.texts import get_text
from src.bot import keyboards

logger = logging.getLogger("subhub.bot.language")
router = Router(name="language")


@router.callback_query(F.data == "menu:language")
async def show_language_select(callback: CallbackQuery) -> None:
    """Show language selection keyboard."""
    await callback.answer()
    user = await user_service.get_user_by_telegram_id(callback.from_user.id)
    lang = user.get("language_code", "uz") if user else "uz"
    try:
        await callback.message.edit_text(
            get_text("choose_language", lang),
            reply_markup=keyboards.language_select(),
        )
    except Exception:
        await callback.message.answer(
            get_text("choose_language", lang),
            reply_markup=keyboards.language_select(),
        )


@router.callback_query(F.data.startswith("lang:"))
async def set_language(callback: CallbackQuery) -> None:
    """Handle language selection: lang:uz or lang:ru."""
    lang = callback.data.split(":")[1]
    if lang not in ("uz", "ru"):
        lang = "uz"

    telegram_id = callback.from_user.id
    await user_service.update_language(telegram_id, lang)
    await callback.answer(get_text("language_set", lang))

    # Check subscription
    from src.bot.handlers.start import is_user_subscribed, send_subscription_prompt
    if not await is_user_subscribed(callback.bot, telegram_id):
        await send_subscription_prompt(callback, lang)
        return

    # Show confirmation and main menu
    try:
        platforms = await catalog_service.get_active_platforms()
        await callback.message.edit_text(
            get_text("language_set", lang) + "\n\n" + get_text("main_menu", lang),
            reply_markup=keyboards.main_menu(platforms, lang),
        )
    except Exception:
        platforms = await catalog_service.get_active_platforms()
        await callback.message.answer(
            get_text("language_set", lang) + "\n\n" + get_text("main_menu", lang),
            reply_markup=keyboards.main_menu(platforms, lang),
        )

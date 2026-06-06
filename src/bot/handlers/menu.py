"""Handler: main menu routing — routes menu:* callbacks to respective sections."""
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery

from src.services import user_service, catalog_service
from src.bot.texts import get_text
from src.bot import keyboards

logger = logging.getLogger("subhub.bot.menu")
router = Router(name="menu")


async def _get_lang(telegram_id: int) -> str:
    """Get user's language preference."""
    user = await user_service.get_user_by_telegram_id(telegram_id)
    return user.get("language_code", "uz") if user else "uz"


@router.callback_query(F.data == "menu:main")
async def show_main_menu(callback: CallbackQuery) -> None:
    """Show the main menu."""
    await callback.answer()
    lang = await _get_lang(callback.from_user.id)
    try:
        platforms = await catalog_service.get_active_platforms()
        await callback.message.edit_text(
            get_text("main_menu", lang),
            reply_markup=keyboards.main_menu(platforms, lang),
        )
    except Exception:
        platforms = await catalog_service.get_active_platforms()
        await callback.message.answer(
            get_text("main_menu", lang),
            reply_markup=keyboards.main_menu(platforms, lang),
        )


@router.callback_query(F.data == "menu:faq")
async def show_faq(callback: CallbackQuery) -> None:
    """Show FAQ text."""
    await callback.answer()
    lang = await _get_lang(callback.from_user.id)
    try:
        await callback.message.edit_text(
            get_text("faq_text", lang),
            reply_markup=keyboards.back_to_menu(lang),
        )
    except Exception:
        await callback.message.answer(
            get_text("faq_text", lang),
            reply_markup=keyboards.back_to_menu(lang),
        )

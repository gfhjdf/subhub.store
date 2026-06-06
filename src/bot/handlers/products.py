"""Handler: product browsing — platforms list, plans list, plan detail."""
import logging
import re
from aiogram import Router, F
from aiogram.types import CallbackQuery

from src.services import user_service, catalog_service, settings_service
from src.bot.texts import get_text, format_price, format_emoji_for_message
from src.bot import keyboards


async def get_support_username() -> str:
    """Extract support telegram username from settings."""
    support_text = await settings_service.get_text("support_text", "uz")
    if not support_text:
        return "Abdulloh_Zokirov"
    match = re.search(r"@([a-zA-Z0-9_]{5,32})", support_text)
    if match:
        return match.group(1)
    return "Abdulloh_Zokirov"

logger = logging.getLogger("subhub.bot.products")
router = Router(name="products")


async def _get_lang(telegram_id: int) -> str:
    """Get user's language preference."""
    user = await user_service.get_user_by_telegram_id(telegram_id)
    return user.get("language_code", "uz") if user else "uz"


@router.callback_query(F.data == "menu:products")
async def show_platforms(callback: CallbackQuery) -> None:
    """Redirect to main menu since products are shown there directly."""
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


@router.callback_query(F.data.startswith("platform:"))
async def show_plans(callback: CallbackQuery) -> None:
    """Show plans for a specific platform."""
    await callback.answer()
    lang = await _get_lang(callback.from_user.id)

    try:
        platform_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.message.edit_text(
            get_text("error_generic", lang),
            reply_markup=keyboards.back_to_menu(lang),
        )
        return

    try:
        platform = await catalog_service.get_platform_by_id(platform_id)
        if not platform:
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

        plans = await catalog_service.get_plans_for_platform(platform_id)
        if not plans:
            text = get_text("no_plans", lang)
            try:
                await callback.message.edit_text(
                    text,
                    reply_markup=keyboards.back_to_platforms(lang),
                )
            except Exception:
                await callback.message.answer(
                    text,
                    reply_markup=keyboards.back_to_platforms(lang),
                )
            return

        emoji_str = format_emoji_for_message(platform.get("custom_emoji_code"))
        platform_name = f"{emoji_str} {platform['name']}".strip() if emoji_str else platform["name"]
        text = get_text("plans_title", lang).format(platform=platform_name)
        try:
            await callback.message.edit_text(
                text,
                reply_markup=keyboards.plans_list(plans, platform_id, lang),
            )
        except Exception:
            await callback.message.answer(
                text,
                reply_markup=keyboards.plans_list(plans, platform_id, lang),
            )
    except Exception as e:
        logger.error(f"Error loading plans for platform {platform_id}: {e}")
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


@router.callback_query(F.data.startswith("plan:"))
async def show_plan_detail(callback: CallbackQuery) -> None:
    """Show plan detail with price, stock count, description, FAQ, and buy button."""
    await callback.answer()
    lang = await _get_lang(callback.from_user.id)

    try:
        plan_id = int(callback.data.split(":")[1])
    except (ValueError, IndexError):
        await callback.message.edit_text(
            get_text("error_generic", lang),
            reply_markup=keyboards.back_to_menu(lang),
        )
        return

    try:
        plan = await catalog_service.get_plan_by_id(plan_id)
        if not plan:
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

        stock = plan.get("stock", 0)
        description = plan.get(f"description_{lang}") or plan.get("description_ru", "")
        faq = plan.get(f"faq_{lang}") or plan.get("faq_ru", "")

        emoji_str = format_emoji_for_message(plan.get("platform_emoji_code"))
        platform_name = f"{emoji_str} {plan['platform_name']}".strip() if emoji_str else plan["platform_name"]

        plan_type = plan.get("plan_type", "regular")

        if plan_type == "contact_admin":
            text = get_text("plan_detail_contact_admin", lang).format(
                platform=platform_name,
                plan=plan["name"],
                stock=stock,
                description=description,
            )
        else:
            text = get_text("plan_detail", lang).format(
                platform=platform_name,
                plan=plan["name"],
                price=format_price(plan["price_uzs"]),
                stock=stock,
                description=description,
            )

        if faq:
            text += get_text("plan_detail_faq", lang).format(faq=faq)

        if plan_type != "contact_admin" and stock == 0:
            text += "\n\n" + get_text("out_of_stock", lang)

        support_username = "subhub_support"
        if plan_type == "contact_admin":
            support_username = await get_support_username()

        kb = keyboards.plan_detail(
            plan_id=plan_id,
            platform_id=plan["platform_id"],
            has_stock=stock > 0,
            lang=lang,
            plan_type=plan_type,
            admin_username=support_username,
        )

        try:
            await callback.message.edit_text(text, reply_markup=kb)
        except Exception:
            await callback.message.answer(text, reply_markup=kb)
    except Exception as e:
        logger.error(f"Error loading plan {plan_id}: {e}")
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

"""Inline keyboard builders for SubHub.store Telegram bot (aiogram 3.x)."""
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup

from src.bot.texts import get_text, format_price
import re


def clean_emoji_for_button(emoji_code: str | None) -> str:
    """Extract standard emoji/text from HTML tags or IDs (e.g., <tg-emoji ...>🤖</tg-emoji> -> 🤖)."""
    if not emoji_code:
        return ""
    emoji_code = emoji_code.strip()
    if emoji_code.isdigit():
        return "🔹"
    # Strip HTML tags to get raw text/emoji
    cleaned = re.sub(r'<[^>]+>', '', emoji_code).strip()
    return cleaned



def main_menu(platforms: list[dict], lang: str) -> InlineKeyboardMarkup:
    """Main menu listing all active platforms first, followed by navigation buttons."""
    builder = InlineKeyboardBuilder()
    
    # 1. Add all active platforms (products)
    for p in platforms:
        emoji_code = p.get("custom_emoji_code")
        if emoji_code and emoji_code.strip().isdigit():
            builder.button(
                text=p["name"],
                callback_data=f"platform:{p['id']}",
                icon_custom_emoji_id=emoji_code.strip()
            )
        else:
            emoji_str = clean_emoji_for_button(emoji_code)
            btn_text = f"{emoji_str} {p['name']}".strip() if emoji_str else p["name"]
            builder.button(text=btn_text, callback_data=f"platform:{p['id']}")
    
    # 2. Add other navigation buttons at the end
    builder.button(text=get_text("btn_orders", lang), callback_data="menu:orders")
    builder.button(text=get_text("btn_balance", lang), callback_data="menu:balance")
    builder.button(text=get_text("btn_referral", lang), callback_data="menu:referral")
    builder.button(text=get_text("btn_faq", lang), callback_data="menu:faq")
    builder.button(text=get_text("btn_support", lang), callback_data="menu:support")
    builder.button(text=get_text("btn_language", lang), callback_data="menu:language")
    
    adjust_pattern = [1] * len(platforms) + [2, 2, 2]
    builder.adjust(*adjust_pattern)
    return builder.as_markup()


def language_select() -> InlineKeyboardMarkup:
    """Language selection: Uzbek / Russian."""
    builder = InlineKeyboardBuilder()
    builder.button(text="🇺🇿 O'zbek tili", callback_data="lang:uz")
    builder.button(text="🇷🇺 Русский язык", callback_data="lang:ru")
    builder.adjust(1)
    return builder.as_markup()


def platforms_list(platforms: list[dict], lang: str) -> InlineKeyboardMarkup:
    """Dynamic platform list buttons from DB."""
    builder = InlineKeyboardBuilder()
    for p in platforms:
        emoji_code = p.get("custom_emoji_code")
        if emoji_code and emoji_code.strip().isdigit():
            builder.button(
                text=p["name"],
                callback_data=f"platform:{p['id']}",
                icon_custom_emoji_id=emoji_code.strip()
            )
        else:
            emoji_str = clean_emoji_for_button(emoji_code)
            btn_text = f"{emoji_str} {p['name']}".strip() if emoji_str else p["name"]
            builder.button(text=btn_text, callback_data=f"platform:{p['id']}")
    builder.button(text=get_text("btn_back_to_menu", lang), callback_data="menu:main")
    # Platforms in single column, back button on its own row
    builder.adjust(1)
    return builder.as_markup()


def plans_list(plans: list[dict], platform_id: int, lang: str) -> InlineKeyboardMarkup:
    """Dynamic plan list buttons for a specific platform."""
    builder = InlineKeyboardBuilder()
    for p in plans:
        stock = p.get("stock", 0)
        stock_label = f" ({stock})" if stock > 0 else " (❌)"
        if p.get("plan_type") == "contact_admin":
            builder.button(
                text=f"{p['name']}{stock_label}",
                callback_data=f"plan:{p['id']}",
            )
        else:
            price_label = format_price(p["price_uzs"])
            builder.button(
                text=f"{p['name']} — {price_label} UZS{stock_label}",
                callback_data=f"plan:{p['id']}",
            )
    builder.button(
        text=get_text("btn_back_to_platforms", lang), callback_data="menu:main"
    )
    builder.adjust(1)
    return builder.as_markup()


def plan_detail(plan_id: int, platform_id: int, has_stock: bool, lang: str, plan_type: str = "regular", admin_username: str = "Abdulloh_Zokirov") -> InlineKeyboardMarkup:
    """Plan detail view with Buy / Contact / Back buttons."""
    builder = InlineKeyboardBuilder()
    if plan_type == "contact_admin":
        builder.button(
            text=get_text("btn_contact_admin", lang),
            url=f"https://t.me/{admin_username}"
        )
    elif has_stock:
        builder.button(
            text=get_text("btn_buy", lang), callback_data=f"buy:{plan_id}"
        )
    builder.button(
        text=get_text("btn_back", lang), callback_data=f"platform:{platform_id}"
    )
    builder.button(
        text=get_text("btn_back_to_menu", lang), callback_data="menu:main"
    )
    if plan_type == "contact_admin" or has_stock:
        builder.adjust(1, 2)
    else:
        builder.adjust(1, 1)
    return builder.as_markup()


def payment_methods(
    balance: int, price: int, plan_id: int, lang: str
) -> InlineKeyboardMarkup:
    """Payment method selection: Wallet or Card."""
    builder = InlineKeyboardBuilder()

    # Wallet payment button
    wallet_btn_text = f"{get_text('btn_pay_wallet', lang)} ({format_price(balance)} UZS)"
    builder.button(
        text=wallet_btn_text,
        callback_data=f"pay:wallet:{plan_id}",
    )

    # Card payment button
    builder.button(
        text=get_text("btn_pay_full_card", lang),
        callback_data=f"pay:full_card:{plan_id}",
    )

    builder.button(
        text=get_text("btn_cancel", lang), callback_data="menu:main"
    )
    builder.adjust(1)
    return builder.as_markup()


def wallet_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Keyboard for the Wallet main screen."""
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text("btn_wallet_topup", lang), callback_data="wallet:topup")
    builder.button(text=get_text("btn_wallet_history", lang), callback_data="wallet:history")
    builder.button(text=get_text("btn_back_to_menu", lang), callback_data="menu:main")
    builder.adjust(1)
    return builder.as_markup()


def cancel_order(order_id: int, lang: str) -> InlineKeyboardMarkup:
    """Cancel order button + back to menu."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=get_text("btn_cancel", lang),
        callback_data=f"cancel_order:{order_id}",
    )
    builder.button(
        text=get_text("btn_back_to_menu", lang), callback_data="menu:main"
    )
    builder.adjust(1)
    return builder.as_markup()


def order_list_keyboard(
    orders: list[dict], lang: str
) -> InlineKeyboardMarkup:
    """Order list with cancel buttons for cancellable orders, plus back to menu."""
    builder = InlineKeyboardBuilder()
    for order in orders:
        if order["status"] in ("created", "pending_payment"):
            order_label = get_text("order_cancel_btn", lang).format(
                order_id=order["public_order_id"]
            )
            builder.button(text=order_label, callback_data=f"cancel_order:{order['id']}")
    builder.button(
        text=get_text("btn_back_to_menu", lang), callback_data="menu:main"
    )
    builder.adjust(1)
    return builder.as_markup()


def back_to_menu(lang: str) -> InlineKeyboardMarkup:
    """Single back-to-menu button."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=get_text("btn_back_to_menu", lang), callback_data="menu:main"
    )
    return builder.as_markup()


def back_to_wallet(lang: str) -> InlineKeyboardMarkup:
    """Single back-to-wallet button."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=get_text("btn_back", lang), callback_data="menu:balance"
    )
    return builder.as_markup()


def back_to_platforms(lang: str) -> InlineKeyboardMarkup:
    """Back to platforms list button."""
    builder = InlineKeyboardBuilder()
    builder.button(
        text=get_text("btn_back_to_platforms", lang), callback_data="menu:main"
    )
    builder.button(
        text=get_text("btn_back_to_menu", lang), callback_data="menu:main"
    )
    builder.adjust(1)
    return builder.as_markup()


def points_menu_keyboard(lang: str) -> InlineKeyboardMarkup:
    """Keyboard for the Points & Rewards main screen."""
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text("btn_daily_checkin", lang), callback_data="points:checkin")
    builder.button(text=get_text("btn_rewards_catalog", lang), callback_data="points:catalog")
    builder.button(text=get_text("btn_my_redemptions", lang), callback_data="points:redemptions")
    builder.button(text=get_text("btn_back_to_menu", lang), callback_data="menu:main")
    builder.adjust(1)
    return builder.as_markup()


def rewards_catalog_keyboard(rewards: list[dict], lang: str) -> InlineKeyboardMarkup:
    """List of active rewards to redeem."""
    builder = InlineKeyboardBuilder()
    for r in rewards:
        builder.button(
            text=f"{r['name']} — {r['points_required']} pts",
            callback_data=f"reward:view:{r['id']}"
        )
    builder.button(text=get_text("btn_back_to_points_rewards", lang), callback_data="menu:referral")
    builder.adjust(1)
    return builder.as_markup()


def reward_detail_keyboard(reward_id: int, user_points: int, points_required: int, lang: str) -> InlineKeyboardMarkup:
    """View details of a single reward, with option to redeem if affordable."""
    builder = InlineKeyboardBuilder()
    if user_points >= points_required:
        builder.button(
            text=get_text("btn_redeem", lang),
            callback_data=f"reward:redeem:{reward_id}"
        )
    builder.button(text=get_text("btn_back", lang), callback_data="points:catalog")
    builder.button(text=get_text("btn_back_to_menu", lang), callback_data="menu:main")
    if user_points >= points_required:
        builder.adjust(1, 2)
    else:
        builder.adjust(1)
    return builder.as_markup()


def back_to_points_rewards(lang: str) -> InlineKeyboardMarkup:
    """Back to points & rewards screen."""
    builder = InlineKeyboardBuilder()
    builder.button(text=get_text("btn_back_to_points_rewards", lang), callback_data="menu:referral")
    return builder.as_markup()

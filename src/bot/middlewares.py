"""Middleware: Telegram channel subscription checker."""
import logging
import re
from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.services import settings_service, user_service

logger = logging.getLogger("subhub.bot.middlewares")


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        # 1. Only intercept messages and callback queries
        if not isinstance(event, (Message, CallbackQuery)):
            return await handler(event, data)

        # 2. Check if subscription validation is enabled
        sub_enabled_str = await settings_service.get_setting("sub_check_enabled")
        sub_enabled = (sub_enabled_str == "true" or sub_enabled_str is True)
        if not sub_enabled:
            return await handler(event, data)

        # 3. Check if required channel is set
        channel = await settings_service.get_setting("sub_channel_username")
        if not channel:
            return await handler(event, data)

        # 4. Whitelist start flow & verification callbacks to prevent lockouts
        if isinstance(event, Message):
            text = event.text or ""
            if text.startswith("/start"):
                return await handler(event, data)
        elif isinstance(event, CallbackQuery):
            cb_data = event.data or ""
            if cb_data == "sub_check" or cb_data.startswith("lang:"):
                return await handler(event, data)

        # 5. Retrieve user language and profile
        user_id = event.from_user.id
        user = await user_service.get_user_by_telegram_id(user_id)
        lang = user.get("language_code", "uz") if user else "uz"

        # 6. Format channel ID/username for get_chat_member
        channel_id = channel.strip()
        if "/" in channel_id:
            parts = channel_id.split("/")
            channel_id = "@" + parts[-1]
        elif not channel_id.startswith("@") and not channel_id.startswith("-"):
            channel_id = "@" + channel_id

        # 7. Check subscription membership status
        bot = data["bot"]
        is_subscribed = False
        try:
            member = await bot.get_chat_member(chat_id=channel_id, user_id=user_id)
            if member.status in ["creator", "administrator", "member"] or (member.status == "restricted"):
                is_subscribed = True
        except Exception as e:
            logger.warning(
                f"Failed subscription check for user {user_id} in {channel_id}: {e}"
            )
            # If checking fails, default to blocked (user must subscribe/admin must fix bot rights)
            is_subscribed = False

        if is_subscribed:
            return await handler(event, data)

        # 8. User is not subscribed! Block and prompt them
        custom_msg = await settings_service.get_text("sub_message", lang)
        if not custom_msg:
            if lang == "uz":
                custom_msg = "⚠️ Botdan foydalanish uchun rasmiy kanalimizga a'zo bo'ling."
            else:
                custom_msg = "⚠️ Для использования бота подпишитесь на наш официальный канал."

        # Format subscription link
        link = channel.strip()
        if not link.startswith("http"):
            clean_username = link.replace("@", "")
            link = f"https://t.me/{clean_username}"

        # Build prompt keyboard
        kb_builder = InlineKeyboardBuilder()
        btn_sub_text = "📢 A'zo bo'lish / Подписаться" if lang == "uz" else "📢 Подписаться на канал"
        btn_check_text = "✅ Tekshirish / Проверить" if lang == "uz" else "✅ Проверить подписку"
        
        kb_builder.button(text=btn_sub_text, url=link)
        kb_builder.button(text=btn_check_text, callback_data="sub_check")
        kb_builder.adjust(1)
        kb = kb_builder.as_markup()

        if isinstance(event, Message):
            await event.answer(custom_msg, reply_markup=kb)
        else:
            # For callback queries, update current message layout to show prompt
            try:
                await event.message.edit_text(custom_msg, reply_markup=kb)
            except Exception:
                await event.message.answer(custom_msg, reply_markup=kb)

        return None

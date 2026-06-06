"""Bot initialization — Bot instance, Dispatcher, router registration, start/stop."""
import logging
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from src.config import BOT_TOKEN

logger = logging.getLogger("subhub.bot")

# ── Singleton instances ───────────────────────────────────────
_bot: Bot | None = None
_dp: Dispatcher | None = None


def get_bot() -> Bot:
    """Get the Bot instance (used by admin API for sending notifications)."""
    global _bot
    if _bot is None:
        _bot = Bot(
            token=BOT_TOKEN,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
    return _bot


def get_dispatcher() -> Dispatcher:
    """Get the Dispatcher instance."""
    global _dp
    if _dp is None:
        _dp = Dispatcher()
        _register_routers(_dp)
        _register_middlewares(_dp)
    return _dp


def _register_middlewares(dp: Dispatcher) -> None:
    """Register dispatcher middlewares."""
    from src.bot.middlewares import SubscriptionMiddleware
    dp.message.outer_middleware(SubscriptionMiddleware())
    dp.callback_query.outer_middleware(SubscriptionMiddleware())
    logger.info("Bot middlewares registered")


def _register_routers(dp: Dispatcher) -> None:
    """Register all handler routers in the correct order."""
    from src.bot.handlers.start import router as start_router
    from src.bot.handlers.language import router as language_router
    from src.bot.handlers.menu import router as menu_router
    from src.bot.handlers.products import router as products_router
    from src.bot.handlers.purchase import router as purchase_router
    from src.bot.handlers.orders import router as orders_router
    from src.bot.handlers.balance import router as balance_router
    from src.bot.handlers.support import router as support_router

    dp.include_router(start_router)
    dp.include_router(language_router)
    dp.include_router(balance_router)   # Before purchase — FSM wallet states take priority over broad F.photo handler
    dp.include_router(purchase_router)
    dp.include_router(products_router)
    dp.include_router(orders_router)
    dp.include_router(support_router)
    dp.include_router(menu_router)  # Menu router last — it catches broad menu:* callbacks

    logger.info("All bot handler routers registered")


async def start_bot() -> None:
    """Start the bot polling (blocking coroutine)."""
    bot = get_bot()
    dp = get_dispatcher()

    logger.info("Starting Telegram bot polling...")
    try:
        await dp.start_polling(bot, allowed_updates=["message", "callback_query"])
    except Exception as e:
        logger.error(f"Bot polling error: {e}")
        raise


async def stop_bot() -> None:
    """Gracefully stop the bot."""
    global _bot, _dp
    logger.info("Stopping Telegram bot...")
    dp = get_dispatcher()
    await dp.stop_polling()
    if _bot:
        await _bot.session.close()
        _bot = None
    _dp = None
    logger.info("Telegram bot stopped")

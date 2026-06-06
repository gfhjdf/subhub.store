"""SubHub.store — Main entry point.
Launches FastAPI server + Telegram bot together.
"""
import asyncio
import logging
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware

from src.config import HOST, PORT, UPLOAD_DIR
from src.database.connection import get_db, close_db
from src.database.init_db import init_database

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("subhub")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle."""
    # Startup
    logger.info("🚀 Starting SubHub.store...")
    await init_database()

    # Ensure upload directory exists
    Path(UPLOAD_DIR).mkdir(parents=True, exist_ok=True)

    # Start Telegram bot in background
    from src.bot.bot import start_bot, stop_bot
    bot_task = asyncio.create_task(start_bot())
    logger.info("🤖 Telegram bot started")

    # Start reservation checker in background
    from src.services.order_service import check_and_cancel_expired_orders_loop
    expiration_task = asyncio.create_task(check_and_cancel_expired_orders_loop())
    logger.info("⏰ Reservation expiration checker started (15m timeout)")

    logger.info(f"🌐 Admin panel: http://localhost:{PORT}/admin/")
    logger.info(f"📚 API docs: http://localhost:{PORT}/docs")

    yield

    # Shutdown
    logger.info("🛑 Shutting down...")
    await stop_bot()
    bot_task.cancel()
    expiration_task.cancel()
    await close_db()


app = FastAPI(
    title="SubHub.store API",
    description="Telegram marketplace bot backend + admin panel",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount admin static files
admin_dir = Path(__file__).parent / "admin"
admin_dir.mkdir(parents=True, exist_ok=True)
app.mount("/admin", StaticFiles(directory=str(admin_dir), html=True), name="admin")

# Mount uploads for screenshot access (admin only in production)
uploads_dir = Path(UPLOAD_DIR)
uploads_dir.mkdir(parents=True, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=str(uploads_dir.parent)), name="uploads")

# Register API routes
from src.api.admin_routes import router as admin_router
app.include_router(admin_router)


@app.get("/")
async def root():
    return {"status": "ok", "service": "SubHub.store", "admin": f"/admin/"}


if __name__ == "__main__":
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)

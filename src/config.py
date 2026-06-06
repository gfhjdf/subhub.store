"""Centralized configuration from environment variables."""
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent.parent

# Telegram Bot
BOT_TOKEN = os.getenv("BOT_TOKEN", "")
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

# Server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "3000"))

# JWT
JWT_SECRET = os.getenv("JWT_SECRET", "change-me-in-production")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))

# Default Admin
DEFAULT_ADMIN_USERNAME = os.getenv("DEFAULT_ADMIN_USERNAME", "admin")
DEFAULT_ADMIN_PASSWORD = os.getenv("DEFAULT_ADMIN_PASSWORD", "admin123")

# Database
DB_PATH = BASE_DIR / os.getenv("DB_PATH", "data/subhub.db")

# Uploads
UPLOAD_DIR = BASE_DIR / os.getenv("UPLOAD_DIR", "uploads/screenshots")

# Referral
REFERRAL_REWARD_UZS = int(os.getenv("REFERRAL_REWARD_UZS", "3000"))
SUSPICIOUS_REFERRAL_THRESHOLD = int(os.getenv("SUSPICIOUS_REFERRAL_THRESHOLD", "10"))
SUSPICIOUS_REFERRAL_WINDOW_HOURS = int(os.getenv("SUSPICIOUS_REFERRAL_WINDOW_HOURS", "1"))

# Warranty
WARRANTY_DAYS = int(os.getenv("WARRANTY_DAYS", "7"))

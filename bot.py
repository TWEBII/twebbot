import logging
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
)

# ضع توكن البوت الخاص بك هنا
TOKEN = "YOUR_BOT_TOKEN_HERE"

# إعداد السجلات (Logging)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)

# تخزين أسلوب التحدث لكل مستخدم (اختياري لتخصيص الردود)
user_styles = {}


async def set_bot_commands(application):
    """إعداد قائمة الأوامر التي تظهر في زر القائمة (Menu) للجميع"""
    commands = [
        BotCommand("start", "بداية التشغيل وأقسام البوت"),
        BotCommand("info", "معلوماتي (قنواتي وحسابي)"),
        BotCommand("style", "طريقة تعامل البوت معك"),
    ]
    await application.bot.set_my_commands(commands)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر /start وعرض الأزرار الرئيسية"""
    user_name = update.effective_user.first_name
    keyboard = [
        [InlineKeyboardButton("📢 معلوماتي (قنواتي والحساب)", callback_data="my_info")],
        [InlineKeyboardButton("⚙️ طريقة تعامل البوت معي", callback_data="bot_style")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"أهلاً بك يا {user_name} في بوت الذكاء الاصطناعي الخاص بنا! 🤖\n"
        "اختر أحد الخيارات أدناه من القائمة أو الأزرار:",
        reply_markup=reply_markup,
    )


async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر /info أو زر المعلومات"""
    text = (
        "📌 **معلومات المطور والقنوات:**\n\n"
        "👤 **حساب الشخصي:** @TWEB_1 (أو ضع حسابك هنا)\n"
        "📢 **قناتي الرسمية:** @TWEB_CHANNEL\n"
        "✨ تواصل معنا لأي استفسار أو اقتراح!"
    )
    # إذا تم استدعاؤها عبر زر تفاعلي أو أمر عادي
    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(
            text, parse_mode="Markdown", disable_web_page_preview=True
        )
    else:
        await update.message.reply_text(
            text, parse_mode="Markdown", disable_web_page_preview=True
        )


async def style_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالجة أمر /style أو زر اختيار أسلوب التحدث"""
    keyboard = [
        [InlineKeyboardButton("🤵 رسمي ومحترف", callback_data="style_formal")],
        [InlineKeyboardButton("😄 مضحك وفكاهي", callback_data="style_funny")],
        [InlineKeyboardButton("🤝 ودي وقريب", callback_data="style_friendly")],
        [InlineKeyboardButton("🔙 رجوع للقائمة الرئيسية", callback_data="back_home")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = (
        "🎭 **اختر كيف تريد أن أتحدث معك:**\n"
        "اضغط على الزر المناسب لأسلوبك المفضّل وسأقوم بتعديل طريقة الرد بناءً عليه:"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """التحكم بجميع الضغطات على الأزرار الشفافة"""
    query = update.callback_query
    await query.answer()

    data = query.data
    user_id = query.from_user.id

    if data == "my_info":
        await info_command(update, context)

    elif data == "bot_style":
        await style_command(update, context)

    elif data.startswith("style_"):
        chosen_style = data.split("_")[1]
        user_styles[user_id] = chosen_style

        style_names = {
            "formal": "الرسمي والمحترف 🤵",
            "funny": "المضحك والفكاهي 😄",
            "friendly": "الودي والقريب 🤝",
        }

        current_name = style_names.get(chosen_style, "العادي")
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 العودة للقائمة الرئيسية", callback_data="back_home"
                )
            ]
        ]
        await query.message.edit_text(
            f"✅ تم ضبط أسلوب التحدث معك بنجاح إلى: **{current_name}**.\n"
            "سأقوم بمراعاة هذا الأسلوب في ردودي القادمة معك!",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="Markdown",
        )

    elif data == "back_home":
        user_name = query.from_user.first_name
        keyboard = [
            [
                InlineKeyboardButton(
                    "📢 معلوماتي (قنواتي والحساب)", callback_data="my_info"
                )
            ],
            [
                InlineKeyboardButton(
                    "⚙️ طريقة تعامل البوت معي", callback_data="bot_style"
                )
            ],
        ]
        await query.message.edit_text(
            f"أهلاً بك من جديد يا {user_name}!\nاختر ما تحب:",
            reply_markup=InlineKeyboardMarkup(keyboard),
        )


def main():
    # بناء تطبيق البوت
    application = ApplicationBuilder().token(TOKEN).build()

    # تسجيل الأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("info", info_command))
    application.add_handler(CommandHandler("style", style_command))

    # تسجيل مستقبل الضغط على الأزرار
    application.add_handler(CallbackQueryHandler(button_handler))

    # تعيين الأوامر لتظهر في زر القائمة تلقائياً عند التشغيل
    application.job_queue.run_once(
        lambda ctx: application.create_task(set_bot_commands(application)), 1
    )

    print("🤖 البوت يعمل الآن بنجاح...")
    application.run_polling()


if __name__ == "__main__":
    main()

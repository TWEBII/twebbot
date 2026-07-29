from ai import ask_ai
from database import db
from config import ADMIN_ID
from keyboards import main_menu, admin_menu


def register_handlers(bot):

    @bot.message_handler(commands=["start"])
    def start(message):

        db.add_user(message.from_user)

        is_admin = message.from_user.id == ADMIN_ID

        text = (
            "👋 أهلاً بك في Tweby AI\n\n"
            "🤖 أنا مساعد ذكي يعمل بواسطة الذكاء الاصطناعي.\n"
            "اختر أحد الخيارات من القائمة بالأسفل."
        )

        bot.send_message(
            message.chat.id,
            text,
            reply_markup=main_menu(is_admin)
        )


    @bot.message_handler(commands=["help"])
    def help_cmd(message):

        bot.reply_to(
            message,
            "📌 أرسل أي سؤال وسأجيبك بالذكاء الاصطناعي."
        )


    @bot.message_handler(commands=["stats"])
    def stats(message):

        if message.from_user.id != ADMIN_ID:
            return

        users = db.total_users()
        msgs = db.get_stat("messages")

        bot.reply_to(
            message,
            f"👥 المستخدمون: {users}\n💬 الرسائل: {msgs}"
        )


    # لوحة تحكم المطور
    @bot.message_handler(func=lambda m: m.text == "👑 لوحة التحكم")
    def admin_panel(message):

        if message.from_user.id != ADMIN_ID:
            return

        bot.send_message(
            message.chat.id,
            "👑 مرحباً أحمد\n\nاختر العملية التي تريدها:",
            reply_markup=admin_menu()
        )


    # زر المطور
    @bot.message_handler(func=lambda m: m.text == "👨‍💻 المطور")
    def developer(message):

        bot.send_message(
            message.chat.id,
            "👨‍💻 مطور البوت: أحمد\n\n"
            "Tweby AI"
        )


    # زر المساعدة
    @bot.message_handler(func=lambda m: m.text == "ℹ️ المساعدة")
    def help_button(message):

        bot.send_message(
            message.chat.id,
            "💡 أرسل أي رسالة وسأحاول مساعدتك."
        )


    # زر الدردشة الذكية
    @bot.message_handler(func=lambda m: m.text == "🤖 الدردشة الذكية")
    def ai_chat_button(message):

        bot.send_message(
            message.chat.id,
            "🤖 أرسل سؤالك الآن."
        )


    # استقبال الرسائل والرد بالذكاء الاصطناعي
    @bot.message_handler(content_types=["text"])
    def chat(message):

        db.add_user(message.from_user)

        if message.text.startswith("/"):
            return


        # تجاهل أزرار التحكم
        buttons = [
            "👑 لوحة التحكم",
            "👨‍💻 المطور",
            "ℹ️ المساعدة",
            "🤖 الدردشة الذكية",
            "⚙️ الإعدادات",
            "📜 سجل المحادثات"
        ]

        if message.text in buttons:
            return


        # المجموعات
        if message.chat.type != "private":

            reply = False
            mention = False

            if message.reply_to_message:

                if message.reply_to_message.from_user.id == bot.get_me().id:
                    reply = True

            me = bot.get_me()

            if me.username:

                if "@" + me.username.lower() in message.text.lower():
                    mention = True

            if not reply and not mention:
                return


        wait = bot.reply_to(
            message,
            "⏳ جاري التفكير..."
        )


        try:

            answer = ask_ai(
                message.from_user,
                message.text
            )

            bot.edit_message_text(
                answer,
                chat_id=message.chat.id,
                message_id=wait.message_id
            )


        except Exception as e:

            print(e)

            bot.edit_message_text(
                "❌ حدث خطأ أثناء معالجة الطلب.",
                chat_id=message.chat.id,
                message_id=wait.message_id
            )

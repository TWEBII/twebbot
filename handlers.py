import telebot

from ai import ask_ai
from database import db
from config import ADMIN_ID


def register_handlers(bot):

    @bot.message_handler(commands=["start"])
    def start(message):

        db.add_user(message.from_user)

        text = (
            "👋 أهلاً بك في Tweby AI\n\n"
            "أنا مساعد ذكي يعمل بواسطة Groq.\n"
            "أرسل أي سؤال وسأجيبك."
        )

        bot.reply_to(message, text)

    @bot.message_handler(commands=["help"])
    def help_cmd(message):

        bot.reply_to(
            message,
            "أرسل أي رسالة وسأجيب عنها."
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

    @bot.message_handler(content_types=["text"])
    def chat(message):

        db.add_user(message.from_user)

        if message.text.startswith("/"):
            return

        # لا يرد في المجموعات إلا عند الرد على البوت أو منشن
        if message.chat.type != "private":

            reply = False
            mention = False

            if message.reply_to_message:

                if message.reply_to_message.from_user.id == bot.get_me().id:
                    reply = True

            me = bot.get_me()

            if me.username:

                if "@"+me.username.lower() in message.text.lower():
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
                "❌ حدث خطأ.",
                chat_id=message.chat.id,
                message_id=wait.message_id
            )

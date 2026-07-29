import sqlite3
from threading import Lock

DB_NAME = "data/bot.db"

lock = Lock()


class Database:

    def __init__(self):
        self.conn = sqlite3.connect(DB_NAME, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            first_name TEXT,
            username TEXT,
            joined_at TEXT
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS messages(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            role TEXT,
            content TEXT,
            created_at TEXT
        )
        """)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS stats(
            key TEXT PRIMARY KEY,
            value INTEGER
        )
        """)

        self.conn.commit()

    # =======================
    # المستخدمين
    # =======================

    def add_user(self, user):

        with lock:

            self.cursor.execute("""
            INSERT OR IGNORE INTO users
            VALUES(?,?,?,datetime('now'))
            """,
            (
                user.id,
                user.first_name,
                user.username
            ))

            self.conn.commit()

    def total_users(self):

        self.cursor.execute(
            "SELECT COUNT(*) FROM users"
        )

        return self.cursor.fetchone()[0]

    def get_users(self):

        self.cursor.execute(
            "SELECT user_id FROM users"
        )

        return [x[0] for x in self.cursor.fetchall()]

    # =======================
    # المحادثات
    # =======================

    def save_message(self,
                     user_id,
                     role,
                     content):

        with lock:

            self.cursor.execute("""
            INSERT INTO messages(
                user_id,
                role,
                content,
                created_at
            )

            VALUES(
                ?,
                ?,
                ?,
                datetime('now')
            )

            """,
            (
                user_id,
                role,
                content
            ))

            self.conn.commit()

    def get_history(
            self,
            user_id,
            limit=10):

        self.cursor.execute("""

        SELECT role,content

        FROM messages

        WHERE user_id=?

        ORDER BY id DESC

        LIMIT ?

        """,
        (
            user_id,
            limit
        ))

        rows = self.cursor.fetchall()

        rows.reverse()

        history = []

        for role, content in rows:

            history.append({
                "role": role,
                "content": content
            })

        return history

    # =======================
    # الإحصائيات
    # =======================

    def increase(self, key):

        self.cursor.execute("""
        INSERT INTO stats(key,value)

        VALUES(?,1)

        ON CONFLICT(key)

        DO UPDATE SET

        value=value+1
        """, (key,))

        self.conn.commit()

    def get_stat(self, key):

        self.cursor.execute(
            "SELECT value FROM stats WHERE key=?",
            (key,)
        )

        row = self.cursor.fetchone()

        if row:
            return row[0]

        return 0


db = Database()
from groq import Groq
from config import GROQ_API_KEY, MODEL_NAME, TEMPERATURE
from database import db

client = Groq(api_key=GROQ_API_KEY)


SYSTEM_PROMPT = """
أنت مساعد ذكي اسمك Tweby.

- تتحدث بالعربية بطلاقة.
- إذا خاطبك المستخدم باللهجة العراقية يمكنك الرد باللهجة العراقية.
- أجب باختصار إلا إذا طلب المستخدم شرحًا.
- لا تقل أنك مجرد نموذج إلا إذا سُئلت مباشرة.
- كن مهذبًا واحترافيًا.
"""


def ask_ai(user, text):

    history = db.get_history(user.id)

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    messages.extend(history)

    messages.append({
        "role": "user",
        "content": text
    })

    try:

        response = client.chat.completions.create(

            model=MODEL_NAME,

            messages=messages,

            temperature=TEMPERATURE

        )

        answer = response.choices[0].message.content.strip()

        db.save_message(
            user.id,
            "user",
            text
        )

        db.save_message(
            user.id,
            "assistant",
            answer
        )

        db.increase("messages")

        return answer

    except Exception as e:

        print(e)

        return "حدث خطأ أثناء الاتصال بالذكاء الاصطناعي."
import telebot

from config import ADMIN_ID
from database import db
from ai import ask_ai


def register_handlers(bot):

    # ===========================
    # START
    # ===========================

    @bot.message_handler(commands=["start"])
    def start(message):

        db.add_user(message.from_user)

        text = (
            "👋 أهلاً بك في Tweby AI\n\n"
            "أنا مساعد ذكي يعمل بواسطة Groq.\n"
            "أرسل أي سؤال وسأجيبك مباشرة."
        )

        bot.reply_to(message, text)

    # ===========================
    # HELP
    # ===========================

    @bot.message_handler(commands=["help"])
    def help_command(message):

        bot.reply_to(
            message,
            "أرسل أي رسالة وسأجيب عنها باستخدام الذكاء الاصطناعي."
        )

    # ===========================
    # STATS
    # ===========================

    @bot.message_handler(commands=["stats"])
    def stats(message):

        if message.from_user.id != ADMIN_ID:
            return

        users = db.total_users()

        msgs = db.get_stat("messages")

        text = f"""
📊 الإحصائيات

👥 المستخدمون:
{users}

💬 الرسائل:
{msgs}
"""

        bot.reply_to(message, text)

    # ===========================
    # AI
    # ===========================

    @bot.message_handler(content_types=["text"])
    def chat(message):

        db.add_user(message.from_user)

        # تجاهل أوامر أخرى

        if message.text.startswith("/"):
            return

        # بالمجموعات

        if message.chat.type != "private":

            is_reply = False

            if message.reply_to_message:

                if message.reply_to_message.from_user.id == bot.get_me().id:

                    is_reply = True

            mention = False

            txt = message.text.lower()

            me = bot.get_me()

            if me.username:

                if "@"+me.username.lower() in txt:

                    mention = True

            if not is_reply and not mention:

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

        except Exception:

            bot.edit_message_text(

                "❌ حدث خطأ أثناء إنشاء الرد.",

                chat_id=message.chat.id,

                message_id=wait.message_id

            )
       from telebot import types

from config import ADMIN_ID
from database import db


broadcast_mode = {}

start_message = (
    "👋 أهلاً بك في Tweby AI\n\n"
    "أنا مساعد ذكي يعمل بواسطة Groq."
)


def register_admin(bot):

    @bot.message_handler(commands=["admin"])
    def admin(message):

        if message.from_user.id != ADMIN_ID:
            return

        keyboard = types.InlineKeyboardMarkup(row_width=2)

        keyboard.add(
            types.InlineKeyboardButton(
                "📊 الإحصائيات",
                callback_data="stats"
            ),
            types.InlineKeyboardButton(
                "📢 إذاعة",
                callback_data="broadcast"
            )
        )

        keyboard.add(
            types.InlineKeyboardButton(
                "✏️ رسالة البدء",
                callback_data="startmsg"
            )
        )

        bot.send_message(
            message.chat.id,
            "لوحة التحكم",
            reply_markup=keyboard
        )

    @bot.callback_query_handler(func=lambda c: True)
    def callback(call):

        global start_message

        if call.from_user.id != ADMIN_ID:
            return

        if call.data == "stats":

            users = db.total_users()

            msgs = db.get_stat("messages")

            text = f"""
👥 المستخدمون

{users}

💬 الرسائل

{msgs}
"""

            bot.edit_message_text(
                text,
                call.message.chat.id,
                call.message.message_id,
                reply_markup=call.message.reply_markup
            )

        elif call.data == "broadcast":

            broadcast_mode[
                call.from_user.id
            ] = True

            bot.send_message(
                call.message.chat.id,
                "📢 أرسل رسالة الإذاعة الآن."
            )

        elif call.data == "startmsg":

            broadcast_mode[
                call.from_user.id
            ] = "start"

            bot.send_message(
                call.message.chat.id,
                "✏️ أرسل رسالة البدء الجديدة."
            )

    @bot.message_handler(func=lambda m: m.from_user.id == ADMIN_ID)
    def admin_steps(message):

        global start_message

        if message.from_user.id not in broadcast_mode:
            return

        mode = broadcast_mode.pop(
            message.from_user.id
        )

        if mode == True:

            ok = 0

            fail = 0

            for user in db.get_users():

                try:

                    bot.copy_message(
                        user,
                        message.chat.id,
                        message.message_id
                    )

                    ok += 1

                except:

                    fail += 1

            bot.send_message(

                ADMIN_ID,

                f"""✅ انتهت الإذاعة

تم الإرسال:
{ok}

فشل:
{fail}
"""

            )

        elif mode == "start":

            start_message = message.text

            bot.send_message(

                ADMIN_ID,

                "✅ تم تغيير رسالة البدء."

            )
from database import db

broadcast_waiting = set()


def register_broadcast(bot, ADMIN_ID):

    @bot.message_handler(commands=["broadcast"])
    def broadcast(message):

        if message.from_user.id != ADMIN_ID:
            return

        broadcast_waiting.add(message.from_user.id)

        bot.reply_to(
            message,
            "📢 أرسل الرسالة التي تريد إرسالها لجميع المستخدمين."
        )

    @bot.message_handler(
        func=lambda m: m.from_user.id in broadcast_waiting,
        content_types=[
            "text",
            "photo",
            "video",
            "document",
            "sticker",
            "audio",
            "voice"
        ]
    )
    def send_broadcast(message):

        broadcast_waiting.remove(message.from_user.id)

        users = db.get_users()

        success = 0
        failed = 0

        progress = bot.send_message(
            message.chat.id,
            "⏳ جاري الإرسال..."
        )

        for uid in users:

            try:

                bot.copy_message(
                    chat_id=uid,
                    from_chat_id=message.chat.id,
                    message_id=message.message_id
                )

                success += 1

            except Exception:
                failed += 1

        bot.edit_message_text(

            f"""✅ انتهت الإذاعة

👥 عدد المستخدمين:
{len(users)}

📨 تم الإرسال:
{success}

❌ فشل:
{failed}
""",

            chat_id=message.chat.id,

            message_id=progress.message_id

        )
        import random

stickers = []


def load_stickers(bot, packs):

    global stickers

    stickers.clear()

    for pack in packs:

        try:

            s = bot.get_sticker_set(pack)

            for sticker in s.stickers:

                stickers.append(
                    sticker.file_id
                )

        except Exception as e:

            print(e)

    print(
        f"Loaded {len(stickers)} stickers."
    )


def send_random(bot, chat_id):

    if not stickers:
        return

    bot.send_sticker(

        chat_id,

        random.choice(stickers)

    )from datetime import datetime, timedelta


def iraq_time():

    return datetime.utcnow() + timedelta(hours=3)


def now():

    return iraq_time().strftime("%Y-%m-%d %H:%M:%S")


def safe_markdown(text: str):

    chars = [
        "_",
        "*",
        "[",
        "]",
        "(",
        ")",
        "~",
        "`",
        ">",
        "#",
        "+",
        "-",
        "=",
        "|",
        "{",
        "}",
        ".",
        "!"
    ]

    for c in chars:
        text = text.replace(c, "\\" + c)

    return text
import telebot

from config import (
    BOT_TOKEN,
    STICKER_PACKS,
    ADMIN_ID
)

from handlers import register_handlers
from admin import register_admin
from broadcast import register_broadcast
from stickers import load_stickers

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="Markdown"
)

register_handlers(bot)

register_admin(bot)

register_broadcast(
    bot,
    ADMIN_ID
)

load_stickers(
    bot,
    STICKER_PACKS
)

print("================================")
print(" Tweby AI Started Successfully ")
print("================================")

bot.remove_webhook()

bot.infinity_polling(
    timeout=60,
    long_polling_timeout=60,
    skip_pending=True
)

import os
import sys
import time
import sqlite3
import telebot
from telebot import types
from groq import Groq

# قراءة المتغيرات من البيئة (Railway Variables)
BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
BOT_NAME = "TWEB"

if not BOT_TOKEN:
    print("خطأ: يرجى تعيين متغير BOT_TOKEN في لوحة تحكم Railway.")
    sys.exit(1)

# تهيئة البوت وخدمة الذكاء الاصطناعي
bot = telebot.TeleBot(BOT_TOKEN)
client = Groq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

# --- 1. إعدادات قاعدة البيانات (SQLite) ---
DB_NAME = "bot_database.db"

def initialize_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id, username):
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("INSERT OR IGNORE INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
        conn.commit()
        conn.close()
    except:
        pass

def get_users_count():
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM users")
        count = cursor.fetchone()[0]
        conn.close()
        return count
    except:
        return 0

# --- 2. محرك الذكاء الاصطناعي (Groq - النموذج الجديد المحدث) ---
def generate_ai_response(user_text):
    if not client:
        return "عذراً، مفتاح الذكاء الاصطناعي (GROQ_API_KEY) غير محدد في المتغيرات."
    try:
        system_instruction = (
            f"أنت مساعد ذكي ومحترف جداً تدعى {BOT_NAME}. "
            "مهمتك الأساسية هي الإجابة بدقة عالية جداً وتقديم إجابات منطقية، علمية، ومؤكدة بنسبة 100%. "
            "تحدث باللغة العربية بأسلوب واضح ومفهوم ومباشر."
        )
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_text}
            ],
            model="llama-3.1-8b-instant",  # النموذج الجديد النشط 100%
            temperature=0.2, 
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"عذراً، حدث خطأ أثناء معالجة الطلب: {e}"

# --- 3. معالجات الأوامر والأزرار (Handlers) ---
def register_handlers(bot_instance):
    
    @bot_instance.message_handler(commands=['start'])
    def send_welcome(message):
        user_id = message.from_user.id
        username = message.from_user.username or "No Username"
        add_user(user_id, username)
        
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
        btn1 = types.KeyboardButton("📊 الإحصائيات")
        btn2 = types.KeyboardButton("📢 إذاعة")
        btn3 = types.KeyboardButton("🛠 معلومات البوت")
        markup.add(btn1, btn2, btn3)
        
        welcome_text = (
            f"أهلاً بك يا مطوري ✍️\n"
            f"أنا بوت {BOT_NAME} تحت خدمتك.\n"
            f"هذه لوحة التحكم الخاصة بك:"
        )
        bot_instance.reply_to(message, welcome_text, reply_markup=markup)

    @bot_instance.message_handler(func=lambda message: True)
    def handle_all_messages(message):
        text = message.text
        
        if text == "📊 الإحصائيات":
            count = get_users_count()
            bot_instance.reply_to(message, f"📊 عدد المستخدمين الكلي في البوت: {count} مشتركاً.")
        elif text == "📢 إذاعة":
            bot_instance.reply_to(message, "ميزة الإذاعة جاهزة، أرسل النص المراد إذاعته.")
        elif text == "🛠 معلومات البوت":
            bot_instance.reply_to(message, f"البوت يعمل بملف واحد متكامل ومربوط بالذكاء الاصطناعي بنجاح ✅")
        else:
            ai_reply = generate_ai_response(text)
            bot_instance.reply_to(message, ai_reply)

# --- 4. التشغيل الرئيسي وحماية الاتصال (Main Loop) ---
def main():
    print(f"جاري تشغيل بوت {BOT_NAME}...")
    
    initialize_db()
    print("تم تهيئة قاعدة البيانات بنجاح ✅")
    
    register_handlers(bot)
    print("تم ربط الأوامر والردود بنجاح ✅")
    
    time.sleep(3)
    
    try:
        bot.remove_webhook()
        print("تم إزالة الـ Webhook القديم بنجاح ✅")
    except Exception as e:
        print(f"ملاحظة: {e}")
        
    print("البوت يعمل الآن بثبات تام!")
    
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=20, skip_pending=True)
        except Exception as e:
            print(f"خطأ في الاتصال: {e}")
            print("إعادة المحاولة خلال 5 ثوانٍ...")
            time.sleep(5)

if __name__ == "__main__":
    main()

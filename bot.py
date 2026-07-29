import telebot
import os
import json
import random
import datetime
import pytz
from groq import Groq
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

# ================= الإعدادات الأساسية =================
TOKEN = "8898698558:AAFjuVht_Qq1DD_-1nRIB1YT6U-VWPnwtFM"
GROQ_API_KEY = "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"
ADMIN_ID = "8411608232"

bot = telebot.TeleBot(TOKEN)
groq_client = Groq(api_key=GROQ_API_KEY)

# ملف قاعدة البيانات البسيطة لحفظ الإعدادات والمستخدمين
DB_FILE = "database.json"

# حزم الملصقات
STICKER_SETS = [
    "Adhkar_by_maker_Sticker_bot", "Stillness_by_maker_Sticker_bot",
    "Childrennnn_by_maker_Sticker_bot", "Moneyme_by_maker_Sticker_bot",
    "yourose_by_maker_Sticker_bot", "Myrefuge_by_maker_Sticker_bot",
    "Funnyye_by_maker_Sticker_bot", "Life_by_maker_Sticker_bot"
]

# ================= دوال قاعدة البيانات =================
def load_db():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"users": [], "support_active": False}

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

# ================= دوال مساعدة =================
def send_random_sticker(chat_id):
    try:
        set_name = random.choice(STICKER_SETS)
        sticker_set = bot.get_sticker_set(set_name)
        if sticker_set.stickers:
            sticker = random.choice(sticker_set.stickers)
            bot.send_sticker(chat_id, sticker.file_id)
    except Exception as e:
        print(f"Sticker Error: {e}")

def get_ai_reply(user_message):
    # جلب الوقت والتاريخ في العراق
    tz = pytz.timezone('Asia/Baghdad')
    iraq_time = datetime.datetime.now(tz).strftime('%Y-%m-%d %I:%M:%S %p')
    
    system_prompt = f"أنت مساعد ذكي ومفيد جداً. الوقت والتاريخ الحالي في العراق هو: {iraq_time}. أجب عن استفسارات المستخدم بدقة عالية باللغة العربية، وكن مباشراً وواضحاً."
    
    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            model="llama3-70b-8192", 
        )
        return response.choices[0].message.content
    except Exception as e:
        return "عذراً، أواجه مشكلة في الاتصال بالخادم حالياً. يرجى المحاولة لاحقاً."

def get_admin_keyboard():
    markup = InlineKeyboardMarkup()
    # الصف الأول
    markup.row(InlineKeyboardButton("المحتوى 📝", callback_data="content"), 
               InlineKeyboardButton("الإعدادات ⚙️", callback_data="settings"))
    # الصف الثاني
    markup.row(InlineKeyboardButton("الاشتراك 🔐", callback_data="subscribe"), 
               InlineKeyboardButton("المستخدمون 👥", callback_data="users_count"))
    # الصف الثالث
    markup.row(InlineKeyboardButton("المالية 💰", callback_data="finance"), 
               InlineKeyboardButton("التواصل 📣", callback_data="broadcast"))
    # الصف الرابع
    markup.row(InlineKeyboardButton("النظام والدعم 🛠", callback_data="toggle_support"))
    # الصف الخامس
    markup.row(InlineKeyboardButton("إشعار الحظر 🚫", callback_data="notice_ban"), 
               InlineKeyboardButton("إشعار الدخول ✅", callback_data="notice_login"))
    # الصف السادس
    markup.row(InlineKeyboardButton("دليل الاستخدام ❓", callback_data="guide"))
    # الصف السابع
    markup.row(InlineKeyboardButton("لوحه تحكم الصانع", callback_data="maker_panel"))
    return markup

# ================= التوجيهات والأوامر =================

@bot.message_handler(commands=['start'])
def start_command(message):
    db = load_db()
    user_id = message.chat.id
    
    # تسجيل المستخدم إذا كان جديداً
    if user_id not in db["users"]:
        db["users"].append(user_id)
        save_db(db)

    # التحقق مما إذا كان المستخدم هو المطور
    if str(user_id) == ADMIN_ID:
        stats_text = (
            "• لوحة التحكم 🤖\n\n"
            "—— إحصائيات اليوم ——\n"
            f"👥 الإجمالي: {len(db['users'])}\n"
            "📈 الرسائل: نشط\n"
            "⚡️ متوسط الاستجابة: سريع\n"
        )
        bot.send_message(user_id, stats_text, reply_markup=get_admin_keyboard())
    else:
        # واجهة المستخدم العادي
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        if db.get("support_active"):
            markup.add(KeyboardButton("📞 التواصل مع الدعم"))
        else:
            markup = ReplyKeyboardRemove()
            
        send_random_sticker(user_id)
        bot.reply_to(message, "مرحباً بك! أنا بوت ذكاء اصطناعي، كيف يمكنني مساعدتك اليوم؟", reply_markup=markup)

# ================= التحكم بأزرار المطور (Callback) =================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if str(call.message.chat.id) != ADMIN_ID:
        return

    db = load_db()
    
    if call.data == "users_count":
        bot.answer_callback_query(call.id, f"عدد المستخدمين الكلي: {len(db['users'])}", show_alert=True)
        
    elif call.data == "broadcast":
        msg = bot.send_message(call.message.chat.id, "حسنًا، أرسل رسالة الإذاعة الآن:")
        bot.register_next_step_handler(msg, process_broadcast)
        
    elif call.data == "toggle_support":
        db["support_active"] = not db.get("support_active", False)
        save_db(db)
        status = "مفعل ✅" if db["support_active"] else "معطل ❌"
        bot.answer_callback_query(call.id, f"تم تغيير حالة الدعم بنجاح! الحالة الآن: {status}", show_alert=True)
        
    else:
        # لبقية الأزرار كشكل حالي
        bot.answer_callback_query(call.id, "هذا الزر قيد التطوير والإعداد...")

def process_broadcast(message):
    db = load_db()
    success_count = 0
    bot.reply_to(message, "جاري بدء الإذاعة...")
    for user_id in db["users"]:
        try:
            bot.copy_message(user_id, message.chat.id, message.message_id)
            success_count += 1
        except Exception:
            pass
    bot.send_message(message.chat.id, f"تمت الإذاعة بنجاح لـ {success_count} مستخدم.")

# ================= معالجة الرسائل والدعم الفني =================
@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    db = load_db()
    user_id = message.chat.id

    # أوامر خاصة بالمطور للرد على طلبات الدعم
    if str(user_id) == ADMIN_ID and message.text.startswith('/reply'):
        try:
            parts = message.text.split(' ', 2)
            target_user = parts[1]
            reply_text = parts[2]
            bot.send_message(target_user, f"رسالة من المطور:\n\n{reply_text}")
            bot.reply_to(message, "تم إرسال ردك للمستخدم بنجاح.")
        except:
            bot.reply_to(message, "صيغة الرد خاطئة! استخدم:\n`/reply USER_ID text`", parse_mode="Markdown")
        return

    # تفاعل المستخدم مع زر الدعم
    if message.text == "📞 التواصل مع الدعم" and db.get("support_active"):
        msg = bot.reply_to(message, "أرسل رسالتك أو مشكلتك الآن، وسأقوم بإرسالها للمطور مباشرة:")
        bot.register_next_step_handler(msg, forward_to_admin)
        return

    # إذا لم يكن أمراً خاصاً، الرد بالذكاء الاصطناعي
    bot.send_chat_action(user_id, 'typing')
    ai_response = get_ai_reply(message.text)
    
    # إرسال ملصق عشوائي في بعض الأحيان مع المحادثة لإضافة طابع حيوي (فرصة 30%)
    if random.random() < 0.3:
        send_random_sticker(user_id)
        
    bot.reply_to(message, ai_response)

def forward_to_admin(message):
    user_id = message.chat.id
    username = f"@{message.from_user.username}" if message.from_user.username else "بدون يوزر"
    
    # إرسال للمطور
    bot.send_message(
        ADMIN_ID, 
        f"📩 **رسالة دعم جديدة**\n\n"
        f"👤 الأيدي: `{user_id}`\n"
        f"🔗 اليوزر: {username}\n\n"
        f"الرسالة: {message.text}\n\n"
        f"للرد عليه انسخ الأمر التالي:\n"
        f"`/reply {user_id} رسالتك_هنا`",
        parse_mode="Markdown"
    )
    bot.reply_to(message, "تم استلام رسالتك وتوجيهها للمطور. سيتم الرد عليك قريباً.")

# ================= تشغيل البوت =================
print("تم تشغيل البوت بنجاح...")
bot.infinity_polling()

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

DB_FILE = "database.json"

# حزم الملصقات المطلوبة
STICKER_SETS = [
    "Adhkar_by_maker_Sticker_bot", "Stillness_by_maker_Sticker_bot",
    "Childrennnn_by_maker_Sticker_bot", "Moneyme_by_maker_Sticker_bot",
    "yourose_by_maker_Sticker_bot", "Myrefuge_by_maker_Sticker_bot",
    "Funnyye_by_maker_Sticker_bot", "Life_by_maker_Sticker_bot"
]

# ================= دوال قاعدة البيانات =================
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
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
    # جلب التوقيت والتاريخ الفعلي في العراق بدقة تامة
    tz = pytz.timezone('Asia/Baghdad')
    iraq_time = datetime.datetime.now(tz).strftime('%Y-%m-%d %I:%M:%S %p')
    
    system_prompt = f"أنت مساعد ذكي ومفيد جداً. الوقت والتاريخ الحالي في العراق هو: {iraq_time}. أجب عن استفسارات المستخدم بدقة عالية باللغة العربية، وكن مباشراً وواضحاً."
    
    try:
        # استخدام الموديل الأحدث والأكثر استقراراً لتفادي أخطاء التوقف
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            model="llama-3.3-70b-versatile", 
        )
        return response.choices[0].message.content
    except Exception as e:
        # طباعة الخطأ في سجلات Railway لمعرفته فوراً عند حدوثه
        print(f"❌ Groq API Error: {e}")
        return "عذراً، أواجه مشكلة في الاتصال بالخادم حالياً. يرجى المحاولة لاحقاً."

def get_admin_keyboard():
    markup = InlineKeyboardMarkup()
    # تصميم الأزرار الشفافة مطابقة للصورة تماماً
    markup.row(InlineKeyboardButton("المحتوى 📝", callback_data="content"), 
               InlineKeyboardButton("الإعدادات ⚙️", callback_data="settings"))
    markup.row(InlineKeyboardButton("الاشتراك 🔐", callback_data="subscribe"), 
               InlineKeyboardButton("المستخدمون 👥", callback_data="users_count"))
    markup.row(InlineKeyboardButton("المالية 💰", callback_data="finance"), 
               InlineKeyboardButton("التواصل 📣", callback_data="broadcast"))
    markup.row(InlineKeyboardButton("النظام والدعم 🛠", callback_data="toggle_support"))
    markup.row(InlineKeyboardButton("إشعار الحظر 🚫", callback_data="notice_ban"), 
               InlineKeyboardButton("إشعار الدخول ✅", callback_data="notice_login"))
    markup.row(InlineKeyboardButton("دليل الاستخدام ❓", callback_data="guide"))
    markup.row(InlineKeyboardButton("لوحه تحكم الصانع", callback_data="maker_panel"))
    return markup

# ================= تفتيش التفاعلات والأوامر =================
@bot.message_handler(commands=['start'])
def start_command(message):
    db = load_db()
    user_id = message.chat.id
    
    if user_id not in db["users"]:
        db["users"].append(user_id)
        save_db(db)

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
        # تخصيص قائمة العميل حسب حالة تفعيل أو إغلاق الدعم من قبلك
        markup = ReplyKeyboardMarkup(resize_keyboard=True)
        if db.get("support_active", False):
            markup.add(KeyboardButton("📞 التواصل مع الدعم"))
        else:
            markup = ReplyKeyboardRemove()
            
        send_random_sticker(user_id)
        bot.reply_to(message, "مرحباً بك! أنا بوت ذكاء اصطناعي، كيف يمكنني مساعدتك اليوم؟", reply_markup=markup)

# ================= الأزرار الشفافة التفاعلية =================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if str(call.message.chat.id) != ADMIN_ID:
        return

    db = load_db()
    
    if call.data == "users_count":
        bot.answer_callback_query(call.id, f"عدد المستخدمين الكلي: {len(db['users'])}", show_alert=True)
    elif call.data == "broadcast":
        msg = bot.send_message(call.message.chat.id, "حسنًا، أرسل رسالة الإذاعة الآن للجميع:")
        bot.register_next_step_handler(msg, process_broadcast)
    elif call.data == "toggle_support":
        db["support_active"] = not db.get("support_active", False)
        save_db(db)
        status = "مفعل ومتاح للمستخدمين ✅" if db["support_active"] else "مغلق ومخفي عن المستخدمين ❌"
        bot.answer_callback_query(call.id, f"تم تحديث حالة الدعم: {status}", show_alert=True)
    else:
        bot.answer_callback_query(call.id, "هذا الزر قيد التطوير والإعداد...")

def process_broadcast(message):
    db = load_db()
    success_count = 0
    bot.reply_to(message, "جاري بدء الإذاعة ونشر المحتوى...")
    for user_id in db["users"]:
        try:
            bot.copy_message(user_id, message.chat.id, message.message_id)
            success_count += 1
        except:
            pass
    bot.send_message(message.chat.id, f"تمت الإذاعة بنجاح لـ {success_count} مستخدم.")

# ================= استقبال الرسائل والردود =================
@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    db = load_db()
    user_id = message.chat.id

    # تحكم المطور بالردود على رسائل الدعم الفني
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

    # معالجة طلب الدعم من العميل
    if message.text == "📞 التواصل مع الدعم" and db.get("support_active", False):
        msg = bot.reply_to(message, "أرسل رسالتك أو مشكلتك الآن، وسأقوم بإرسالها للمطور مباشرة:")
        bot.register_next_step_handler(msg, forward_to_admin)
        return

    # الرد عبر الذكاء الاصطناعي
    bot.send_chat_action(user_id, 'typing')
    ai_response = get_ai_reply(message.text)
    
    # فرصة عشوائية لإرسال ملصق من الحزم أثناء المحادثة (30%)
    if random.random() < 0.3:
        send_random_sticker(user_id)
        
    bot.reply_to(message, ai_response)

def forward_to_admin(message):
    user_id = message.chat.id
    username = f"@{message.from_user.username}" if message.from_user.username else "بدون يوزر"
    bot.send_message(
        ADMIN_ID, 
        f"📩 **رسالة دعم جديدة**\n\n👤 الأيدي: `{user_id}`\n🔗 اليوزر: {username}\n\nالرسالة: {message.text}\n\nللرد عليه انسخ الأمر التالي:\n`/reply {user_id} رسالتك_هنا`",
        parse_mode="Markdown"
    )
    bot.reply_to(message, "تم استلام رسالتك وتوجيهها للمطور. سيتم الرد عليك قريباً.")

# ================= بدء التشغيل =================
print("...تم تشغيل البوت بنجاح")
bot.infinity_polling()

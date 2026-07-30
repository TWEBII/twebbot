import telebot
import os
import json
import random
import datetime
import pytz
import re
import threading
import time
from flask import Flask, render_template_string, request, redirect
from groq import Groq
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
import yt_dlp
import games

# ================= الإعدادات الأساسية =================
TOKEN = "8898698558:AAEDmDHjT4g6h3eLRvs5uWCnrT0BDOosOjQ"
GROQ_API_KEY = "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"
ADMIN_ID = "8411608232"
VIDEO_PATH = "video.mp4" 

bot = telebot.TeleBot(TOKEN)
games.setup_game_handlers(bot)
groq_client = Groq(api_key=GROQ_API_KEY)
DB_FILE = "database.json"

STICKER_SETS = [
    "Adhkar_by_maker_Sticker_bot", "Stillness_by_maker_Sticker_bot",
    "Childrennnn_by_maker_Sticker_bot", "Moneyme_by_maker_Sticker_bot",
    "yourose_by_maker_Sticker_bot", "Myrefuge_by_maker_Sticker_bot",
    "Funnyye_by_maker_Sticker_bot", "Life_by_maker_Sticker_bot"
]

try:
    bot.set_my_commands([BotCommand("/start", "رسالة البدء التشغيلية")])
except Exception as e:
    print(f"Error setting commands: {e}")

# ================= إعداد موقع الويب الخاص بك (Flask Web App) =================
app = Flask(__name__)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TWEB Media - التحميل المباشر</title>
    <style>
        body {
            background-color: #0f172a;
            color: #f8fafc;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .card {
            background: #1e293b;
            padding: 30px;
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.5);
            text-align: center;
            max-width: 400px;
            width: 90%;
            border: 1px solid #334155;
        }
        h1 {
            color: #38bdf8;
            font-size: 24px;
            margin-bottom: 10px;
        }
        p {
            color: #94a3b8;
            font-size: 14px;
            margin-bottom: 25px;
        }
        .btn {
            display: block;
            width: 100%;
            padding: 14px;
            background: linear-gradient(135deg, #0284c7, #2563eb);
            color: white;
            text-decoration: none;
            border-radius: 10px;
            font-weight: bold;
            font-size: 16px;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
            transition: 0.3s;
            box-sizing: border-box;
        }
        .btn:hover {
            opacity: 0.9;
            transform: translateY(-2px);
        }
        .footer {
            margin-top: 20px;
            font-size: 12px;
            color: #64748b;
        }
    </style>
</head>
<body>
    <div class="card">
        <h1>⚡ TWEB Media Center</h1>
        <p>جاهز لتحميل الفيديو الخاص بك فوراً وبأعلى جودة بدون إعلانات.</p>
        {% if direct_url %}
            <a href="{{ direct_url }}" class="btn" download>📥 اضغط هنا للتحميل المباشر</a>
        {% else %}
            <p style="color: #ef4444;">عذراً، انتهت مهلة الاتصال أو أن الرابط غير مدعوم حالياً. حاول مجدداً.</p>
        {% endif %}
        <div class="footer">TWEB Bot Production © 2026</div>
    </div>
</body>
</html>
"""

@app.route('/dl')
def web_download():
    video_url = request.args.get('url')
    if not video_url:
        return render_template_string(HTML_TEMPLATE, direct_url=None)
    
    direct_link = None
    try:
        ydl_opts = {
            'format': 'best', 
            'quiet': True,
            'no_warnings': True,
            'socket_timeout': 5,
            'extractor_retries': 1,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            direct_link = info.get('url')
    except Exception as e:
        print(f"Extraction Error: {e}")
        direct_link = None
        
    return render_template_string(HTML_TEMPLATE, direct_url=direct_link)

def run_flask():
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

# ================= إدارة قاعدة البيانات =================
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "login_notice" not in data: data["login_notice"] = True
                if "notified_users" not in data: data["notified_users"] = []
                if "banned_users" not in data: data["banned_users"] = []
                if "users" not in data: data["users"] = []
                return data
        except Exception as e:
            print(f"DB Load Error: {e}")
    return {
        "users": [], "banned_users": [], "notified_users": [],
        "bot_active": True,
        "start_text": "أهلاً بك في بوت الذكاء الاصطناعي TWEB! كيف يمكنني مساعدتك اليوم؟",
        "custom_buttons": [], "support_logs": {}, "user_instructions": {},
        "msg_counters": {}, "login_notice": True
    }

def save_db(db):
    try:
        temp_file = DB_FILE + ".tmp"
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=4)
        os.replace(temp_file, DB_FILE)
    except Exception as e:
        print(f"DB Save Error: {e}")

# ================= لوحات التحكم وقوائم الإدارة =================
def get_admin_keyboard():
    db = load_db()
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("المحتوى 📝", callback_data="menu_content"), 
               InlineKeyboardButton("الإعدادات ⚙️", callback_data="menu_settings"))
    markup.row(InlineKeyboardButton("الاشتراك 🔐", callback_data="menu_subscribe"), 
               InlineKeyboardButton("المستخدمون 👥", callback_data="users_count"))
    markup.row(InlineKeyboardButton("المالية 💰", callback_data="menu_finance"), 
               InlineKeyboardButton("التواصل 📣", callback_data="menu_broadcast"))
    markup.row(InlineKeyboardButton("النظام والدعم 🛠", callback_data="menu_system_support"))
    status_ban = "✅" if "ban_notice" in db else "🚫"
    status_login = "✅" if db.get("login_notice", True) else "🚫"
    markup.row(InlineKeyboardButton(f"إشعار الحظر {status_ban}", callback_data="toggle_ban_notice"), 
               InlineKeyboardButton(f"إشعار الدخول {status_login}", callback_data="toggle_login_notice"))
    markup.row(InlineKeyboardButton("دليل الاستخدام ❓", callback_data="menu_guide"))
    markup.row(InlineKeyboardButton("لوحه تحكم الصانع", callback_data="menu_creator"))
    return markup

def get_settings_keyboard():
    db = load_db()
    markup = InlineKeyboardMarkup()
    status = "💡 مشتغل حالياً" if db.get("bot_active", True) else "🔒 معطل حالياً"
    markup.row(InlineKeyboardButton("🟢 تفعيل البوت عند الكل", callback_data="set_bot_on"))
    markup.row(InlineKeyboardButton("🔴 تعطيل البوت عند الكل", callback_data="set_bot_off"))
    markup.row(InlineKeyboardButton(status, callback_data="none"))
    markup.row(InlineKeyboardButton("« رجوع للوحة الرئيسية", callback_data="back_main"))
    return markup

def get_content_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📝 تعديل الأزرار الشفافة", callback_data="edit_all_inline"))
    markup.row(InlineKeyboardButton("➕ إضافة زر شفاف لرسالة START", callback_data="add_start_btn"))
    markup.row(InlineKeyboardButton("« رجوع للوحة الرئيسية", callback_data="back_main"))
    return markup

def get_creator_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("✏️ تعديل نص رسالة START", callback_data="edit_start_text"))
    markup.row(InlineKeyboardButton("❌ حذف الأزرار الشفافة المضافة", callback_data="clear_start_btns"))
    markup.row(InlineKeyboardButton("« رجوع للوحة الرئيسية", callback_data="back_main"))
    return markup

def build_user_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("الاشتراك 🔐", callback_data="user_menu_sub"),
               InlineKeyboardButton("التواصل 📣", callback_data="user_menu_contact"))
    markup.row(InlineKeyboardButton("النظام والدعم 🛠", callback_data="user_menu_support"),
               InlineKeyboardButton("دليل الاستخدام ❓", callback_data="user_menu_guide"))
    markup.row(InlineKeyboardButton("🎮 الألعاب والترفيه", callback_data="user_menu_games"))
    markup.row(InlineKeyboardButton("تحميل من السوشيال ميديا 📥", callback_data="user_menu_download_guide"))
    markup.row(InlineKeyboardButton("ترجمة صور ومستندات 📸", url="https://translate.google.com.sa/?sl=auto&tl=ar&op=docs"))
    db = load_db()
    for btn in db.get("custom_buttons", []):
        markup.row(InlineKeyboardButton(btn['text'], url=btn['url']))
    return markup

def get_user_back_button():
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("« رجوع للقائمة الرئيسية", callback_data="user_back_home"))
    return markup

def edit_user_interface(call, text, markup):
    try:
        if call.message.photo or call.message.video:
            bot.edit_message_caption(caption=text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.edit_message_text(text=text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        try:
            if call.message.photo or call.message.video:
                bot.edit_message_caption(caption=text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
            else:
                bot.edit_message_text(text=text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
        except Exception as ex:
            print(f"Interface Edit Error: {ex}")

# ================= دوال الذكاء الاصطناعي والمساعدات =================
def send_random_sticker(chat_id):
    try:
        set_name = random.choice(STICKER_SETS)
        sticker_set = bot.get_sticker_set(set_name)
        if sticker_set.stickers:
            bot.send_sticker(chat_id, random.choice(sticker_set.stickers).file_id)
    except:
        pass

def clean_ai_response(text):
    if not text: return text
    cleaned = re.sub(r'\b(tôi|Tôî|aquí)\b', '', text, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', cleaned).strip()

def get_ai_reply(message, user_message):
    tz = pytz.timezone('Asia/Baghdad')
    iraq_time = datetime.datetime.now(tz).strftime('%Y-%m-%d %I:%M:%S %p')
    user_id = message.from_user.id
    username = message.from_user.username or ""
    is_developer = (str(user_id) == ADMIN_ID or username.lower() == "twebii")
    db = load_db()
    
    dev_directive = ""
    if is_developer:
        dev_directive = f"[تنبيه هام جداً]: هذا المستخدم الذي يراسلك الآن هو مطورك وصانعك الأبدي ومبرمجك 'أحمد' (TWEB)، أيديه {ADMIN_ID} ومعرفه @TWEBii."
    
    system_prompt = (
        f"أنت مساعد ذكي مبرمج بواسطة المطور أحمد (TWEB)، واسمك تويب. الوقت والتاريخ الحالي في العراق: {iraq_time}.\n"
        f"{dev_directive}\nقواعد الإجابة: اكتب باللغة العربية الفصحى السليمة فقط ولا تستخدم أي كلمات أجنبية."
    )
    try:
        response = groq_client.chat.completions.create(
            messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": user_message}],
            model="llama-3.3-70b-versatile", temperature=0.1, max_tokens=1024
        )
        return clean_ai_response(response.choices[0].message.content)
    except:
        return "عذراً، أواجه مشكلة في الاتصال بالخادم حالياً. يرجى المحاولة لاحقاً."

# ================= معالجة الأوامر والرسائل =================
@bot.message_handler(commands=['start'])
def start_command(message):
    db = load_db()
    user_id = message.from_user.id
    str_user_id = str(user_id)
    if str_user_id in db.get("banned_users", []): return
    if not db.get("bot_active", True) and str_user_id != ADMIN_ID:
        bot.send_message(message.chat.id, "⚠️ عذراً، البوت متوقف حالياً من قبل المطور لأعمال الصيانة.")
        return

    send_random_sticker(message.chat.id)

    if user_id not in db["users"] and str_user_id != ADMIN_ID:
        db["users"].append(user_id)
        save_db(db)

    if "notified_users" not in db: db["notified_users"] = []
    if str_user_id not in db["notified_users"] and str_user_id != ADMIN_ID:
        db["notified_users"].append(str_user_id)
        save_db(db)
        if db.get("login_notice", True):
            try:
                name = message.from_user.first_name if message.from_user.first_name else "بدون اسم"
                user_link = f"[{name}](tg://user?id={user_id})"
                username = f"@{message.from_user.username}" if message.from_user.username else "لا يوجد يوزر"
                notice_msg = f"🔔 دخل شخص جديد للبوت!\n👤 الحساب: {user_link}\n🔗 اليوزر: {username}\n🆔 الأيدي: `{user_id}`"
                bot.send_message(ADMIN_ID, notice_msg, parse_mode="Markdown")
            except Exception as e:
                print(f"Login Notice Error: {e}")

    if str_user_id == ADMIN_ID or message.from_user.username == "TWEBii":
        stats_text = (
            "• لوحة التحكم الإدارية 🤖\n\n"
            "—— إحصائيات النظام ——\n"
            f"👥 إجمالي المستخدمين: {len(db['users'])}\n"
            f"🚫 المحظورون: {len(db.get('banned_users', []))}\n"
            "📈 حالة البوت: نشط ومستقر\n"
        )
        bot.send_message(message.chat.id, stats_text, reply_markup=get_admin_keyboard())
    else:
        if os.path.exists(VIDEO_PATH):
            with open(VIDEO_PATH, 'rb') as video:
                bot.send_video(message.chat.id, video, caption=db.get("start_text"), reply_markup=build_user_keyboard())
        else:
            bot.send_message(message.chat.id, db.get("start_text"), reply_markup=build_user_keyboard())

# ================= معالج روابط السوشيال ميديا =================
@bot.message_handler(func=lambda m: m.text and ("http://" in m.text or "https://" in m.text))
def handle_social_links(message):
    if "translate.google.com" in message.text: return
    db = load_db()
    user_id = message.from_user.id
    if str(user_id) in db.get("banned_users", []): return
    if not db.get("bot_active", True) and str(user_id) != ADMIN_ID: return
    
    url = message.text.strip()
    railway_domain = "https://twebbot-production.up.railway.app"
    web_page_url = f"{railway_domain}/dl?url={url}"
    
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("🌐 افتح موقع TWEB وحمل الفيديو فوراً", url=web_page_url))

    text_reply = (
        "✨ **TWEB Media Center**\n"
        "━━━━━━━━━━━━━━━━━━━\n"
        "⚡ **تم تجهيز موقعك الخاص بنجاح!**\n"
        "اضغط على الزر أدناه لفتح موقع **TWEB** ورؤية زر التحميل المباشر للبدء بالتحميل فوراً:"
    )
    bot.reply_to(message, text_reply, reply_markup=markup, parse_mode="Markdown")

@bot.message_handler(func=lambda m: True, content_types=['photo', 'document'])
def handle_files(message):
    db = load_db()
    if str(message.from_user.id) in db.get("banned_users", []): return
    text = (
        "📸 **أداة الترجمة الذكية للمستندات والصور**\n\n"
        "🔗 [اضغط هنا للدخول لموقع الترجمة وبدء العمل مباشرة](https://translate.google.com.sa/?sl=auto&tl=ar&op=docs)"
    )
    bot.reply_to(message, text, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(func=lambda m: True, content_types=['sticker'])
def handle_sticker(message):
    db = load_db()
    if str(message.from_user.id) in db.get("banned_users", []): return
    emoji = message.sticker.emoji if message.sticker.emoji else "غير معروف"
    prompt = f"المستخدم أرسل ملصقاً بإيموجي: {emoji}. تفاعل معه بعبارة عربية قصيرة ولطيفة."
    bot.send_chat_action(message.chat.id, 'typing')
    bot.reply_to(message, get_ai_reply(message, prompt))

# ================= معالجة تفاعلات الأزرار الشفافة =================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    db = load_db()

    if call.data == "user_back_home":
        bot.answer_callback_query(call.id)
        edit_user_interface(call, db.get("start_text"), build_user_keyboard())
    elif call.data == "user_menu_sub":
        bot.answer_callback_query(call.id)
        sub_text = (
            "🔐 **قسم دعم وتطوير البوت ماليًا**\n\n"
            "▪️ **معرف بايننس (Binance ID):** `907262941`\n"
            "▪️ **رقم آسيا سيل (AsiaCell):** `07704701242`"
        )
        edit_user_interface(call, sub_text, get_user_back_button())
    elif call.data == "user_menu_contact":
        bot.answer_callback_query(call.id)
        contact_text = "📣 **معلومات التواصل الرسمية مع المطور:**\n\n▪️ **المطور:** @TWEBii\n▪️ **بوت التواصل:** @TWEBI_BOT"
        edit_user_interface(call, contact_text, get_user_back_button())
    elif call.data == "user_menu_support":
        bot.answer_callback_query(call.id)
        today = datetime.datetime.now(pytz.timezone('Asia/Baghdad')).strftime('%Y-%m-%d')
        if db.get("support_logs", {}).get(str(user_id)) == today:
            bot.send_message(user_id, "⚠️ عذراً، لقد قمت بإرسال رسالة دعم اليوم بالفعل.")
            return
        msg = bot.send_message(user_id, "أهلاً بك في قسم الدعم الفني. 🛠\n\nيرجى كتابة رسالتك وسأقوم بتوجيهها للمطور:")
        bot.register_next_step_handler(msg, process_user_support_message, today)
    elif call.data == "user_menu_guide":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(user_id, "دليل الاستخدام. ❓\n\nأرسل رسالة توضح الطريقة التي تفضل أن يتعامل بها البوت معك:")
        bot.register_next_step_handler(msg, process_user_instructions)
    elif call.data == "user_menu_download_guide":
        bot.answer_callback_query(call.id)
        dl_text = (
            "📥 **قسم التحميل من السوشيال ميديا**\n\n"
            "فقط قم بـ **إرسال الرابط مباشرة** هنا في المحادثة، وسيوفر لك البوت زراً يفتح موقع **TWEB** الخاص بك للتحميل الفوري!"
        )
        edit_user_interface(call, dl_text, get_user_back_button())

    if str(user_id) == ADMIN_ID or call.from_user.username == "TWEBii":
        if call.data == "back_main":
            bot.answer_callback_query(call.id)
            stats_text = (
                "• لوحة التحكم الإدارية 🤖\n\n"
                f"👥 إجمالي المستخدمين: {len(db['users'])}\n"
                f"🚫 المحظورون: {len(db.get('banned_users', []))}\n"
                "📈 حالة البوت: نشط ومستقر\n"
            )
            bot.edit_message_text(stats_text, chat_id=user_id, message_id=call.message.message_id, reply_markup=get_admin_keyboard())
        elif call.data == "menu_settings":
            bot.answer_callback_query(call.id)
            bot.edit_message_text("⚙️ **إعدادات التحكم وتشغيل البوت:**", chat_id=user_id, message_id=call.message.message_id, reply_markup=get_settings_keyboard(), parse_mode="Markdown")
        elif call.data == "set_bot_on":
            db["bot_active"] = True
            save_db(db)
            bot.answer_callback_query(call.id, "🟢 تم تفعيل البوت بنجاح.", show_alert=True)
            bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=get_settings_keyboard())
        elif call.data == "set_bot_off":
            db["bot_active"] = False
            save_db(db)
            bot.answer_callback_query(call.id, "🔴 تم تعطيل البوت بنجاح.", show_alert=True)
            bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=get_settings_keyboard())
        elif call.data == "menu_content":
            bot.answer_callback_query(call.id)
            bot.edit_message_text("📝 **إعدادات إدارة المحتوى:**", chat_id=user_id, message_id=call.message.message_id, reply_markup=get_content_keyboard(), parse_mode="Markdown")
        elif call.data == "add_start_btn":
            bot.answer_callback_query(call.id)
            msg = bot.send_message(user_id, "أرسل اسم الزر والرابط هكذا:\n\n`اسم الزر - الرابط`", parse_mode="Markdown")
            bot.register_next_step_handler(msg, process_add_start_button)
        elif call.data == "edit_all_inline":
            bot.answer_callback_query(call.id, "استخدم خيار الإضافة الشفافة المخصص.", show_alert=True)
        elif call.data == "menu_subscribe":
            bot.answer_callback_query(call.id)
            support_view = "🔐 **معلومات الدعم الفعالة:**\n\n▪️ بايننس: `907262941`\n▪️ آسيا سيل: `07704701242`"
            bot.edit_message_text(support_view, chat_id=user_id, message_id=call.message.message_id, reply_markup=get_admin_keyboard(), parse_mode="Markdown")
        elif call.data == "users_count":
            bot.answer_callback_query(call.id, f"👥 عدد المستخدمين الكلي: {len(db['users'])}\n🚫 المحظورون: {len(db.get('banned_users', []))}", show_alert=True)
        elif call.data == "menu_finance":
            bot.answer_callback_query(call.id, "💰 القسم المالي مرتبط ببيانات الدعم المباشرة.", show_alert=True)
        elif call.data == "menu_broadcast":
            bot.answer_callback_query(call.id)
            msg = bot.send_message(user_id, "📣 أرسل رسالة الإذاعة الآن:")
            bot.register_next_step_handler(msg, process_broadcast)
        elif call.data == "menu_system_support":
            bot.answer_callback_query(call.id)
            system_text = "🛠 **إعدادات التحكم بالحظر والأمان:**"
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("🚫 حظر مستخدم", callback_data="admin_ban_user"),
                       InlineKeyboardButton("🟢 إلغاء حظر", callback_data="admin_unban_user"))
            markup.row(InlineKeyboardButton("« رجوع", callback_data="back_main"))
            bot.edit_message_text(system_text, chat_id=user_id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        elif call.data == "admin_ban_user":
            bot.answer_callback_query(call.id)
            msg = bot.send_message(user_id, "🚫 أرسل المعرف أو الأيدي للحظر:")
            bot.register_next_step_handler(msg, process_ban_action, True)
        elif call.data == "admin_unban_user":
            bot.answer_callback_query(call.id)
            msg = bot.send_message(user_id, "🟢 أرسل المعرف أو الأيدي لإلغاء الحظر:")
            bot.register_next_step_handler(msg, process_ban_action, False)
        elif call.data == "toggle_ban_notice":
            if "ban_notice" in db: del db["ban_notice"]
            else: db["ban_notice"] = True
            save_db(db)
            bot.answer_callback_query(call.id, "✅ تم تغيير إعداد إشعار الحظر.", show_alert=True)
            bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=get_admin_keyboard())
        elif call.data == "toggle_login_notice":
            db["login_notice"] = not db.get("login_notice", True)
            save_db(db)
            bot.answer_callback_query(call.id, "✅ تم تغيير إعداد إشعار الدخول.", show_alert=True)
            bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=get_admin_keyboard())
        elif call.data == "menu_guide":
            bot.answer_callback_query(call.id, "❓ هذا القسم يدار بذكاء استنادا لمدخلات العملاء.", show_alert=True)
        elif call.data == "menu_creator":
            bot.answer_callback_query(call.id)
            bot.edit_message_text("🤖 **لوحة الصانع الفوقية الخاصة بالمطور:**", chat_id=user_id, message_id=call.message.message_id, reply_markup=get_creator_keyboard(), parse_mode="Markdown")
        elif call.data == "edit_start_text":
            bot.answer_callback_query(call.id)
            msg = bot.send_message(user_id, "✏️ أرسل نص الترحيب الجديد لرسالة START:")
            bot.register_next_step_handler(msg, process_edit_start_text)
        elif call.data == "clear_start_btns":
            db["custom_buttons"] = []
            save_db(db)
            bot.answer_callback_query(call.id, "❌ تم حذف جميع الأزرار الإضافية بنجاح.", show_alert=True)

# ================= معالجة مدخلات البيانات والفلاتر =================
def process_add_start_button(message):
    if str(message.from_user.id) != ADMIN_ID: return
    try:
        text, url = message.text.split('-', 1)
        db = load_db()
        db["custom_buttons"].append({"text": text.strip(), "url": url.strip()})
        save_db(db)
        bot.reply_to(message, "✅ تم إضافة الزر الشفاف بنجاح.")
    except:
        bot.reply_to(message, "⚠️ صيغة الإدخال خاطئة! يرجى الإرسال هكذا:\n`اسم الزر - الرابط`", parse_mode="Markdown")

def process_edit_start_text(message):
    if str(message.from_user.id) != ADMIN_ID: return
    db = load_db()
    db["start_text"] = message.text
    save_db(db)
    bot.reply_to(message, "✅ تم تحديث نص رسالة START بنجاح.")

def process_broadcast(message):
    if str(message.from_user.id) != ADMIN_ID: return
    db = load_db()
    success, failed = 0, 0
    sent_msg = bot.reply_to(message, "⏳ جاري بدء عملية الإذاعة للمستخدمين...")
    for user_id in db["users"]:
        try:
            bot.copy_message(user_id, message.chat.id, message.message_id)
            success += 1
        except:
            failed += 1
    bot.edit_message_text(chat_id=message.chat.id, message_id=sent_msg.message_id, text=f"📢 تمت الإذاعة بنجاح!\n\n✅ تم الإرسال إلى: {success}\n❌ فشل: {failed}")

def process_ban_action(message, mode_ban=True):
    if str(message.from_user.id) != ADMIN_ID: return
    db = load_db()
    target = message.text.strip().replace("@", "")
    if mode_ban:
        if target not in db["banned_users"]:
            db["banned_users"].append(target)
            save_db(db)
            bot.reply_to(message, f"🚫 تم حظر المستخدم `{target}` بنجاح.", parse_mode="Markdown")
        else:
            bot.reply_to(message, f"⚠️ المستخدم `{target}` محظور مسبقاً.", parse_mode="Markdown")
    else:
        if target in db["banned_users"]:
            db["banned_users"].remove(target)
            save_db(db)
            bot.reply_to(message, f"🟢 تم إلغاء حظر المستخدم `{target}` بنجاح.", parse_mode="Markdown")
        else:
            bot.reply_to(message, f"⚠️ المستخدم `{target}` غير موجود في قائمة الحظر.", parse_mode="Markdown")

# ================= معالجة الرسائل النصية العامة =================
@bot.message_handler(func=lambda m: True, content_types=['text'])
def handle_user_messages(message):
    db = load_db()
    user_id = message.from_user.id
    text = message.text or ""

    if str(user_id) in db.get("banned_users", []) or (message.from_user.username and message.from_user.username in db.get("banned_users", [])):
        return
    if not db.get("bot_active", True) and str(user_id) != ADMIN_ID:
        return

    if message.chat.type in ['group', 'supergroup']:
        is_mentioned = any(name in text for name in ["تويب", "Tweb", "TWEB", "أحمد", "احمد"])
        is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id
        if not (is_mentioned or is_reply_to_bot): return

    user_key = str(user_id)
    counters = db.get("msg_counters", {})
    counters[user_key] = counters.get(user_key, 0) + 1
    db["msg_counters"] = counters
    save_db(db)

    bot.send_chat_action(message.chat.id, 'typing')
    bot.reply_to(message, get_ai_reply(message, text))

    if counters[user_key] % 10 == 0:
        send_random_sticker(message.chat.id)

def process_user_support_message(message, today):
    db = load_db()
    user_id = message.from_user.id
    if "support_logs" not in db: db["support_logs"] = {}
    db["support_logs"][str(user_id)] = today
    save_db(db)
    
    username = f"@{message.from_user.username}" if message.from_user.username else "بدون يوزر"
    report_text = f"📩 **بلاغ دعم فني جديد**\n\n👤 أيدي: `{user_id}`\n🔗 يوزر: {username}\n\n💬 النص:\n{message.text}"
    try:
        bot.send_message(ADMIN_ID, report_text)
        bot.reply_to(message, "✅ تم إرسال بلاغك للمطور بنجاح.")
    except:
        bot.reply_to(message, "⚠️ فشل إرسال البلاغ حالياً، حاول لاحقاً.")

def process_user_instructions(message):
    db = load_db()
    user_id = message.from_user.id
    if "user_instructions" not in db: db["user_instructions"] = {}
    db["user_instructions"][str(user_id)] = message.text
    save_db(db)
    bot.reply_to(message, "✅ تم حفظ تفضيلاتك وأسلوبك، سألتزم بها بدقة في ردودي القادمة.")

if __name__ == "__main__":
    flask_thread = threading.Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    print("تم تفعيل بوت تيليجرام وموقع TWEB المدمج بنجاح!")
    
    while True:
        try:
            bot.infinity_polling(none_stop=True, interval=0, timeout=20, long_polling_timeout=20)
        except Exception as e:
            print(f"Polling error: {e}")
            time.sleep(5)

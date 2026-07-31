import telebot
import os
import json
import random
import datetime
import pytz
import re
import uuid
import time
import logging
from groq import Groq
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, BotCommand
from downloader import download_media, get_video_info
import games  # استدعاء ملف الألعاب الخارجي

# ================= إعدادات التسجيل (Logging) =================
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ================= الإعدادات الأساسية =================
TOKEN = "8898698558:AAEDmDHjT4g6h3eLRvs5uWCnrT0BDOosOjQ" 
GROQ_API_KEY = "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"
ADMIN_ID = "8411608232"
VIDEO_PATH = "video.mp4" 

# ذاكرة مؤقتة لحفظ الروابط لتجنب مشكلة الـ 64 حرف في أزرار تيليجرام
pending_downloads = {}

# ذاكرة لتتبع وقت العداد ومنع حظر الـ API (FloodWait)
last_edit_time = {}

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
    bot.set_my_commands([
        BotCommand("/start", "رسالة البدء"),
        BotCommand("/ping", "فحص سرعة البوت (للمطور)")
    ])
except Exception as e:
    logger.error(f"Error setting commands: {e}")

# ================= إدارة قاعدة البيانات =================
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if "login_notice" not in data: data["login_notice"] = True
                if "notified_users" not in data: data["notified_users"] = []
                return data
        except Exception as e:
            logger.error(f"Error loading DB: {e}")
            pass
    return {
        "users": [], "banned_users": [], "notified_users": [],
        "bot_active": True, "start_text": "أهلاً بك في بوت الذكاء الاصطناعي TWEB! كيف يمكنني مساعدتك اليوم؟",
        "custom_buttons": [], "support_logs": {}, "user_instructions": {},
        "msg_counters": {}, "login_notice": True
    }

def save_db(db):
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(db, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logger.error(f"Error saving DB: {e}")

# ================= لوحات تحكم الإدارة =================
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

# ================= لوحات تحكم وقوائم المستخدمين =================
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
    markup.add(InlineKeyboardButton("« رجوع للقائمة الرئيسية 🔙", callback_data="user_back_home"))
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
            logger.error(f"Interface Edit Error: {ex}")

# ================= دوال الذكاء الاصطناعي والمساعدات =================
def send_random_sticker(chat_id):
    try:
        set_name = random.choice(STICKER_SETS)
        sticker_set = bot.get_sticker_set(set_name)
        if sticker_set.stickers:
            sticker = random.choice(sticker_set.stickers)
            bot.send_sticker(chat_id, sticker.file_id)
    except Exception as e:
        logger.warning(f"Failed to send sticker: {e}")

def clean_ai_response(text):
    if not text:
        return text
    cleaned = re.sub(r'\b(tôi|Tôî|aquí)\b', '', text, flags=re.IGNORECASE)
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

def get_ai_reply(message, user_message):
    tz = pytz.timezone('Asia/Baghdad')
    iraq_time = datetime.datetime.now(tz).strftime('%Y-%m-%d %I:%M:%S %p')
    
    user_id = message.from_user.id
    username = message.from_user.username or ""
    is_developer = (str(user_id) == ADMIN_ID or username.lower() == "twebii")
    
    db = load_db()
    custom_instr = db.get("user_instructions", {}).get(str(user_id), "لا توجد شروط مخصصة.")
    
    dev_directive = ""
    if is_developer:
        dev_directive = (
            f"\n[تنبيه هام جداً ورئيسي]: هذا المستخدم الذي يراسلك الآن هو مطورك وصانعك الأبدي ومبرمجك 'أحمد' (TWEB), "
            f"أيديه هو {ADMIN_ID} ومعرفه هو @TWEBii ورقم هاتفه 07704701242. "
            f"يجب عليك معرفته والاعتراف به فوراً وبكل فخر واحترام في أي مكان أو مجموعة دون أن يحتاج لتذكيرك، "
            f"ولا تنكر أبداً أنه مطورك وصانعك."
        )
    
    system_prompt = (
        f"أنت مساعد ذكي مبرمج بواسطة المطور أحمد (TWEB), واسمك تويب (Tweb أو TWEB). "
        f"الوقت والتاريخ الحالي في العراق هو: {iraq_time}.\n"
        f"{dev_directive}\n"
        f"قواعد الإجابة الصارمة:\n"
        f"1. اكتب باللغة العربية الفصحى السليمة فقط لا غير.\n"
        f"2. يمنع منعاً باتاً استخدام أو إدراج أي كلمات أجنبية أو حروف غريبة تحت أي ظرف.\n"
        f"3. التزم تماماً بتفضيلات التعامل المحددة من هذا المستخدم إن وجدت وهي: [{custom_instr}]."
    )
    
    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.1,
            max_tokens=1024
        )
        raw_reply = response.choices[0].message.content
        return clean_ai_response(raw_reply)
    except Exception as e:
        logger.error(f"Groq API Error: {e}")
        return "عذراً، أواجه مشكلة في الاتصال بالخادم حالياً. يرجى المحاولة لاحقاً."

# ================= معالجة الأوامر والرسائل الأساسية =================
@bot.message_handler(commands=['ping'])
def ping_command(message):
    if str(message.from_user.id) == ADMIN_ID or message.from_user.username == "TWEBii":
        start_time = time.time()
        msg = bot.reply_to(message, "🏓 جاري الفحص...")
        end_time = time.time()
        ping_time = round((end_time - start_time) * 1000)
        bot.edit_message_text(f"🏓 **Pong!**\n⚡️ زمن الاستجابة: `{ping_time}ms`", chat_id=message.chat.id, message_id=msg.message_id, parse_mode="Markdown")

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
                notice_msg = (
                    f"🔔 دخل شخص جديد للبوت!\n"
                    f"👤 الحساب: {user_link}\n"
                    f"🔗 اليوزر: {username}\n"
                    f"🆔 الأيدي: `{user_id}`"
                )
                bot.send_message(ADMIN_ID, notice_msg, parse_mode="Markdown")
            except Exception as e: 
                logger.error(f"Failed to send login notice: {e}")

    if str_user_id == ADMIN_ID or message.from_user.username == "TWEBii":
        stats_text = (
            "• لوحة التحكم 🤖\n\n"
            "—— إحصائيات اليوم ——\n"
            f"👥 الإجمالي: {len(db['users'])}\n"
            "📈 الرسائل: نشط\n"
            "⚡️ متوسط الاستجابة: سريع\n"
        )
        bot.send_message(message.chat.id, stats_text, reply_markup=get_admin_keyboard())
    else:
        if os.path.exists(VIDEO_PATH):
            with open(VIDEO_PATH, 'rb') as video:
                bot.send_video(message.chat.id, video, caption=db.get("start_text"), reply_markup=build_user_keyboard())
        else:
            bot.send_message(message.chat.id, db.get("start_text"), reply_markup=build_user_keyboard())

# ================= معالج طلبات الملصقات والروابط =================
@bot.message_handler(func=lambda m: m.text and any(word in m.text for word in ["ملصق", "ملصقات", "ستيكر", "ستيكرات"]))
def handle_sticker_request(message):
    db = load_db()
    user_id = message.from_user.id
    
    if str(user_id) in db.get("banned_users", []): return
    if not db.get("bot_active", True) and str(user_id) != ADMIN_ID: return
        
    text = message.text
    if any(w in text for w in ["رابط", "روابط"]):
        set_name = random.choice(STICKER_SETS)
        link = f"https://t.me/addstickers/{set_name}"
        bot.reply_to(message, f"🔗 تفضل رابط حزمة الملصقات العشوائية:\n{link}")
    else:
        send_random_sticker(message.chat.id)

def format_duration(seconds):
    if not seconds: return "00:00"
    m, s = divmod(int(seconds), 60)
    h, m = divmod(m, 60)
    if h > 0: return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def format_views(views):
    if not views: return "0"
    if views >= 1_000_000: return f"{views / 1_000_000:.1f}M"
    elif views >= 1_000: return f"{views / 1_000:.1f}K"
    return str(views)

# ================= معالج روابط السوشيال ميديا =================
@bot.message_handler(func=lambda m: m.text and ("http://" in m.text or "https://" in m.text))
def handle_social_links(message):
    if "translate.google.com" in message.text: return
        
    db = load_db()
    user_id = message.from_user.id
    if str(user_id) in db.get("banned_users", []): return
    if not db.get("bot_active", True) and str(user_id) != ADMIN_ID: return
    
    url = message.text.strip()
    status_msg = bot.reply_to(message, "⏳ جاري استخراج تفاصيل المقطع، يرجى الانتظار...")
    info = get_video_info(url)
    
    if not info:
        bot.edit_message_text("❌ عذراً، لم أتمكن من جلب تفاصيل هذا الرابط. تأكد من صلاحية الرابط وأنه مدعوم.", 
                              chat_id=message.chat.id, message_id=status_msg.message_id)
        return

    title = info.get('title', 'بدون عنوان')
    duration = format_duration(info.get('duration', 0))
    views = format_views(info.get('view_count', 0))
    uploader = info.get('uploader', 'غير معروف')
    
    text = (
        f"🎬 **التفاصيل المستخرجة:**\n\n"
        f"📌 **العنوان:** {title}\n"
        f"⏱ **المدة:** {duration}\n"
        f"👁 **المشاهدات:** {views}\n"
        f"👤 **القناة:** {uploader}\n\n"
        f"👇 **اختر الصيغة المطلوبة للتحميل (الحد الأقصى 50MB):**"
    )
    
    short_id = str(uuid.uuid4())[:8]
    pending_downloads[short_id] = url
    
    markup = InlineKeyboardMarkup()
    markup.row(
        InlineKeyboardButton("تحميل كـ فيديو 🎥", callback_data=f"dl_vid|{short_id}"),
        InlineKeyboardButton("تحميل كـ صوت 🎵", callback_data=f"dl_aud|{short_id}")
    )
    markup.row(InlineKeyboardButton("« رجوع للقائمة الرئيسية 🔙", callback_data="user_back_home"))
    
    bot.edit_message_text(text, chat_id=message.chat.id, message_id=status_msg.message_id, 
                          reply_markup=markup)

# ================= معالج أزرار التحميل (المُحدث والآمن) =================
@bot.callback_query_handler(func=lambda call: call.data.startswith("dl_"))
def handle_download_callback(call):
    data_parts = call.data.split("|", 1)
    action = data_parts[0]
    short_id = data_parts[1]
    
    url = pending_downloads.get(short_id)
    if not url:
        bot.answer_callback_query(call.id, "⚠️ انتهت صلاحية هذا الزر، يرجى إرسال الرابط مجدداً.", show_alert=True)
        return

    bot.answer_callback_query(call.id, "⏳ جاري المعالجة...")
    
    progress_msg = bot.edit_message_text(
        text="📥 **جاري تجهيز التحميل...**\n`[0.0%] ⏳`", 
        chat_id=call.message.chat.id, 
        message_id=call.message.message_id, 
        parse_mode="Markdown"
    )
    
    def progress_updater(percent):
        current_time = time.time()
        msg_id = progress_msg.message_id
        if current_time - last_edit_time.get(msg_id, 0) > 3:
            try:
                bot.edit_message_text(
                    text=f"📥 **جاري التحميل الفعلي...**\n`[{percent:.1f}%] ⏳`", 
                    chat_id=call.message.chat.id, 
                    message_id=msg_id, 
                    parse_mode="Markdown"
                )
                last_edit_time[msg_id] = current_time
            except Exception:
                pass

    media_type = 'video' if action == "dl_vid" else 'audio'
    file_path = download_media(url, media_type=media_type, progress_callback=progress_updater)
    last_edit_time.pop(progress_msg.message_id, None)

    if not file_path:
        error_message = (
            "❌ **عذراً، تعذر إرسال الفيديو!**\n\n"
            "> حجم الفيديو يتجاوز حد تليجرام المسموح (50 ميجابايت)، وحتى بعد محاولة تحميله بأقل دقة ممكنة، لا يزال الملف كبيراً جداً.\n\n"
            "💡 **نصيحة:** حاول تحميل مقطع أقصر مدة ليناسب الحد المسموح."
        )
        bot.edit_message_text(
            chat_id=call.message.chat.id, 
            message_id=progress_msg.message_id, 
            text=error_message,
            parse_mode="Markdown"
        )
    elif os.path.exists(file_path):
        try:
            bot.edit_message_text(
                text="✅ **اكتمل التحميل، جاري الرفع لتيليجرام...**", 
                chat_id=call.message.chat.id, 
                message_id=progress_msg.message_id, 
                parse_mode="Markdown"
            )
            
            with open(file_path, 'rb') as f:
                back_markup = InlineKeyboardMarkup()
                back_markup.add(InlineKeyboardButton("« رجوع للقائمة الرئيسية 🔙", callback_data="user_back_home"))
                
                if media_type == "video":
                    bot.send_video(
                        call.message.chat.id, f, 
                        caption="✅ تم التنزيل بنجاح عبر بوت TWEB",
                        reply_markup=back_markup
                    )
                else:
                    bot.send_audio(
                        call.message.chat.id, f,
                        caption="🎵 الملف الصوتي عبر بوت TWEB",
                        reply_markup=back_markup
                    )
            
            pending_downloads.pop(short_id, None)
            bot.delete_message(call.message.chat.id, progress_msg.message_id)
            
        except Exception as e:
            logger.error(f"Telegram Send Error: {e}")
            bot.edit_message_text(
                chat_id=call.message.chat.id, 
                message_id=progress_msg.message_id, 
                text="⚠️ حدث خطأ أثناء رفع الملف إلى تيليجرام."
            )
        finally:
            if os.path.exists(file_path):
                try: os.remove(file_path)
                except Exception as e: logger.error(f"Failed to remove file: {e}")

# ================= التفاعل مع الملفات والملصقات =================
@bot.message_handler(func=lambda m: True, content_types=['photo', 'document'])
def handle_files(message):
    db = load_db()
    if str(message.from_user.id) in db.get("banned_users", []): return
    if not db.get("bot_active", True) and str(message.from_user.id) != ADMIN_ID: return

    text = (
        "📸 **أداة الترجمة الذكية للمستندات والصور**\n\n"
        "لقد قمت بإرسال ملف أو صورة! للترجمة الاحترافية والدقيقة، "
        "نوصي باستخدام أداة ترجمة جوجل المخصصة، والتي تتميز بـ:\n\n"
        "✨ **السرعة والدقة** في ترجمة النصوص داخل الصور.\n"
        "📄 **دعم ملفات** الـ PDF والـ Word وغيرها.\n"
        "🔒 **الحفاظ على تنسيق** الملف الأصلي.\n\n"
        "🔗 [اضغط هنا للدخول لموقع الترجمة وبدء العمل مباشرة](https://translate.google.com.sa/?sl=auto&tl=ar&op=docs)"
    )
    bot.reply_to(message, text, parse_mode="Markdown", disable_web_page_preview=True)

@bot.message_handler(func=lambda m: True, content_types=['sticker'])
def handle_sticker(message):
    db = load_db()
    if str(message.from_user.id) in db.get("banned_users", []): return
    if not db.get("bot_active", True) and str(message.from_user.id) != ADMIN_ID: return
    
    emoji = message.sticker.emoji if message.sticker.emoji else "غير معروف"
    prompt = f"المستخدم أرسل لي ملصقاً (Sticker) يعبر عن هذا الإيموجي: {emoji}. تفاعل معه بعبارة عربية قصيرة ولطيفة جداً."
    
    bot.send_chat_action(message.chat.id, 'typing')
    ai_response = get_ai_reply(message, prompt)
    bot.reply_to(message, ai_response)

# ================= معالجة تفاعلات الأزرار الشفافة والإدارة =================
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
            "يمكنك المساهمة في استمرار وتطوير خدماتنا عبر قنوات الدعم التالية:\n\n"
            "▪️ **معرف بايننس (Binance ID):** `907262941`\n"
            "▪️ **رقم آسيا سيل (AsiaCell):** `07704701242`"
        )
        edit_user_interface(call, sub_text, get_user_back_button())
        
    elif call.data == "user_menu_contact":
        bot.answer_callback_query(call.id)
        contact_text = (
            "📣 **معلومات التواصل الرسمية والمباشرة مع المطور:**\n\n"
            "▪️ **الحساب الشخصي للمطور:** @TWEBii\n"
            "▪️ **بوت التواصل المباشر:** @TWEBI_BOT\n\n"
            "يسعدنا استقبال استفساراتكم في أي وقت."
        )
        edit_user_interface(call, contact_text, get_user_back_button())
        
    elif call.data == "user_menu_support":
        bot.answer_callback_query(call.id)
        today = datetime.datetime.now(pytz.timezone('Asia/Baghdad')).strftime('%Y-%m-%d')
        if db.get("support_logs", {}).get(str(user_id)) == today:
            bot.send_message(user_id, "⚠️ عذراً عزيزي، لقد قمت بإرسال رسالة دعم اليوم بالفعل. يُسمح برسالة واحدة يومياً.")
            return
            
        msg = bot.send_message(user_id, "أهلاً بك في قسم الدعم الفني. 🛠\n\nيرجى كتابة وإرسال تفاصيل الخطأ أو التحديث الذي تقترحه في رسالة واحدة واضحة. سيتم توجيهها لمالك البوت (بلاغ واحد يومياً).")
        bot.register_next_step_handler(msg, process_user_support_message, today)
        
    elif call.data == "user_menu_guide":
        bot.answer_callback_query(call.id)
        msg = bot.send_message(user_id, "دليل الاستخدام المطور. ❓\n\nأرسل رسالة توضح الطريقة التي تفضل أن يتعامل بها البوت معك (مثال: أجبني باختصار), وسيقوم بتطبيقها فوراً.")
        bot.register_next_step_handler(msg, process_user_instructions)

    elif call.data == "user_menu_download_guide":
        bot.answer_callback_query(call.id)
        dl_text = (
            "📥 **قسم التحميل من السوشيال ميديا**\n\n"
            "لكي تقوم بتحميل أي فيديو (الحد الأقصى 50 ميجابايت):\n"
            "فقط قم بـ **إرسال الرابط مباشرة** (من تيك توك، يوتيوب، انستغرام، فيسبوك، وغيرها) هنا في المحادثة، وسيقوم البوت بتحميله وإرساله إليك فوراً وبأعلى جودة مناسبة!"
        )
        edit_user_interface(call, dl_text, get_user_back_button())

    # أوامر الإدارة
    if str(user_id) == ADMIN_ID or call.from_user.username == "TWEBii":
        if call.data == "back_main":
            stats_text = (
                "• لوحة التحكم 🤖\n\n"
                "—— إحصائيات اليوم ——\n"
                f"👥 الإجمالي: {len(db['users'])}\n"
                "📈 الرسائل: نشط\n"
                "⚡️ متوسط الاستجابة: سريع\n"
            )
            bot.edit_message_text(stats_text, chat_id=user_id, message_id=call.message.message_id, reply_markup=get_admin_keyboard())

        elif call.data == "menu_settings":
            bot.edit_message_text("⚙️ **إعدادات التحكم وتشغيل البوت:**", chat_id=user_id, message_id=call.message.message_id, reply_markup=get_settings_keyboard(), parse_mode="Markdown")

        elif call.data == "set_bot_on":
            db["bot_active"] = True
            save_db(db)
            bot.answer_callback_query(call.id, "🟢 تم تفعيل البوت.", show_alert=True)
            bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=get_settings_keyboard())

        elif call.data == "set_bot_off":
            db["bot_active"] = False
            save_db(db)
            bot.answer_callback_query(call.id, "🔴 تم تعطيل البوت.", show_alert=True)
            bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=get_settings_keyboard())

        elif call.data == "menu_content":
            bot.edit_message_text("📝 **إعدادات إدارة المحتوى:**", chat_id=user_id, message_id=call.message.message_id, reply_markup=get_content_keyboard(), parse_mode="Markdown")

        elif call.data == "add_start_btn":
            msg = bot.send_message(user_id, "أرسل اسم الزر والرابط هكذا:\n\n`اسم الزر - الرابط`", parse_mode="Markdown")
            bot.register_next_step_handler(msg, process_add_start_button)

        elif call.data == "edit_all_inline":
            bot.answer_callback_query(call.id, "استخدم خيار الإضافة الشفاف.", show_alert=True)

        elif call.data == "menu_subscribe":
            support_view = (
                "🔐 **معلومات الدعم الفعالة حالياً:**\n\n"
                f"▪️ معرف بايننس: `907262941`\n"
                f"▪️ رقم آسيا سيل: `07704701242`"
            )
            bot.edit_message_text(support_view, chat_id=user_id, message_id=call.message.message_id, reply_markup=get_admin_keyboard())

        elif call.data == "users_count":
            bot.answer_callback_query(call.id, f"👥 عدد المستخدمين: {len(db['users'])}", show_alert=True)

        elif call.data == "menu_finance":
            bot.answer_callback_query(call.id, "💰 القسم المالي متاح وتلقائي.")

        elif call.data == "menu_broadcast":
            msg = bot.send_message(user_id, "📣 أرسل رسالة الإذاعة الآن:")
            bot.register_next_step_handler(msg, process_broadcast)

        elif call.data == "menu_system_support":
            system_text = "🛠 **إعدادات التحكم بالحظر والأمان:**"
            markup = InlineKeyboardMarkup()
            markup.row(InlineKeyboardButton("🚫 حظر مستخدم", callback_data="admin_ban_user"),
                       InlineKeyboardButton("🟢 إلغاء حظر", callback_data="admin_unban_user"))
            markup.row(InlineKeyboardButton("« رجوع", callback_data="back_main"))
            bot.edit_message_text(system_text, chat_id=user_id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")

        elif call.data == "admin_ban_user":
            msg = bot.send_message(user_id, "🚫 أرسل المعرف للحظر:")
            bot.register_next_step_handler(msg, process_ban_action, True)

        elif call.data == "admin_unban_user":
            msg = bot.send_message(user_id, "🟢 أرسل المعرف لإلغاء الحظر:")
            bot.register_next_step_handler(msg, process_ban_action, False)

        elif call.data == "toggle_ban_notice":
            if "ban_notice" in db: del db["ban_notice"]
            else: db["ban_notice"] = True
            save_db(db)
            bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=get_admin_keyboard())

        elif call.data == "toggle_login_notice":
            db["login_notice"] = not db.get("login_notice", True)
            save_db(db)
            bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=get_admin_keyboard())

        elif call.data == "menu_guide":
            bot.edit_message_text("❓ تعمل تلقائياً مع مدخلات العميل.", chat_id=user_id, message_id=call.message.message_id, reply_markup=get_admin_keyboard())

        elif call.data == "menu_creator":
            bot.edit_message_text("🤖 **لوحة الصانع الفوقية:**", chat_id=user_id, message_id=call.message.message_id, reply_markup=get_creator_keyboard(), parse_mode="Markdown")

        elif call.data == "edit_start_text":
            msg = bot.send_message(user_id, "✏️ أرسل نص الترحيب الجديد:")
            bot.register_next_step_handler(msg, process_edit_start_text)

        elif call.data == "clear_start_btns":
            db["custom_buttons"] = []
            save_db(db)
            bot.answer_callback_query(call.id, "❌ تم حذف الأزرار الإضافية.", show_alert=True)

# ================= معالجة مدخلات البيانات الفوقية =================
def process_add_start_button(message):
    if str(message.from_user.id) != ADMIN_ID: return
    try:
        text, url = message.text.split('-', 1)
        db = load_db()
        db["custom_buttons"].append({"text": text.strip(), "url": url.strip()})
        save_db(db)
        bot.reply_to(message, "✅ تم إضافة الزر.")
    except Exception as e:
        logger.error(f"Button add error: {e}")
        bot.reply_to(message, "⚠️ صيغة الإدخال خاطئة! `اسم الزر - الرابط`")

def process_edit_start_text(message):
    if str(message.from_user.id) != ADMIN_ID: return
    db = load_db()
    db["start_text"] = message.text
    save_db(db)
    bot.reply_to(message, "✅ تم تحديث النص.")

def process_broadcast(message):
    if str(message.from_user.id) != ADMIN_ID: return
    db = load_db()
    success = 0
    bot.reply_to(message, "جاري الإذاعة...")
    for user_id in db["users"]:
        try:
            bot.copy_message(user_id, message.chat.id, message.message_id)
            success += 1
        except Exception:
            pass
    bot.send_message(message.chat.id, f"📢 تمت الإذاعة لـ {success} مستخدم.")

def process_ban_action(message, mode_ban=True):
    if str(message.from_user.id) != ADMIN_ID: return
    db = load_db()
    target = message.text.strip().replace("@", "")
    
    if mode_ban:
        if target not in db["banned_users"]:
            db["banned_users"].append(target)
            save_db(db)
            bot.reply_to(message, f"🚫 تم حظر `{target}`.", parse_mode="Markdown")
    else:
        if target in db["banned_users"]:
            db["banned_users"].remove(target)
            save_db(db)
            bot.reply_to(message, f"🟢 تم إلغاء حظر `{target}`.", parse_mode="Markdown")

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
        
        if not (is_mentioned or is_reply_to_bot):
            return

    user_key = str(user_id)
    counters = db.get("msg_counters", {})
    counters[user_key] = counters.get(user_key, 0) + 1
    db["msg_counters"] = counters
    save_db(db)

    bot.send_chat_action(message.chat.id, 'typing')
    ai_response = get_ai_reply(message, text)
    bot.reply_to(message, ai_response)

    if counters[user_key] % 10 == 0:
        send_random_sticker(message.chat.id)

def process_user_support_message(message, today):
    db = load_db()
    user_id = message.from_user.id
    
    if "support_logs" not in db: db["support_logs"] = {}
    db["support_logs"][str(user_id)] = today
    save_db(db)
    
    username = f"@{message.from_user.username}" if message.from_user.username else "بدون يوزر"
    report_text = (
        f"📩 **بلاغ دعم فني**\n\n"
        f"👤 أيدي: `{user_id}`\n"
        f"🔗 يوزر: {username}\n\n"
        f"💬 النص:\n{message.text}"
    )
    try:
        bot.send_message(ADMIN_ID, report_text)
        bot.reply_to(message, "✅ تم إرسال البلاغ للمطور بنجاح.")
    except Exception as e:
        logger.error(f"Support report error: {e}")
        bot.reply_to(message, "⚠️ فشل الإرسال حالياً.")

def process_user_instructions(message):
    db = load_db()
    user_id = message.from_user.id
    
    if "user_instructions" not in db: db["user_instructions"] = {}
    db["user_instructions"][str(user_id)] = message.text
    save_db(db)
    
    bot.reply_to(message, "✅ تم حفظ أسلوبك، سألتزم به في ردودي القادمة.")

if __name__ == "__main__":
    logger.info("تم تحديث البوت بالكامل، وربط كليشة تجاوز الحد الأقصى (50MB) بنجاح!")
    bot.remove_webhook()
    bot.infinity_polling()

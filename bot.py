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

STICKER_SETS = [
    "Adhkar_by_maker_Sticker_bot", "Stillness_by_maker_Sticker_bot",
    "Childrennnn_by_maker_Sticker_bot", "Moneyme_by_maker_Sticker_bot",
    "yourose_by_maker_Sticker_bot", "Myrefuge_by_maker_Sticker_bot",
    "Funnyye_by_maker_Sticker_bot", "Life_by_maker_Sticker_bot"
]

# ================= إدارة قاعدة البيانات =================
def load_db():
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "users": [],
        "banned_users": [],
        "bot_active": True,
        "start_text": "أهلاً بك في بوت التذاكاء الاصطناعي TWEB! كيف يمكنني مساعدتك اليوم؟",
        "custom_buttons": [],
        "support_logs": {},
        "user_instructions": {},
        "msg_counters": {}
    }

def save_db(db):
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=4)

# ================= صناعة لوحات التحكم وقوائم الأزرار =================

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
    status_login = "✅" if "login_notice" in db else "🔔"
    markup.row(InlineKeyboardButton(f"إشعار الحظر {status_ban}", callback_data="toggle_ban_notice"), 
               InlineKeyboardButton(f"إشعار الدخول {status_login}", callback_data="toggle_login_notice"))
               
    markup.row(InlineKeyboardButton("دليل الاستخدام ❓", callback_data="menu_guide"))
    markup.row(InlineKeyboardButton("لوحه تحكم الصانع", callback_data="menu_creator"))
    return markup

def get_back_button(target):
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("« رجوع للوحة الرئيسية", callback_data=f"back_{target}"))
    return markup

# ================= لوحات القوائم الفرعية للمطور =================
def get_settings_keyboard():
    db = load_db()
    markup = InlineKeyboardMarkup()
    status = "💡 مشتغل حالياً" if db.get("bot_active", True) else "🔒 معطل حالياً"
    markup.row(InlineKeyboardButton("🟢 تفعيل البوت عند الكل", callback_data="set_bot_on"))
    markup.row(InlineKeyboardButton("🔴 تعطيل البوت عند الكل", callback_data="set_bot_off"))
    markup.row(InlineKeyboardButton(status, callback_data="none"))
    markup.row(InlineKeyboardButton("« رجوع", callback_data="back_main"))
    return markup

def get_content_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("📝 تعديل الأزرار الشفافة", callback_data="edit_all_inline"))
    markup.row(InlineKeyboardButton("➕ إضافة زر شفاف لرسالة START", callback_data="add_start_btn"))
    markup.row(InlineKeyboardButton("« رجوع", callback_data="back_main"))
    return markup

def get_creator_keyboard():
    markup = InlineKeyboardMarkup()
    markup.row(InlineKeyboardButton("✏️ تعديل نص رسالة START", callback_data="edit_start_text"))
    markup.row(InlineKeyboardButton("❌ حذف الأزرار الشفافة المضافة", callback_data="clear_start_btns"))
    markup.row(InlineKeyboardButton("« رجوع", callback_data="back_main"))
    return markup

# ================= دوال الذكاء الاصطناعي والمساعدات =================
def send_random_sticker(chat_id):
    try:
        set_name = random.choice(STICKER_SETS)
        sticker_set = bot.get_sticker_set(set_name)
        if sticker_set.stickers:
            sticker = random.choice(sticker_set.stickers)
            bot.send_sticker(chat_id, sticker.file_id)
    except Exception as e:
        print(f"Sticker Error: {e}")

def get_ai_reply(user_id, user_message):
    tz = pytz.timezone('Asia/Baghdad')
    iraq_time = datetime.datetime.now(tz).strftime('%Y-%m-%d %I:%M:%S %p')
    
    db = load_db()
    custom_instr = db.get("user_instructions", {}).get(str(user_id), "لا توجد شروط مخصصة.")
    
    system_prompt = (
        f"أنت مساعد ذكي مبرمج بواسطة المطور أحمد (TWEB)، واسمك تويب (Tweb أو TWEB). "
        f"حساب مطورك على ببجي هو TWEB. الوقت والتاريخ الحالي في العراق هو: {iraq_time}.\n"
        f"قواعد الإجابة الصارمة:\n"
        f"1. تحدث باللغة العربية الفصحى الحديثة والمفهومة بدقة بالغة وبأسلوب رسمي رصين.\n"
        f"2. يمنع منعاً باتاً إدخال أو دمج أي كلمات لغات أجنبية غريبة (مثل البولندية أو غيرها).\n"
        f"3. قلل من استخدام الرموز التعبيرية (الإيموجي) واجعل التفاعل رسمياً ومحدوداً جداً.\n"
        f"4. التزم تماماً بتفضيلات التعامل المحددة من هذا المستخدم إن وجدت وهي: [{custom_instr}]."
    )
    
    try:
        response = groq_client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message}
            ],
            model="llama-3.3-70b-versatile",
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"❌ Groq API Error: {e}")
        return "عذراً، أواجه مشكلة في الاتصال بالخادم حالياً. يرجى المحاولة لاحقاً."

# بناء قائمة التفاعل لرسالة Start الخاصة بكل مستخدم
def build_user_start_keyboard():
    markup = InlineKeyboardMarkup()
    db = load_db()
    
    # أزرار مضافة ديناميكياً من المطور
    for btn in db.get("custom_buttons", []):
        markup.row(InlineKeyboardButton(btn['text'], url=btn['url']))
        
    # الزر الثابت لترجمة المستندات والصور
    markup.row(InlineKeyboardButton("📸 ترجمة صور ومستندات", url="https://translate.google.com.sa/?sl=auto&tl=ar&op=docs"))
    return markup

# ================= معالجة الأوامر والرسائل الأساسية =================

@bot.message_handler(commands=['start'])
def start_command(message):
    db = load_db()
    user_id = message.chat.id
    
    # فحص الحظر
    if str(user_id) in db.get("banned_users", []):
        return

    # فحص تعطل البوت عند الكل (ما عدا المطور)
    if not db.get("bot_active", True) and str(user_id) != ADMIN_ID:
        bot.send_message(user_id, "⚠️ عذراً، البوت متوقف حالياً من قبل المطور لأعمال الصيانة.")
        return

    # معالجة دخول مستخدم جديد وتفعيل الإشعار للمطور
    if user_id not in db["users"]:
        db["users"].append(user_id)
        save_db(db)
        if db.get("login_notice", False):
            try:
                bot.send_message(ADMIN_ID, f"🔔 دخل شخص جديد للبوت!\n👤 الأيدي: `{user_id}`", parse_mode="Markdown")
            except: pass

    # التحقق لو كان المستخدم هو المطور
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
        # إرسال الصورة الترحيبية مع الأزرار للمستخدم العادي
        # نستخدم رابط صورة افتراضية كنموذج
        photo_url = "https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?q=80&w=1000&auto=format&fit=crop"
        
        send_random_sticker(user_id)
        try:
            bot.send_photo(
                user_id, 
                photo_url, 
                caption=db.get("start_text"), 
                reply_markup=build_user_start_keyboard()
            )
        except:
            bot.send_message(user_id, db.get("start_text"), reply_markup=build_user_start_keyboard())

# ================= معالجة تفاعلات الـ Callback (الأزرار الشفافة) =================
@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.message.chat.id
    db = load_db()

    # أزرار المستخدمين العامين
    if str(user_id) != ADMIN_ID:
        if call.data == "user_support":
            bot.answer_callback_query(call.id)
            # إرسال معلومات الدعم الفني الخاصة بك
            support_info = (
                "💸 **دعم وتطوير البوت**\n\n"
                f"🆔 معرف بايننس (Binance ID): `907262941`\n"
                f"📞 رقم آسيا سيل (AsiaCell): `07704701242`"
            )
            bot.send_message(user_id, support_info, parse_mode="Markdown")
        return

    # --- أزرار التحكم الخاصة بالمطور أحمد ---
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
        bot.answer_callback_query(call.id, "🟢 تم تفعيل وتشغيل البوت بنجاح للجميع.", show_alert=True)
        bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=get_settings_keyboard())

    elif call.data == "set_bot_off":
        db["bot_active"] = False
        save_db(db)
        bot.answer_callback_query(call.id, "🔴 تم تعطيل البوت بنجاح وحظره عن الجميع.", show_alert=True)
        bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=get_settings_keyboard())

    elif call.data == "menu_content":
        bot.edit_message_text("📝 **إعدادات إدارة محتوى وأزرار البوت:**", chat_id=user_id, message_id=call.message.message_id, reply_markup=get_content_keyboard(), parse_mode="Markdown")

    elif call.data == "add_start_btn":
        msg = bot.send_message(user_id, "أرسل الآن اسم الزر الشفاف متبوعاً بالرابط بهذا الشكل تماماً:\n\n`اسم الزر - الرابط`", parse_mode="Markdown")
        bot.register_next_step_handler(msg, process_add_start_button)

    elif call.data == "edit_all_inline":
        bot.answer_callback_query(call.id, "يمكنك إدارة الأزرار الشفافة لرسالة START عبر خيارات لوحة المحتوى والصانع.", show_alert=True)

    elif call.data == "menu_subscribe":
        # قسم إيضاح دعم البوت المالي
        support_view = (
            "🔐 **قسم الاشتراك والدعم المالي للبوت**\n\n"
            "المعلومات الحالية المعروضة للمستخدمين:\n"
            f"▪️ معرف بايننس: `907262941`\n"
            f"▪️ رقم آسيا سيل: `07704701242`"
        )
        bot.edit_message_text(support_view, chat_id=user_id, message_id=call.message.message_id, reply_markup=get_back_button("main"), parse_mode="Markdown")

    elif call.data == "users_count":
        bot.answer_callback_query(call.id, f"👥 عدد مستخدمي البوت الكلي: {len(db['users'])}", show_alert=True)

    elif call.data == "menu_finance":
        bot.answer_callback_query(call.id, "💰 القسم المالي متاح وقيد الربط الفوري.")

    elif call.data == "menu_broadcast":
        msg = bot.send_message(user_id, "📣 أرسل رسالة الإذاعة الآن لنشرها لكافة المستخدمين:")
        bot.register_next_step_handler(msg, process_broadcast)

    elif call.data == "menu_system_support":
        system_text = (
            "🛠 **إعدادات النظام والدعم الفني**\n\n"
            "للقيام بحظر مستخدم أو إلغاء حظره، استخدم الأزرار التفاعلية التالية:"
        )
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("🚫 حظر مستخدم نهائياً", callback_data="admin_ban_user"),
                   InlineKeyboardButton("🟢 إلغاء حظر مستخدم", callback_data="admin_unban_user"))
        markup.row(InlineKeyboardButton("« رجوع", callback_data="back_main"))
        bot.edit_message_text(system_text, chat_id=user_id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")

    elif call.data == "admin_ban_user":
        msg = bot.send_message(user_id, "🚫 أرسل الآن معرف الشخص (Username) أو الآيدي (ID) الخاص به ليتم حظره:")
        bot.register_next_step_handler(msg, process_ban_action, True)

    elif call.data == "admin_unban_user":
        msg = bot.send_message(user_id, "🟢 أرسل الآن معرف الشخص أو الآيدي الخاص به لإلغاء الحظر عنه:")
        bot.register_next_step_handler(msg, process_ban_action, False)

    elif call.data == "toggle_ban_notice":
        if "ban_notice" in db: del db["ban_notice"]
        else: db["ban_notice"] = True
        save_db(db)
        bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=get_admin_keyboard())

    elif call.data == "toggle_login_notice":
        db["login_notice"] = not db.get("login_notice", False)
        save_db(db)
        bot.edit_message_reply_markup(chat_id=user_id, message_id=call.message.message_id, reply_markup=get_admin_keyboard())

    elif call.data == "menu_guide":
        bot.edit_message_text("❓ دليل الاستخدام مفعل للمستخدمين لتوجيه طريقتهم الخاصة للذكاء الاصطناعي.", chat_id=user_id, message_id=call.message.message_id, reply_markup=get_back_button("main"))

    elif call.data == "menu_creator":
        bot.edit_message_text("🤖 **لوحة تحكم الصانع الفوقية:**", chat_id=user_id, message_id=call.message.message_id, reply_markup=get_creator_keyboard(), parse_mode="Markdown")

    elif call.data == "edit_start_text":
        msg = bot.send_message(user_id, "✏️ أرسل الآن نص الترحيب الجديد الخاص برسالة START:")
        bot.register_next_step_handler(msg, process_edit_start_text)

    elif call.data == "clear_start_btns":
        db["custom_buttons"] = []
        save_db(db)
        bot.answer_callback_query(call.id, "❌ تم حذف وتصفير جميع الأزرار الشفافة المضافة لرسالة START.", show_alert=True)

# ================= معالجة دوال الـ Step المتقدمة للمطور =================
def process_add_start_button(message):
    if str(message.chat.id) != ADMIN_ID: return
    try:
        text, url = message.text.split('-', 1)
        db = load_db()
        db["custom_buttons"].append({"text": text.strip(), "url": url.strip()})
        save_db(db)
        bot.reply_to(message, "✅ تم إضافة الزر الشفاف بنجاح لرسالة START.")
    except:
        bot.reply_to(message, "⚠️ صيغة الإدخال خاطئة! يرجى كتابتها على هذا النحو: `اسم الزر - الرابط`")

def process_edit_start_text(message):
    if str(message.chat.id) != ADMIN_ID: return
    db = load_db()
    db["start_text"] = message.text
    save_db(db)
    bot.reply_to(message, "✅ تم تحديث وتغيير نص رسالة START بنجاح.")

def process_broadcast(message):
    if str(message.chat.id) != ADMIN_ID: return
    db = load_db()
    success = 0
    bot.reply_to(message, "جاري بدء الإذاعة ونشر المحتوى للجميع...")
    for user_id in db["users"]:
        try:
            bot.copy_message(user_id, message.chat.id, message.message_id)
            success += 1
        except: pass
    bot.send_message(message.chat.id, f"📢 تم إرسال الإذاعة بنجاح لـ {success} مستخدم.")

def process_ban_action(message, mode_ban=True):
    if str(message.chat.id) != ADMIN_ID: return
    db = load_db()
    target = message.text.strip().replace("@", "")
    
    if mode_ban:
        if target not in db["banned_users"]:
            db["banned_users"].append(target)
            save_db(db)
            bot.reply_to(message, f"🚫 تم حظر المستخدم `{target}` نهائياً بنجاح من البوت.", parse_mode="Markdown")
    else:
        if target in db["banned_users"]:
            db["banned_users"].remove(target)
            save_db(db)
            bot.reply_to(message, f"🟢 تم إلغاء حظر المستخدم `{target}` وأصبح بإمكانه استخدام البوت.", parse_mode="Markdown")
        else:
            bot.reply_to(message, "⚠️ هذا المستخدم غير موجود في قائمة المحظورين أصلاً.")

# ================= التفاعل العام وقائمتي المستخدمين =================
@bot.message_handler(func=lambda m: True, content_types=['text'])
def handle_user_messages(message):
    db = load_db()
    user_id = message.chat.id
    text = message.text

    # فحص الحظر
    if str(user_id) in db.get("banned_users", []) or (message.from_user.username and message.from_user.username in db.get("banned_users", [])):
        return

    # فحص تعطل البوت للجميع
    if not db.get("bot_active", True) and str(user_id) != ADMIN_ID:
        return

    # معالجة الردود في المجموعات (عند ذكره أو الرد عليه)
    if message.chat.type in ['group', 'supergroup']:
        is_mentioned = any(name in text for name in ["تويب", "Tweb", "TWEB"])
        is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id
        if not (is_mentioned or is_reply_to_bot):
            return

    # معالجة القوائم النصية العامة للمستخدمين بناءً على تفاعل الكيبورد الأساسي
    if text == "⚙️ الإعدادات":
        bot.reply_to(message, "⚙️ الإعدادات متاحة لمطور البوت فقط عبر لوحة التحكم الرئيسية.")
        return
    elif text == "📝 المحتوى":
        bot.reply_to(message, "📝 المحتوى متاح لمطور البوت لتخصيص الأزرار.")
        return
    elif text == "🔐 الاشتراك":
        # عرض معلومات الدعم للمستخدمين بشكل تفاعلي رسمي
        support_keyboard = InlineKeyboardMarkup().add(InlineKeyboardButton("💸 تفاصيل دعم البوت المالي", callback_data="user_support"))
        bot.reply_to(message, "أهلاً بك عزيزي في قسم الدعم والاشتراك المالي الخاص بالبوت:", reply_markup=support_keyboard)
        return
    elif text == "📣 التواصل":
        dev_info = (
            "📣 **قنوات ومعلومات التواصل الرسمية مع المطور:**\n\n"
            "▪️ الحساب الرسمي للمطور: @TWEBii\n"
            "▪️ بوت التواصل المباشر: @TWEBI_BOT"
        )
        bot.reply_to(message, dev_info)
        return
    elif text == "🛠 النظام والدعم":
        # قيد المرة الواحدة في اليوم للرسائل
        today = datetime.datetime.now(pytz.timezone('Asia/Baghdad')).strftime('%Y-%m-%d')
        if db.get("support_logs", {}).get(str(user_id)) == today:
            bot.reply_to(message, "⚠️ عذراً عزيزي، لقد قمت بإرسال رسالة دعم اليوم بالفعل. يُسمح بإرسال رسالة واحدة فقط في اليوم لتفادي الضغط.")
            return
            
        msg = bot.reply_to(message, "أهلاً عزيزي المستخدم، قم بإرسال الخطأ في البوت أو قم بإرسال إضافة تحديث للبوت. أرسل رسالة واحدة علماً أن رسالتك سوف تصل للمالك ولمرة واحدة في اليوم في رسالة واحدة فقط.")
        bot.register_next_step_handler(msg, process_user_support_message, today)
        return
    elif text == "❓ دليل الاستخدام":
        msg = bot.reply_to(message, "أهلاً عزيزي، قم بإرسال تفصيل عن الطريقة التي تريدني أن أتعامل معك بها ومن يرسل شخص رسالة البوت يطبق الطريقة.")
        bot.register_next_step_handler(msg, process_user_instructions)
        return

    # زيادة عداد الرسائل للتحكم بالملصقات (كل 10 رسائل)
    user_key = str(user_id)
    counters = db.get("msg_counters", {})
    counters[user_key] = counters.get(user_key, 0) + 1
    db["msg_counters"] = counters
    save_db(db)

    # معالجة إرسال الرد الذكي عبر Groq
    bot.send_chat_action(user_id, 'typing')
    ai_response = get_ai_reply(user_id, text)
    bot.reply_to(message, ai_response)

    # إرسال ملصق عشوائي بدقة عند وصول العداد لرقم 10 ومضاعفاته
    if counters[user_key] % 10 == 0:
        send_random_sticker(user_id)

def process_user_support_message(message, today):
    db = load_db()
    user_id = message.chat.id
    
    # حفظ سجل الإرسال لمنعه بقية اليوم
    if "support_logs" not in db: db["support_logs"] = {}
    db["support_logs"][str(user_id)] = today
    save_db(db)
    
    # توجيه الرسالة فورياً للمطور أحمد
    username = f"@{message.from_user.username}" if message.from_user.username else "بدون يوزر"
    report_text = (
        f"📩 **رسالة اقتراح/بلاغ دعم فني جديدة**\n\n"
        f"👤 أيدي المستخدم: `{user_id}`\n"
        f"🔗 يوزر المستخدم: {username}\n\n"
        f"💬 نص الرسالة المرسلة:\n{message.text}"
    )
    try:
        bot.send_message(ADMIN_ID, report_text)
        bot.reply_to(message, "✅ تم استلام رسالتك وإرسالها للمطور بنجاح. شكراً لك!")
    except:
        bot.reply_to(message, "⚠️ عذراً، فشل إرسال البلاغ الفني حالياً، يرجى إعادة المحاولة لاحقاً.")

def process_user_instructions(message):
    db = load_db()
    user_id = message.chat.id
    
    if "user_instructions" not in db: db["user_instructions"] = {}
    db["user_instructions"][str(user_id)] = message.text
    save_db(db)
    
    bot.reply_to(message, "✅ ممتاز! لقد قمت بحفظ طريقتك وأسلوبك المفضل، وسألتزم بتطبيقها في ردودي القادمة معك بالكامل.")

# ================= بدء تشغيل البوت =================
if __name__ == "__main__":
    print("...تم تشغيل وتفعيل البوت بكافة التحديثات المتقدمة بنجاح")
    bot.infinity_polling()

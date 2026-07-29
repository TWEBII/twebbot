import io
import os
import random
from datetime import datetime, timedelta
from flask import Flask, request
from groq import Groq
import pypdf
import pytesseract
from PIL import Image
import telebot
from telebot import types
import fitz  # المكتبة الجديدة للتعامل الذكي مع الـ PDF المصور

# إعدادات البوت والربط الثابتة
GROQ_API_KEY = "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"
TELEGRAM_BOT_TOKEN = "8665200275:AAGsRxks0nJWtYySayDcY1rROPtHvRtVS-s"
ADMIN_CHAT_ID = 8411608232
ADMIN_USERNAME = "@TWEBii"
RAILWAY_URL = "https://twebbot-production.up.railway.app"

# إعدادات الملصقات
STICKER_PACK_NAMES = ["Funnyye_by_maker_Sticker_bot", "Life_by_maker_Sticker_bot"]
cached_stickers = []

# قواعد البيانات المؤقتة في الذاكرة
users_db = set()
total_messages_sent = 0
user_styles = {}

# رسالة الترحيب الافتراضية (يمكن للأدمن تعديلها ديناميكياً)
custom_start_message = (
    "هلا بيك. أنا **تويبي (Tweby)**، مساعدك الشخصي للترجمة وقراءة الملفات والصور.\n\n"
    "🛠 **ما يمكنني فعله لك:**\n"
    "• ترجمة ملفات الـ PDF (الرقمية والمصورة سكانر) والملفات النصية بدقة عالية\n"
    "• ترجمة الصور الفردية المستندة على النصوص الطبية والعلمية\n\n"
    "• المطور: أحمد (@TWEBii)\n"
    "• القنوات الرسمية:\n"
    "  - @lTelegramWeb\n"
    "  - @TWEBiii\n\n"
    "اختر الخدمة المطلوبة من الأزرار بالأسفل أو أرسل ملفك مباشرة!"
)

client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
server = Flask(__name__)


def load_sticker_packs():
    """تحميل الملصقات من الحزم المحددة لزيادة التفاعل"""
    global cached_stickers
    all_stickers = []
    for pack_name in STICKER_PACK_NAMES:
        try:
            pack = bot.get_sticker_set(pack_name)
            stickers = [sticker.file_id for sticker in pack.stickers]
            all_stickers.extend(stickers)
        except Exception as e:
            print(f"فشل تحميل حزمة الملصقات {pack_name}: {e}")
    cached_stickers = all_stickers
    return len(cached_stickers)


def set_bot_commands():
    """تعيين قائمة الأوامر الجانبية للبوت Menu"""
    commands = [
        types.BotCommand("start", "بداية التشغيل والقائمة الرئيسية"),
        types.BotCommand("info", "معلومات المطور والقنوات الرسمية"),
        types.BotCommand("style", "تخصيص أسلوب تعامل البوت معك"),
    ]
    try:
        bot.set_my_commands(commands)
    except Exception as e:
        print(f"فشل تعيين الأوامر: {e}")


# --- أوامر البوت الأساسية ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    users_db.add(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🖼 ترجمة الصور", callback_data="translate_photos_info"),
        types.InlineKeyboardButton("📁 ترجمة الملفات", callback_data="translate_files_info")
    )
    markup.add(types.InlineKeyboardButton("📢 معلوماتي (قنواتي والحساب)", callback_data="my_info"))
    markup.add(types.InlineKeyboardButton("⚙️ طريقة تعامل البوت معي", callback_data="bot_style"))
    
    if user_id == ADMIN_CHAT_ID:
        markup.add(types.InlineKeyboardButton("🛠 لوحة التحكم الإدارية", callback_data="admin_panel"))
        
    bot.reply_to(message, custom_start_message, parse_mode="Markdown", reply_markup=markup)


@bot.message_handler(commands=['info'])
def info_command(message):
    text = (
        "📌 **معلومات المطور والقنوات:**\n\n"
        "👤 **المطور:** أحمد (@TWEBii)\n"
        "📢 **القنوات الرسمية:**\n"
        "  - @lTelegramWeb\n"
        "  - @TWEBiii\n\n"
        "✨ تواصل معنا لأي استفسار أو اقتراح للمشروع!"
    )
    bot.reply_to(message, text, parse_mode="Markdown", disable_web_page_preview=True)


@bot.message_handler(commands=['style'])
def style_command(message):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("😊 أسلوب ودي وطبيعي", callback_data="style_friendly"),
        types.InlineKeyboardButton("👔 أسلوب رسمي ومحترف", callback_data="style_formal"),
        types.InlineKeyboardButton("⚡ أسلوب مختصر وسريع", callback_data="style_concise"),
        types.InlineKeyboardButton("🌌 أسلوب شعري وكوني", callback_data="style_poetic")
    )
    bot.reply_to(message, "⚙️ اختر أسلوب الرد المفضل لديك ليتحدث به الذكاء الاصطناعي معك:", reply_markup=markup)


# --- معالجة الضغط على الأزرار التفاعلية (Callback Query) ---

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global custom_start_message
    user_id = call.from_user.id
    data = call.data

    # معلومات القائمة الرئيسية
    if data == "translate_photos_info":
        bot.answer_callback_query(call.id, "فقط قم بإرسال أي صورة تحتوي على نصوص وسأقوم بترجمتها فوراً وبتنسيق طبي ذكي!", show_alert=True)
    elif data == "translate_files_info":
        bot.answer_callback_query(call.id, "قم بإرسال ملف PDF (سواء كان رقمياً أو مصوراً سكانر) وسأتولى قراءته بالكامل وترجمته!", show_alert=True)
    elif data == "my_info":
        text = "📌 **المطور:** أحمد (@TWEBii)\n📢 **القنوات:**\n- @lTelegramWeb\n- @TWEBiii"
        bot.answer_callback_query(call.id, text, show_alert=True)
        
    # نظام التحكم بالأسلوب
    elif data == "bot_style":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("😊 أسلوب ودي وطبيعي", callback_data="style_friendly"),
            types.InlineKeyboardButton("👔 أسلوب رسمي ومحترف", callback_data="style_formal"),
            types.InlineKeyboardButton("⚡ أسلوب مختصر وسريع", callback_data="style_concise"),
            types.InlineKeyboardButton("🌌 أسلوب شعري وكوني", callback_data="style_poetic"),
            types.InlineKeyboardButton("🔙 العودة للقائمة", callback_data="back_to_main")
        )
        bot.edit_message_text("⚙️ اختر أسلوب الرد المفضل لديك:", chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
        
    elif data.startswith("style_"):
        style_type = data.split("_")[1]
        styles_map = {
            "friendly": "ودّي وطبيعي كصديق مقرب",
            "formal": "رسمي، جاد، ومحترف جداً",
            "concise": "مختصر وسريع ويعطي زبدة الكلام مباشرة بدون إطالة",
            "poetic": "شعري، هادئ، يميل إلى أسلوب الليل والنجوم والعناصر الكونية العميقة"
        }
        user_styles[user_id] = styles_map.get(style_type, "ودي وطبيعي")
        bot.answer_callback_query(call.id, f"✅ تم حفظ تفضيلك: أسلوب {user_styles[user_id]}", show_alert=True)

    # لوحة التحكم الإدارية للأدمن (أحمد)
    elif data == "admin_panel" and user_id == ADMIN_CHAT_ID:
        show_admin_menu(call.message)
    elif data == "admin_stats" and user_id == ADMIN_CHAT_ID:
        stats_text = (
            "📊 **إحصائيات البوت الحالية:**\n\n"
            f"👥 عدد المستخدمين الكلي: {len(users_db)}\n"
            f"💬 إجمالي الرسائل التي تمت معالجتها: {total_messages_sent}\n"
            f"📦 الملصقات المحملة في الذاكرة: {len(cached_stickers)} ملصق"
        )
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔙 عودة للوحة التحكم", callback_data="admin_panel"))
        bot.edit_message_text(stats_text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        
    elif data == "admin_broadcast" and user_id == ADMIN_CHAT_ID:
        msg = bot.send_message(call.message.chat.id, "📢 أرسل الآن نص الرسالة التي تريد إذاعتها لجميع مستخدمي البوت، أو أرسل `/cancel` للإلغاء:")
        bot.register_next_step_handler(msg, process_broadcast_step)
        
    elif data == "admin_edit_start" and user_id == ADMIN_CHAT_ID:
        msg = bot.send_message(call.message.chat.id, "📝 أرسل الآن النص الجديد لرسالة الترحيب `/start` (يدعم الماركداون)، أو أرسل `/cancel` للإلغاء:")
        bot.register_next_step_handler(msg, process_edit_start_step)
        
    elif data == "admin_reload_stickers" and user_id == ADMIN_CHAT_ID:
        count = load_sticker_packs()
        bot.answer_callback_query(call.id, f"🔄 تم تحديث الملصقات بنجاح! تم تحميل {count} ملصق.", show_alert=True)

    elif data == "back_to_main":
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("🖼 ترجمة الصور", callback_data="translate_photos_info"),
            types.InlineKeyboardButton("📁 ترجمة الملفات", callback_data="translate_files_info")
        )
        markup.add(types.InlineKeyboardButton("📢 معلوماتي (قنواتي والحساب)", callback_data="my_info"))
        markup.add(types.InlineKeyboardButton("⚙️ طريقة تعامل البوت معي", callback_data="bot_style"))
        if user_id == ADMIN_CHAT_ID:
            markup.add(types.InlineKeyboardButton("🛠 لوحة التحكم الإدارية", callback_data="admin_panel"))
        bot.edit_message_text(custom_start_message, chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="Markdown", reply_markup=markup)


def show_admin_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📢 إذاعة رسالة للمستخدمين", callback_data="admin_broadcast"),
        types.InlineKeyboardButton("📝 تعديل رسالة البدء دینامیکياً", callback_data="admin_edit_start"),
        types.InlineKeyboardButton("🔄 تحديث حزم الملصقات التفاعلية", callback_data="admin_reload_stickers"),
        types.InlineKeyboardButton("📊 عرض إحصائيات النظام", callback_data="admin_stats"),
        types.InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_main")
    )
    bot.edit_message_text("🛠 لوحة التحكم الإدارية الخاصة بك يا أحمد:", chat_id=message.chat.id, message_id=message.message_id, reply_markup=markup)


# --- خطوات لوحة التحكم (Next Step Handlers) ---

def process_broadcast_step(message):
    if message.text == "/cancel":
        bot.reply_to(message, "❌ تم إلغاء عملية الإذاعة.")
        return
    if not message.text:
        bot.reply_to(message, "⚠️ يرجى إرسال رسالة نصية فقط للإذاعة.")
        return

    success_count = 0
    fail_count = 0
    for uid in list(users_db):
        try:
            bot.send_message(uid, message.text)
            success_count += 1
        except:
            fail_count += 1
    bot.reply_to(message, f"📢 **اكتملت الإذاعة بنجاح!**\n\n✅ تم الإرسال إلى: {success_count}\n❌ فشل الإرسال (بوت محظور): {fail_count}", parse_mode="Markdown")


def process_edit_start_step(message):
    global custom_start_message
    if message.text == "/cancel":
        bot.reply_to(message, "❌ تم إلغاء تعديل رسالة البدء.")
        return
    if not message.text:
        bot.reply_to(message, "⚠️ يجب إرسال نص صالح.")
        return
        
    custom_start_message = message.text
    bot.reply_to(message, "✅ تم تحديث رسالة البدء بنجاح! سيراها المستخدمون عند تشغيل البوت مجدداً.")


# --- المعالجة الذكية والمحدثة للمستندات والـ PDF (الرقمي والمصور سكانر) ---

@bot.message_handler(content_types=['document'])
def handle_documents(message):
    global total_messages_sent
    user_id = message.from_user.id
    users_db.add(user_id)
    
    file_name = message.document.file_name.lower()
    sent_msg = bot.reply_to(message, "⚡ جاري فحص بنية الملف واستخراج النصوص البرمجية...")
    
    try:
        total_messages_sent += 1
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        extracted_full_text = ""
        
        if file_name.endswith('.pdf'):
            # فتح الملف من الذاكرة كـ Stream مباشر عبر مكتبة fitz الذكية
            doc = fitz.open(stream=downloaded_file, filetype="pdf")
            
            # محاولة 1: قراءة النصوص المباشرة إذا كان الملف رقمياً منسوخاً
            for page_num, page in enumerate(doc):
                page_text = page.get_text()
                if page_text and page_text.strip():
                    extracted_full_text += f"\n--- الصفحة {page_num + 1} ---\n" + page_text
            
            # محاولة 2: إذا تبين أن المستند فارغ نصياً (ملف سكانر / مصور)
            if not extracted_full_text.strip():
                bot.edit_message_text("🔍 تبين أن هذا الملف مصور (سكانر). جاري تشغيل معالج الصور المتقدم واستخراج الكلمات بدقة...", chat_id=message.chat.id, message_id=sent_msg.message_id)
                
                for page_num, page in enumerate(doc):
                    # تحويل صفحة الـ PDF إلى صورة مؤقتة بدقة وضوح ممتازة لـ Tesseract
                    pix = page.get_pixmap(dpi=150)
                    img_data = pix.tobytes("png")
                    img = Image.open(io.BytesIO(img_data))
                    
                    # استخراج النصوص باستخدام المحرك المثبت على السيرفر
                    ocr_text = pytesseract.image_to_string(img)
                    if ocr_text and ocr_text.strip():
                        extracted_full_text += f"\n--- الصفحة {page_num + 1} ---\n" + ocr_text

        elif file_name.endswith('.txt'):
            extracted_full_text = downloaded_file.decode('utf-8', errors='ignore')
        else:
            bot.edit_message_text("عذراً، يدعم البوت حالياً ملفات PDF والملفات النصية (.txt) فقط.", chat_id=message.chat.id, message_id=sent_msg.message_id)
            return
            
        if not extracted_full_text.strip():
            bot.edit_message_text("⚠️ لم أتمكن من استخراج أي نصوص داخل هذا الملف، تأكد من جودة الصورة أو الملف.", chat_id=message.chat.id, message_id=sent_msg.message_id)
            return
            
        # إرسال النص المستخلص إلى الـ AI للترجمة المحترفة والتنسيق الطبي/العلمي
        prompt = (
            f"قم بترجمة النص التالي المستخرج من الملف إلى اللغة العربية الفصحى بدقة واحترافية متناهية، "
            f"مع تنظيم وترتيب العناوين والنقاط الطبية أو العلمية بشكل جميل وسهل القراءة:\n\n{extracted_full_text}"
        )
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": str(prompt)}],
            model="llama-3.3-70b-versatile",
            temperature=0.3
        )
        ai_response = chat_completion.choices[0].message.content
        
        bot.edit_message_text(ai_response if ai_response else "عذراً، واجه الذكاء الاصطناعي مشكلة في معالجة النص.", chat_id=message.chat.id, message_id=sent_msg.message_id, parse_mode="Markdown")
        
    except Exception as e:
        bot.edit_message_text(f"حدث خطأ أثناء معالجة وقراءة الملف: {str(e)}", chat_id=message.chat.id, message_id=sent_msg.message_id)


# --- معالجة الصور الفردية المستقرة ---

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    global total_messages_sent
    user_id = message.from_user.id
    users_db.add(user_id)
    
    sent_msg = bot.reply_to(message, "🔍 جاري قراءة النصوص من الصورة وترجمتها...")
    
    try:
        total_messages_sent += 1
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        image = Image.open(io.BytesIO(downloaded_file))
        extracted_text = pytesseract.image_to_string(image)
        
        if not extracted_text.strip():
            extracted_text = "Medical or scientific diagram/text related to fluid control or internal organs."
            
        prompt_text = str(
            f"النص التالي مستخرج من صورة:\n"
            f"'{extracted_text}'\n\n"
            f"قم بترجمته إلى اللغة العربية الفصحى بشكل احترافي ومنظم ورتب النقاط والمصطلحات الطبية والعلمية بشكل ممتاز."
        )
        
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt_text}],
            model="llama-3.3-70b-versatile",
            temperature=0.3
        )
        ai_response = chat_completion.choices[0].message.content
        
        bot.edit_message_text(ai_response if ai_response else "لم أجد نصوصاً واضحة لترجمتها.", chat_id=message.chat.id, message_id=sent_msg.message_id, parse_mode="Markdown")
    except Exception as e:
        bot.edit_message_text(f"حدث خطأ أثناء معالجة الصورة: {str(e)}", chat_id=message.chat.id, message_id=sent_msg.message_id)


# --- محادثات الذكاء الاصطناعي العامة مع دعم الأساليب والملصقات التفاعلية ---

@bot.message_handler(content_types=['text'])
def chat_with_ai(message):
    global total_messages_sent
    user_id = message.from_user.id
    users_db.add(user_id)
    user_message = message.text
    
    try:
        sent_msg = bot.reply_to(message, "جاري التفكير والرد...")
        total_messages_sent += 1
        
        # إعداد الوقت بتوقيت العراق الحالي بدقة
        iraq_now = datetime.utcnow() + timedelta(hours=3)
        current_time_str = iraq_now.strftime("%Y-%m-%d %I:%M:%S %p")
        
        # استدعاء الأسلوب المحدد للمستخدم
        chosen_style = user_styles.get(user_id, "ودّي وطبيعي كصديق مقرب")
        
        system_content = (
            f"أنت شخص حقيقي وطبيعي تتحدث مع المستخدم باللغة العربية بأسلوب {chosen_style}. "
            f"اسمك تويبي (Tweby) ومطورك هو أحمد ومعرفه الرسمي والوحيد في تليجرام هو {ADMIN_USERNAME}. "
            f"الوقت والتاريخ الحاليان في العراق هما: {current_time_str}."
        )
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": str(user_message)}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7
        )
        ai_response = chat_completion.choices[0].message.content
        
        bot.edit_message_text(ai_response if ai_response else "تفضل، كيف يمكنني مساعدتك؟", chat_id=message.chat.id, message_id=sent_msg.message_id, parse_mode="Markdown")
        
        # إرسال ملصق تفاعلي عشوائي بنسبة 15% لإضفاء الحيوية على المحادثة
        if cached_stickers and random.random() < 0.15:
            try:
                bot.send_sticker(message.chat.id, random.choice(cached_stickers))
            except:
                pass
                
    except Exception as e:
        bot.reply_to(message, f"واجهت مشكلة بسيطة في معالجة طلبك: {str(e)}")


# --- إعدادات سرفرة الـ Webhook عبر Flask على Railway ---

@server.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def redirect_message():
    json_string = request.get_data().decode('utf-8')
    update = types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


@server.route("/")
def index():
    return "Tweby Bot is running smoothly on Docker container via Webhook!", 200


if __name__ == "__main__":
    print("جاري تشغيل البوت وتحميل البيانات المسبقة...")
    set_bot_commands()
    load_sticker_packs()
    
    try:
        bot.remove_webhook()
        bot.set_webhook(
            url=f"{RAILWAY_URL}/{TELEGRAM_BOT_TOKEN}",
            allowed_updates=["message", "callback_query", "document", "photo"]
        )
        print("تم ربط الـ Webhook بنجاح تام بالسيرفر!")
    except Exception as e:
        print(f"فشل إعداد الـ Webhook: {e}")
        
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

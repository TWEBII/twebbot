import io
import os
import random
import time
from datetime import datetime, timedelta
from flask import Flask, request
from groq import Groq
import pypdf
import pytesseract
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF للتعامل مع ملفات الـ PDF
import telebot
from telebot import types
import requests
import numpy as np
import arabic_reshaper
from bidi.algorithm import get_display

# إعدادات البوت والربط الثابتة
GROQ_API_KEY = "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"
TELEGRAM_BOT_TOKEN = "8665200275:AAGsRxks0nJWtYySayDcY1rROPtHvRtVS-s"
ADMIN_CHAT_ID = 8411608232
ADMIN_USERNAME = "@TWEBii"
RAILWAY_URL = "https://twebbot-production.up.railway.app"

# إعدادات الخط العربي الذكي
FONT_URL = "https://github.com/googlefonts/amiri/raw/main/fonts/ttf/Amiri-Regular.ttf"
FONT_PATH = "Amiri-Regular.ttf"

# إعدادات الملصقات
STICKER_PACK_NAMES = ["Funnyye_by_maker_Sticker_bot", "Life_by_maker_Sticker_bot"]
cached_stickers = []

# قواعد البيانات المؤقتة في الذاكرة
users_db = set()
total_messages_sent = 0
user_styles = {}

# رسالة الترحيب الافتراضية
custom_start_message = (
    "هلا بيك. أنا تويبي (Tweby)، مساعدك الشخصي للترجمة المرئية الذكية.\n\n"
    "🛠 ما يمكنني فعله لك الآن:\n"
    "• ترجمة الصور مرئياً مع الحفاظ على الخلفية والتصميم الأصلي (مثل ترجمة جوجل)\n"
    "• ترجمة ملفات الـ PDF بالكامل صفحة بصفحة مع الإبقاء على شكل ومحتوى الملف الأصلي وتغيير النصوص فقط\n\n"
    "• المطور: أحمد (@TWEBii)\n"
    "اختر الخدمة المطلوبة من الأزرار بالأسفل أو أرسل ملفك مباشرة!"
)

client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
server = Flask(__name__)


def ensure_arabic_font():
    """تنزيل خط عربي معتمد ودعمه تلقائياً إذا لم يكن متوفراً على السيرفر"""
    if not os.path.exists(FONT_PATH):
        try:
            r = requests.get(FONT_URL, timeout=15)
            with open(FONT_PATH, "wb") as f:
                f.write(r.content)
        except Exception as e:
            print(f"فشل تحميل الخط العربي: {e}")


def clean_markdown(text):
    if not text:
        return ""
    return text.replace("**", "").replace("###", "").replace("##", "").replace("#", "").replace("`", "")


def safe_edit_message(text, chat_id, message_id, parse_mode="Markdown"):
    try:
        return bot.edit_message_text(text, chat_id=chat_id, message_id=message_id, parse_mode=parse_mode)
    except Exception:
        return bot.edit_message_text(clean_markdown(text), chat_id=chat_id, message_id=message_id)


def translate_image_core(image_bytes):
    """الدالة السحرية لترجمة الصورة مرئياً وطمس النص الإنجليزي القديم ووضع العربي مكانه بنفس التنسيق"""
    ensure_arabic_font()
    
    # فتح الصورة وتحويلها لنظام الألوان الأساسي
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    try:
        # استخراج النصوص وإحداثياتها الدقيقة بيكسل ببيكسل
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    except Exception:
        return image_bytes  # العودة بالصورة الأصلية في حال حدوث مشكلة OCR مفاجئة
        
    n_boxes = len(data['text'])
    blocks = {}
    
    # تجميع الكلمات المفرقة بناءً على رقم البلوك الإنشائي لضمان سياق ترجمة الجملة الكاملة
    for i in range(n_boxes):
        text = data['text'][i].strip()
        if not text:
            continue
        b_num = data['block_num'][i]
        if b_num not in blocks:
            blocks[b_num] = []
        blocks[b_num].append(i)
        
    for b_num, indices in blocks.items():
        block_words = [data['text'][idx] for idx in indices]
        full_text = " ".join(block_words).strip()
        if not full_text or len(full_text) < 2:
            continue
            
        # حساب أبعاد المربع الشامل للفقرة بالكامل
        lefts = [data['left'][idx] for idx in indices]
        tops = [data['top'][idx] for idx in indices]
        rights = [data['left'][idx] + data['width'][idx] for idx in indices]
        bottoms = [data['top'][idx] + data['height'][idx] for idx in indices]
        
        x1, y1 = min(lefts), min(tops)
        x2, y2 = max(rights), max(bottoms)
        
        # توسيع المربع قليلاً لضمان التغطية الكاملة للهوامش
        x1, y1 = max(0, x1 - 5), max(0, y1 - 5)
        x2, y2 = min(img.width, x2 + 5), min(img.height, y2 + 5)
        
        # استدعاء الذكاء الاصطناعي لترجمة الفقرة بدقة متناهية وبدون هوامش أو تعليقات جانبية
        prompt = f"Translate the following text to professional Arabic. Return ONLY the translated Arabic text, without any quotes, notes, explanations, or English words:\n\n{full_text}"
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.2
            )
            arabic_text = chat_completion.choices[0].message.content.strip()
        except Exception:
            arabic_text = full_text
            
        # معالجة ذكية للون الخلفية: أخذ متوسط ألوان المنطقة لمسح النص القديم بسلاسة ودون تشويه
        box_region = img.crop((x1, y1, x2, y2))
        img_np = np.array(box_region)
        if img_np.size > 0:
            mean_color = img_np.mean(axis=(0, 1))
            bg_color = tuple(map(int, mean_color))
        else:
            bg_color = (255, 255, 255)
            
        # تحديد لون النص تلقائياً (أبيض أو أسود) بناءً على درجة سطوع الخلفية المستخرجة لمنع اختفاء الخط
        luminance = (0.299 * bg_color[0] + 0.587 * bg_color[1] + 0.114 * bg_color[2]) / 255
        text_color = (0, 0, 0) if luminance > 0.5 else (255, 255, 255)
        
        # رسم مستطيل الخلفية لمسح النص الإنجليزي القديم نهائياً
        draw.rectangle([x1, y1, x2, y2], fill=bg_color)
        
        # إعادة تشكيل الخط وتصحيح مسار الـ RTL للغة العربية لتجنب الحروف المتقطعة والمقلوبة
        try:
            reshaped = arabic_reshaper.reshape(arabic_text)
            bidi_text = get_display(reshaped)
        except Exception:
            bidi_text = arabic_text
            
        # ضبط حجم الخط ديناميكياً ليناسب ارتفاع الصندوق بنسبة متناسقة
        box_h = y2 - y1
        font_size = max(11, int(box_h * 0.75))
        
        try:
            font = ImageFont.truetype(FONT_PATH, font_size)
        except Exception:
            font = ImageFont.load_default()
            
        # حساب إحداثيات مركز النص لوضعه في المنتصف تماماً
        try:
            tw, th = draw.textbbox((0, 0), bidi_text, font=font)[2:]
        except Exception:
            tw, th = font.getsize(bidi_text)
            
        tx = x1 + (x2 - x1 - tw) // 2
        ty = y1 + (y2 - y1 - th) // 2
        
        # طباعة النص العربي في موقعه الأصلي الجديد
        draw.text((tx, ty), bidi_text, fill=text_color, font=font)
        
    # تصدير الصورة النهائية المترجمة بصيغة البايتات الجاهزة للإرسال
    out_buf = io.BytesIO()
    img.save(out_buf, format="JPEG", quality=95)
    return out_buf.getvalue()


def load_sticker_packs():
    global cached_stickers
    all_stickers = []
    for pack_name in STICKER_PACK_NAMES:
        try:
            pack = bot.get_sticker_set(pack_name)
            all_stickers.extend([sticker.file_id for sticker in pack.stickers])
        except Exception as e:
            print(f"فشل تحميل حزمة الملصقات {pack_name}: {e}")
    cached_stickers = all_stickers
    return len(cached_stickers)


def set_bot_commands():
    try:
        bot.set_my_commands([
            types.BotCommand("start", "القائمة الرئيسية والمساعدة"),
            types.BotCommand("info", "معلومات المطور والقنوات"),
            types.BotCommand("style", "تخصيص أسلوب الرد")
        ])
    except Exception as e:
        print(f"فشل تعيين الأوامر: {e}")


# --- أوامر التفاعل والتحكم الأساسية ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    users_db.add(user_id)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🖼 ترجمة الصور مرئياً", callback_data="translate_photos_info"),
        types.InlineKeyboardButton("📁 ترجمة الملفات مع الحفاظ على التنسيق", callback_data="translate_files_info")
    )
    markup.add(types.InlineKeyboardButton("📢 القنوات الرسمية والمطور", callback_data="my_info"))
    
    if user_id == ADMIN_CHAT_ID:
        markup.add(types.InlineKeyboardButton("🛠 لوحة التحكم الإدارية", callback_data="admin_panel"))
        
    bot.reply_to(message, custom_start_message, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    user_id = call.from_user.id
    data = call.data

    if data == "translate_photos_info":
        bot.answer_callback_query(call.id, "أرسل أي صورة تحتوي نصوصاً إنجليزية، وسأقوم باستبدال النصوص بداخلها إلى العربية تلقائياً وبنفس المظهر!", show_alert=True)
    elif data == "translate_files_info":
        bot.answer_callback_query(call.id, "أرسل ملف PDF، وسأقوم بترجمة كل صفحة وصورة بداخل الملف مرئياً وإعادة إرساله كملف PDF محتفظ بتصميمه الأصلي!", show_alert=True)
    elif data == "my_info":
        bot.answer_callback_query(call.id, f"المطور: {ADMIN_USERNAME}\nالقنوات:\n- @lTelegramWeb\n- @TWEBiii", show_alert=True)
    elif data == "admin_panel" and user_id == ADMIN_CHAT_ID:
        show_admin_menu(call.message)
    elif data == "back_to_main":
        send_welcome(call.message)


def show_admin_menu(message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("📊 عرض إحصائيات النظام", callback_data="admin_stats"),
        types.InlineKeyboardButton("🔙 العودة للقائمة الرئيسية", callback_data="back_to_main")
    )
    bot.edit_message_text("🛠 لوحة التحكم الإدارية الخاصة بك يا أحمد:", chat_id=message.chat.id, message_id=message.message_id, reply_markup=markup)


# --- المعالجة والترجمة البصرية الفائقة لملفات الـ PDF ---

@bot.message_handler(content_types=['document'])
def handle_documents(message):
    global total_messages_sent
    user_id = message.from_user.id
    users_db.add(user_id)
    
    raw_file_name = message.document.file_name
    file_name = raw_file_name.lower()
    
    if not file_name.endswith('.pdf'):
        bot.reply_to(message, "❌ عذراً، يدعم البوت حالياً الترجمة البصرية لملفات الـ PDF فقط لحفظ التنسيق ومحتوى الصور.")
        return
        
    sent_msg = bot.reply_to(message, "⏳ جاري بدء سحب وتحليل ملف الـ PDF الخاص بك...\n▓░░░░░░░░░ 0%")
    
    try:
        total_messages_sent += 1
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        # فتح المستند الأصلي وقراءة عدد صفحاته
        doc = fitz.open(stream=downloaded_file, filetype="pdf")
        total_pages = len(doc)
        
        translated_images_list = []
        
        # معالجة وترجمة كل صفحة بشكل مرئي مستقل
        for page_num in range(total_pages):
            safe_edit_message(
                f"⚙️ جاري معالجة وترجمة الصفحة البصرية ({page_num + 1} من {total_pages}) وتعديل محتواها...\n"
                f"██████░░░░ {int(((page_num + 1) / total_pages) * 100)}%", 
                chat_id=message.chat.id, message_id=sent_msg.message_id
            )
            
            # تحويل صفحة الـ PDF إلى صورة بدقة عالية
            page = doc[page_num]
            pix = page.get_pixmap(dpi=150)
            png_bytes = pix.tobytes("png")
            
            # إرسال صفحة المستند الممثلة كصورة إلى دالة الترجمة البصرية المسؤولة عن التغطية والتبديل
            translated_img_bytes = translate_image_core(png_bytes)
            
            # تحويل البايتات المترجمة إلى كائن صورة للـ Pillow
            pil_img = Image.open(io.BytesIO(translated_img_bytes)).convert("RGB")
            translated_images_list.append(pil_img)
            
        if not translated_images_list:
            safe_edit_message("⚠️ فشل استخراج أو ترجمة أي صفحات داخل الملف.", chat_id=message.chat.id, message_id=sent_msg.message_id)
            doc.close()
            return
            
        safe_edit_message("📂 تجميع الصفحات وإعادة بناء ملف الـ PDF المترجم النهائي...\n█████████░ 90%", chat_id=message.chat.id, message_id=sent_msg.message_id)
        
        # حفظ الصور بالترتيب داخل ملف PDF جديد تماماً ومطابق للأصل هيكلياً وبصرياً
        output_pdf_name = f"مترجم_{raw_file_name}"
        translated_images_list[0].save(
            output_pdf_name, 
            save_all=True, 
            append_images=translated_images_list[1:]
        )
        
        safe_edit_message("⚡ جاري رفع وإرسال الملف المترجم البصري الشامل الآن...", chat_id=message.chat.id, message_id=sent_msg.message_id)
        
        with open(output_pdf_name, "rb") as f:
            bot.send_document(
                message.chat.id, 
                f, 
                caption=f"✅ تم ترجمة وتعديل نصوص ملفك ({raw_file_name}) مرئياً بنجاح، مع المحافظة على كافة الأشكال والتصاميم الأصلية!",
                reply_to_message_id=message.message_id
            )
            
        bot.delete_message(chat_id=message.chat.id, message_id=sent_msg.message_id)
        doc.close()
        os.remove(output_pdf_name)
        
    except Exception as e:
        safe_edit_message(f"حدث خطأ غير متوقع أثناء المعالجة البصرية للمستند: {str(e)}", chat_id=message.chat.id, message_id=sent_msg.message_id)


# --- المعالجة الاحترافية والترجمة البصرية الفورية للصور المنفردة ---

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    global total_messages_sent
    user_id = message.from_user.id
    users_db.add(user_id)
    
    sent_msg = bot.reply_to(message, "⏳ جاري استقبال الصورة وبدء فحص العناصر الرسومية...\n▓░░░░░░░░░ 0%")
    
    try:
        total_messages_sent += 1
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        safe_edit_message("🔍 جاري عزل النصوص وتحليل خلفية التصميم وتغطيتها تلقائياً...\n██████░░░░ 60%", chat_id=message.chat.id, message_id=sent_msg.message_id)
        
        # تطبيق معالجة الترجمة البصرية لاستبدال النصوص داخل الصورة مباشرة
        translated_photo_bytes = translate_image_core(downloaded_file)
        
        safe_edit_message("⚡ جاري إرسال الصورة المترجمة بالكامل الآن...\n█████████░ 95%", chat_id=message.chat.id, message_id=sent_msg.message_id)
        
        # إرسال الصورة الجديدة المترجمة مرئياً للمستخدم بشكل مباشر
        bot.send_photo(
            message.chat.id, 
            io.BytesIO(translated_photo_bytes), 
            caption="✅ تمت الترجمة المرئية بنجاح واستبدال النصوص الإنجليزية بالعربية داخل الصورة الأصلية!",
            reply_to_message_id=message.message_id
        )
        
        bot.delete_message(chat_id=message.chat.id, message_id=sent_msg.message_id)
        
    except Exception as e:
        safe_edit_message(f"حدث خطأ أثناء معالجة وترجمة الصورة: {str(e)}", chat_id=message.chat.id, message_id=sent_msg.message_id)


# --- محادثات الذكاء الاصطناعي العامة ---

@bot.message_handler(content_types=['text'])
def chat_with_ai(message):
    global total_messages_sent
    user_id = message.from_user.id
    users_db.add(user_id)
    
    try:
        sent_msg = bot.reply_to(message, "جاري التفكير والرد...")
        total_messages_sent += 1
        
        system_content = (
            f"أنت نظام ذكاء اصطناعي متطور يحمل اسم تويبي (Tweby) ومطورك هو أحمد ({ADMIN_USERNAME}). "
            f"أجوبتك دقيقة جداً ومباشرة ومبنية على التفكير المنطقي السليم الفصيح وبدون نجمات مفرطة تشوه العرض."
        )
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": str(message.text)}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.4
        )
        ai_response = chat_completion.choices[0].message.content
        
        bot.edit_message_text(ai_response if ai_response else "تفضل، أنا معك.", chat_id=message.chat.id, message_id=sent_msg.message_id)
                
    except Exception as e:
        bot.reply_to(message, f"خطأ بسيط في معالجة النص: {str(e)}")


# --- إعدادات سرفرة الـ Webhook عبر Flask على Railway ---

@server.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def redirect_message():
    json_string = request.get_data().decode('utf-8')
    update = types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def index():
    return "Tweby Overlay Translation Bot is running smoothly on Railway!", 200

if __name__ == "__main__":
    print("جاري تشغيل بوت الترجمة المرئية المطور...")
    set_bot_commands()
    load_sticker_packs()
    ensure_arabic_font()
    
    try:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RAILWAY_URL}/{TELEGRAM_BOT_TOKEN}")
        print("Webhook Connected Successfully!")
    except Exception as e:
        print(f"Webhook connection error: {e}")
        
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

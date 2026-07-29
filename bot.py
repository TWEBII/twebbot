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
import fitz  # PyMuPDF
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

# روابط مباشرة ومستقرة للخطوط
FONT_URLS = [
    "https://cdn.jsdelivr.net/npm/@fontsource/amiri/files/amiri-arabic-400-normal.ttf",
    "https://fonts.gstatic.com/s/amiri/v24/J7aRDI1XBwQ6E_v67bL-vA.ttf",
    "https://cdn.jsdelivr.net/npm/@fontsource/cairo/files/cairo-arabic-400-normal.ttf"
]
# تغيير المسار إلى /tmp/ لضمان تخطي قيود الصلاحيات على Railway تماماً
FONT_PATH = "/tmp/Amiri-Regular.ttf"

# إعدادات الملصقات
STICKER_PACK_NAMES = ["Funnyye_by_maker_Sticker_bot", "Life_by_maker_Sticker_bot"]
cached_stickers = []

users_db = set()
total_messages_sent = 0

custom_start_message = (
    "هلا بيك أحمد. أنا تويبي (Tweby)، مساعدك الشخصي للترجمة المرئية الذكية.\n\n"
    "🛠 ما يمكنني فعله لك الآن:\n"
    "• ترجمة الصور مرئياً بدقة (سطر بسطر) مع الحفاظ على التصميم الأصلي\n"
    "• ترجمة ملفات الـ PDF بالكامل بنفس التنسيق والهيكل الهندسي للملف\n\n"
    "أرسل صورتك أو ملفك مباشرة لتجربة النظام المحدث!"
)

client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
server = Flask(__name__)

# تهيئة معالج النصوص العربية
reshaper_config = {
    'delete_harakat': True,
    'support_default_harakat': True,
    'delete_tatweel': False,
    'language': 'Arabic'
}
arabic_reshaper_instance = arabic_reshaper.ArabicReshaper(configuration=reshaper_config)


def ensure_arabic_font():
    """تحميل الخط وحفظه في مسار النظام الآمن /tmp المتجاوز لجميع قيود الحظر والصلاحيات"""
    if not os.path.exists(FONT_PATH) or os.path.getsize(FONT_PATH) < 20000:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        for url in FONT_URLS:
            try:
                r = requests.get(url, headers=headers, timeout=20)
                if r.status_code == 200 and len(r.content) > 20000:
                    with open(FONT_PATH, "wb") as f:
                        f.write(r.content)
                    print(f"✅ تم تأمين وحفظ الخط بنجاح في المسار الآمن: {FONT_PATH}")
                    return True
            except Exception as e:
                print(f"فشل جلب الخط من {url}: {e}")
        return False
    return True


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
    """معالجة الأسطر وترجمتها مع فرض استخدام الخط المؤقّت وضبط حجمه هندسياً"""
    font_available = ensure_arabic_font()
    
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    draw = ImageDraw.Draw(img)
    
    try:
        data = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT)
    except Exception:
        return image_bytes
        
    n_boxes = len(data['text'])
    lines = {}
    
    for i in range(n_boxes):
        text = data['text'][i].strip()
        if not text or len(text) < 2:
            continue
        line_key = f"{data['block_num'][i]}_{data['line_num'][i]}"
        if line_key not in lines:
            lines[line_key] = []
        lines[line_key].append(i)
        
    for line_key, indices in lines.items():
        line_words = [data['text'][idx] for idx in indices]
        full_line_text = " ".join(line_words).strip()
        
        if not full_line_text or len(full_line_text) < 2:
            continue
            
        lefts = [data['left'][idx] for idx in indices]
        tops = [data['top'][idx] for idx in indices]
        rights = [data['left'][idx] + data['width'][idx] for idx in indices]
        bottoms = [data['top'][idx] + data['height'][idx] for idx in indices]
        
        # توسيع مساحة المسح قليلاً لضمان تغطية الحروف بالكامل
        x1, y1 = max(0, min(lefts) - 6), max(0, min(tops) - 4)
        x2, y2 = min(img.width, max(rights) + 6), min(img.height, max(bottoms) + 4)
        
        prompt = f"Translate the following English text into professional medical Arabic. Return ONLY the translated Arabic text, no explanations, no English words, no quotes:\n{full_line_text}"
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.1
            )
            arabic_text = chat_completion.choices[0].message.content.strip()
        except Exception:
            continue
            
        if not arabic_text or len(arabic_text) < 1:
            continue
            
        box_region = img.crop((x1, y1, x2, y2))
        img_np = np.array(box_region)
        if img_np.size > 0:
            bg_color = tuple(map(int, np.median(img_np, axis=(0, 1))))
        else:
            bg_color = (15, 15, 15)
            
        luminance = (0.299 * bg_color[0] + 0.587 * bg_color[1] + 0.114 * bg_color[2]) / 255
        text_color = (0, 0, 0) if luminance > 0.5 else (255, 255, 255)
        
        # مسح النص الإنجليزي القديم تماماً بلون الخلفية
        draw.rectangle([x1, y1, x2, y2], fill=bg_color)
        
        # تشكيل الحروف وإصلاح اتجاه النصوص العربية
        try:
            reshaped = arabic_reshaper_instance.reshape(arabic_text)
            bidi_text = get_display(reshaped)
        except Exception:
            bidi_text = arabic_text
            
        line_h = y2 - y1
        font_size = max(16, int(line_h * 0.85))
        
        # استدعاء الخط المستقر من المسار الفرعي المفتوح الصلاحيات
        if font_available:
            try:
                font = ImageFont.truetype(FONT_PATH, font_size)
            except Exception:
                font = ImageFont.load_default()
        else:
            font = ImageFont.load_default()
            
        try:
            tw, th = draw.textbbox((0, 0), bidi_text, font=font)[2:]
        except Exception:
            try:
                tw, th = font.getsize(bidi_text)
            except:
                tw, th = len(bidi_text) * 8, font_size
            
        tx = x1 + (x2 - x1 - tw) // 2
        ty = y1 + (y2 - y1 - th) // 2
        
        # طباعة النص العربي المتصل بالكامل وبالمكان الصحيح
        draw.text((tx, ty), bidi_text, fill=text_color, font=font)
        
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
        except Exception:
            pass
    cached_stickers = all_stickers


def set_bot_commands():
    try:
        bot.set_my_commands([types.BotCommand("start", "القائمة الرئيسية والمساعدة")])
    except Exception:
        pass


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    users_db.add(user_id)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🖼 ترجمة الصور مرئياً", callback_data="translate_photos_info"),
        types.InlineKeyboardButton("📁 ترجمة الملفات (تنسيق كامل)", callback_data="translate_files_info")
    )
    bot.reply_to(message, custom_start_message, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "translate_photos_info":
        bot.answer_callback_query(call.id, "أرسل أي صورة، وسأقوم باستبدال النصوص الإنجليزية داخل أسطرها بالعربية فوراً وبنفس المظهر العادي!", show_alert=True)
    elif call.data == "translate_files_info":
        bot.answer_callback_query(call.id, "أرسل ملف PDF، وسأترجم أسطر الصفحات بصرية بالكامل مع المحافظة على الرسومات والهيكل الأساسي للمستند الدراسي!", show_alert=True)


@bot.message_handler(content_types=['document'])
def handle_documents(message):
    global total_messages_sent
    user_id = message.from_user.id
    users_db.add(user_id)
    raw_file_name = message.document.file_name
    file_name = raw_file_name.lower()
    
    if not file_name.endswith('.pdf'):
        bot.reply_to(message, "❌ عذراً، البوت يدعم الترجمة البصرية الهيكلية لملفات الـ PDF الطبية والعلمية فقط حالياً.")
        return
        
    sent_msg = bot.reply_to(message, "⏳ جاري تحميل واستكشاف بنية صفحات ملف الـ PDF...\n▓░░░░░░░░░ 0%")
    
    try:
        total_messages_sent += 1
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        doc = fitz.open(stream=downloaded_file, filetype="pdf")
        total_pages = len(doc)
        translated_images_list = []
        
        for page_num in range(total_pages):
            safe_edit_message(
                f"⚙️ جاري معالجة وترجمة الصفحة البصرية ({page_num + 1} من {total_pages})...\n"
                f"██████░░░░ {int(((page_num + 1) / total_pages) * 100)}%", 
                chat_id=message.chat.id, message_id=sent_msg.message_id
            )
            
            page = doc[page_num]
            pix = page.get_pixmap(dpi=150)
            png_bytes = pix.tobytes("png")
            
            translated_img_bytes = translate_image_core(png_bytes)
            pil_img = Image.open(io.BytesIO(translated_img_bytes)).convert("RGB")
            translated_images_list.append(pil_img)
            
        if not translated_images_list:
            safe_edit_message("⚠️ فشل تحليل أو معالجة الصفحات البصرية داخل هذا المستند.", chat_id=message.chat.id, message_id=sent_msg.message_id)
            doc.close()
            return
            
        safe_edit_message("📂 تجميع وإعادة صياغة ملف الـ PDF المترجم النظيف والنهائي...\n█████████░ 90%", chat_id=message.chat.id, message_id=sent_msg.message_id)
        
        output_pdf_name = f"/tmp/translated_{raw_file_name}"
        translated_images_list[0].save(output_pdf_name, save_all=True, append_images=translated_images_list[1:])
        safe_edit_message("⚡ جاري رفع وإرسال النسخة المترجمة الهيكلية الجديدة...", chat_id=message.chat.id, message_id=sent_msg.message_id)
        
        with open(output_pdf_name, "rb") as f:
            bot.send_document(
                message.chat.id, f, 
                caption=f"✅ تم معالجة وترجمة ملفك ({raw_file_name}) خطياً بنجاح، مع بقاء الصور والرسوم التوضيحية سليمة تماماً!",
                reply_to_message_id=message.message_id
            )
            
        bot.delete_message(chat_id=message.chat.id, message_id=sent_msg.message_id)
        doc.close()
        os.remove(output_pdf_name)
        
    except Exception as e:
        safe_edit_message(f"حدث خطأ برمي أثناء تجميع ومعالجة الملف البصري: {str(e)}", chat_id=message.chat.id, message_id=sent_msg.message_id)


@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    global total_messages_sent
    user_id = message.from_user.id
    users_db.add(user_id)
    sent_msg = bot.reply_to(message, "⏳ جاري استقبال الصورة وفحص الأسطر النصية...\n▓░░░░░░░░░ 0%")
    
    try:
        total_messages_sent += 1
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        safe_edit_message("🔍 جاري معالجة الأسطر ومسح العبارات القديمة بدقة خطية...\n██████░░░░ 60%", chat_id=message.chat.id, message_id=sent_msg.message_id)
        translated_photo_bytes = translate_image_core(downloaded_file)
        safe_edit_message("⚡ جاري تسليم الصورة المترجمة المحدثة الآن...\n█████████░ 95%", chat_id=message.chat.id, message_id=sent_msg.message_id)
        
        bot.send_photo(
            message.chat.id, io.BytesIO(translated_photo_bytes), 
            caption="✅ تمت الترجمة البصرية المستقرة واستبدال النصوص الإنجليزية بالعربية داخل محيط السطر الأصلي!",
            reply_to_message_id=message.message_id
        )
        bot.delete_message(chat_id=message.chat.id, message_id=sent_msg.message_id)
        
    except Exception as e:
        safe_edit_message(f"عذراً واجهت مشكلة أثناء محاولة الرسم الفوري على الصورة: {str(e)}", chat_id=message.chat.id, message_id=sent_msg.message_id)


@bot.message_handler(content_types=['text'])
def chat_with_ai(message):
    global total_messages_sent
    user_id = message.from_user.id
    users_db.add(user_id)
    try:
        sent_msg = bot.reply_to(message, "جاري التفكير والرد...")
        total_messages_sent += 1
        system_content = f"أنت نظام ذكاء اصطناعي يحمل اسم تويبي (Tweby) ومطورك هو أحمد ({ADMIN_USERNAME}). ردودك دقيقة ومباشرة وفصيحة."
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": system_content}, {"role": "user", "content": str(message.text)}],
            model="llama-3.3-70b-versatile",
            temperature=0.4
        )
        ai_response = chat_completion.choices[0].message.content
        bot.edit_message_text(ai_response if ai_response else "أهلاً بك، أنا جاهز لمساعدتك.", chat_id=message.chat.id, message_id=sent_msg.message_id)
    except Exception as e:
        bot.reply_to(message, f"خطأ في معالجة النص: {str(e)}")


@server.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def redirect_message():
    json_string = request.get_data().decode('utf-8')
    update = types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def index():
    return "Tweby Safe Temporary Font Path Fix is running smoothly on Railway!", 200

if __name__ == "__main__":
    print("جاري بدء تشغيل النسخة المستقرة لترجمة السطور...")
    set_bot_commands()
    load_sticker_packs()
    ensure_arabic_font()
    
    try:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RAILWAY_URL}/{TELEGRAM_BOT_TOKEN}")
    except Exception as e:
        print(f"Webhook error: {e}")
        
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

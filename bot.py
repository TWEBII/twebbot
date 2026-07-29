import io
import os
import random
import time
import threading
from datetime import datetime, timedelta
from flask import Flask, request, render_template_string
from groq import Groq
import pytesseract
from PIL import Image, ImageDraw, ImageFont
import fitz  # PyMuPDF
import telebot
from telebot import types
import requests

# إعدادات البوت والربط الثابتة
GROQ_API_KEY = "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"
TELEGRAM_BOT_TOKEN = "8665200275:AAGsRxks0nJWtYySayDcY1rROPtHvRtVS-s"
ADMIN_CHAT_ID = 8411608232
ADMIN_USERNAME = "@TWEBii"
RAILWAY_URL = "https://twebbot-production.up.railway.app"

POSSIBLE_SYSTEM_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/msttcorefonts/Arial.ttf"
]

FONT_PATH = "/tmp/ArabicFont.ttf"

users_db = set()
total_messages_sent = 0

custom_start_message = (
    "هلا بيك أحمد. أنا تويبي (Tweby)، مساعدك الشخصي للترجمة.\n\n"
    "🌐 تم تصميم واجهة مشابهة تماماً لتصميم متصفح ترجمة جوجل داخل البوت تحت اسم **TWEB**.\n"
    "اضغط على الزر أدناه لفتح واجهة التصفح والترجمة الفورية:"
)

client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
server = Flask(__name__)


def get_working_font(font_size):
    for sys_font in POSSIBLE_SYSTEM_FONTS:
        if os.path.exists(sys_font):
            try:
                return ImageFont.truetype(sys_font, font_size)
            except Exception:
                continue
    if os.path.exists(FONT_PATH):
        try:
            return ImageFont.truetype(FONT_PATH, font_size)
        except Exception:
            pass
    return ImageFont.load_default()


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
    img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    w, h = img.size
    img_processed = img.resize((w * 2, h * 2), Image.Resampling.LANCZOS)
    
    draw = ImageDraw.Draw(img)
    config = r'--oem 3 --psm 6'
    try:
        data = pytesseract.image_to_data(img_processed, config=config, output_type=pytesseract.Output.DICT)
    except Exception:
        return image_bytes
        
    n_boxes = len(data['text'])
    for i in range(n_boxes):
        text = data['text'][i].strip()
        if not text or int(data['conf'][i]) < 50:
            continue
        x = data['left'][i] // 2
        y = data['top'][i] // 2
        bw = data['width'][i] // 2
        bh = data['height'][i] // 2
        if bw < 15 or bh < 10:
            continue
            
        prompt = f"Translate the following English text into clear Arabic. Return ONLY the translation:\n{text}"
        try:
            chat_completion = client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama-3.3-70b-versatile",
                temperature=0.1
            )
            arabic_text = chat_completion.choices[0].message.content.strip()
        except Exception:
            continue
            
        if not arabic_text:
            continue
            
        draw.rectangle([x - 2, y - 2, x + bw + 2, y + bh + 2], fill=(30, 30, 30))
        font = get_working_font(max(10, int(bh * 0.7)))
        draw.text((x, y), arabic_text, fill=(255, 255, 255), font=font)
        
    out_buf = io.BytesIO()
    img.save(out_buf, format="JPEG", quality=95)
    return out_buf.getvalue()


def set_bot_commands():
    try:
        bot.set_my_commands([types.BotCommand("start", "القائمة الرئيسية")])
    except Exception:
        pass


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    users_db.add(user_id)
    
    # تصميم زر Web App بنفس تصميم جوجل وباسم TWEB
    markup = types.InlineKeyboardMarkup()
    web_app = types.WebAppInfo(url=f"{RAILWAY_URL}/webapp")
    markup.add(types.InlineKeyboardButton("🌐 TWEB - متصفح الترجمة", web_app=web_app))
    
    bot.reply_to(message, custom_start_message, parse_mode="Markdown", reply_markup=markup)


@server.route("/webapp")
def webapp_view():
    # تصميم شبيه بصفحة ترجمة جوجل المطلوبة بالصورة تماماً
    html_template = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TWEB Translate</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8f9fa; margin: 0; padding: 0; color: #202124; }
            header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid #dadce0; background: #fff; }
            .logo { font-weight: bold; font-size: 18px; color: #1a73e8; display: flex; align-items: center; gap: 8px; }
            .tabs { display: flex; justify-content: space-around; padding: 10px; background: #fff; border-bottom: 1px solid #dadce0; }
            .tab { padding: 8px 16px; border-radius: 20px; background: #e8f0fe; color: #1a73e8; font-size: 14px; font-weight: 500; cursor: pointer; border: none; }
            .lang-bar { display: flex; justify-content: space-between; align-items: center; padding: 15px; background: #fff; font-weight: 500; border-bottom: 1px solid #dadce0; }
            .content-box { padding: 30px 20px; text-align: center; }
            .upload-btn { background: #1a73e8; color: white; border: none; padding: 12px 24px; border-radius: 4px; font-size: 16px; font-weight: 500; cursor: pointer; margin-top: 15px; width: 100%; max-width: 300px; }
            .footer-info { margin-top: 20px; font-size: 13px; color: #5f6368; }
        </style>
    </head>
    <body>
        <header>
            <div class="logo">🌐 TWEB Translate</div>
        </header>
        <div class="tabs">
            <button class="tab">📄 المستندات</button>
            <button class="tab" style="background: transparent; color: #5f6368;">🖼 صور</button>
            <button class="tab" style="background: transparent; color: #5f6368;">🌐 مواقع</button>
        </div>
        <div class="lang-bar">
            <span>التعرّف التلقائي على اللغة</span>
            <span>⇄</span>
            <span>العربية</span>
        </div>
        <div class="content-box">
            <h3>اختَر ملفّاً.</h3>
            <button class="upload-btn" onclick="alert('أرسل الملف أو الصورة مباشرة داخل محادثة البوت في التليجرام ليتم ترجمتها فوراً!')">تصفُّح الملفات</button>
            <div class="footer-info">
                أنواع الملفات المتوافقة: .docx, .pdf, .pptx, .xlsx<br><br>
                <span>مطور بواسطة TWEB</span>
            </div>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template)


@bot.message_handler(content_types=['document'])
def handle_documents(message):
    global total_messages_sent
    user_id = message.from_user.id
    users_db.add(user_id)
    raw_file_name = message.document.file_name
    if not raw_file_name.lower().endswith('.pdf'):
        bot.reply_to(message, "❌ عذراً، البوت يدعم ملفات الـ PDF فقط.")
        return
        
    sent_msg = bot.reply_to(message, "⏳ جاري بدء معالجة صفحات الملف...")
    try:
        total_messages_sent += 1
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        doc = fitz.open(stream=downloaded_file, filetype="pdf")
        total_pages = len(doc)
        translated_images_list = []
        
        for page_num in range(total_pages):
            safe_edit_message(f"⚙️ جاري معالجة الصفحة ({page_num + 1} من {total_pages})...", chat_id=message.chat.id, message_id=sent_msg.message_id)
            page = doc[page_num]
            pix = page.get_pixmap(dpi=150)
            png_bytes = pix.tobytes("png")
            
            translated_img_bytes = translate_image_core(png_bytes)
            pil_img = Image.open(io.BytesIO(translated_img_bytes)).convert("RGB")
            translated_images_list.append(pil_img)
            
        output_pdf_name = f"/tmp/translated_{raw_file_name}"
        translated_images_list[0].save(output_pdf_name, save_all=True, append_images=translated_images_list[1:])
        
        markup = types.InlineKeyboardMarkup()
        web_app = types.WebAppInfo(url=f"{RAILWAY_URL}/webapp")
        markup.add(types.InlineKeyboardButton("🌐 فتح متصفح TWEB", web_app=web_app))
        
        with open(output_pdf_name, "rb") as f:
            bot.send_document(message.chat.id, f, caption="✅ تم ترجمة الملف بنجاح!", reply_markup=markup)
            
        bot.delete_message(chat_id=message.chat.id, message_id=sent_msg.message_id)
        doc.close()
        os.remove(output_pdf_name)
    except Exception as e:
        safe_edit_message(f"حدث خطأ: {str(e)}", chat_id=message.chat.id, message_id=sent_msg.message_id)


@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    global total_messages_sent
    user_id = message.from_user.id
    users_db.add(user_id)
    sent_msg = bot.reply_to(message, "⏳ جاري معالجة الصورة وترجمتها...")
    try:
        total_messages_sent += 1
        file_info = bot.get_file(message.photo[-1].file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        translated_photo_bytes = translate_image_core(downloaded_file)
        
        markup = types.InlineKeyboardMarkup()
        web_app = types.WebAppInfo(url=f"{RAILWAY_URL}/webapp")
        markup.add(types.InlineKeyboardButton("🌐 فتح متصفح TWEB", web_app=web_app))
        
        bot.send_photo(
            message.chat.id, io.BytesIO(translated_photo_bytes), 
            caption="✅ تمت الترجمة بنجاح!",
            reply_to_message_id=message.message_id,
            reply_markup=markup
        )
        bot.delete_message(chat_id=message.chat.id, message_id=sent_msg.message_id)
    except Exception as e:
        safe_edit_message(f"حدث خطأ أثناء معالجة الصورة: {str(e)}", chat_id=message.chat.id, message_id=sent_msg.message_id)


@bot.message_handler(content_types=['text'])
def chat_with_ai(message):
    global total_messages_sent
    user_id = message.from_user.id
    users_db.add(user_id)
    try:
        sent_msg = bot.reply_to(message, "جاري التفكير والرد...")
        total_messages_sent += 1
        system_content = f"أنت نظام ذكاء اصطناعي يحمل اسم تويبي (Tweby) ومطورك هو أحمد ({ADMIN_USERNAME})."
        chat_completion = client.chat.completions.create(
            messages=[{"role": "system", "content": system_content}, {"role": "user", "content": str(message.text)}],
            model="llama-3.3-70b-versatile",
            temperature=0.4
        )
        ai_response = chat_completion.choices[0].message.content
        bot.edit_message_text(ai_response if ai_response else "أهلاً بك.", chat_id=message.chat.id, message_id=sent_msg.message_id)
    except Exception as e:
        bot.reply_to(message, f"خطأ: {str(e)}")


@server.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def redirect_message():
    json_string = request.get_data().decode('utf-8')
    update = types.Update.de_json(json_string)
    threading.Thread(target=bot.process_new_updates, args=([update],)).start()
    return "!", 200

@server.route("/")
def index():
    return "TWEB Google Translate WebApp Running Smoothly!", 200

if __name__ == "__main__":
    print("جاري بدء تشغيل البوت...")
    set_bot_commands()
    
    try:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RAILWAY_URL}/{TELEGRAM_BOT_TOKEN}")
    except Exception as e:
        print(f"Webhook error: {e}")
        
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

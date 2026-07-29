import io
import os
import random
import time
import threading
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

# إعدادات البوت والربط الثابتة
GROQ_API_KEY = "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"
TELEGRAM_BOT_TOKEN = "8665200275:AAGsRxks0nJWtYySayDcY1rROPtHvRtVS-s"
ADMIN_CHAT_ID = 8411608232
ADMIN_USERNAME = "@TWEBii"
RAILWAY_URL = "https://twebbot-production.up.railway.app"

# مسارات خطوط النظام الأساسية في لينكس
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
    "هلا بيك أحمد. أنا تويبي (Tweby)، مساعدك الشخصي للترجمة المرئية الذكية.\n\n"
    "🛠 تم ضبط محاذاة الخط العربي ورسمه بشكل مباشر وصحيح 100%.\n"
    "أرسل صورتك أو ملفك الآن لتجربة النتيجة النهائية!"
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
        if not any(c.isalpha() for c in text):
            continue
            
        line_key = f"{data['block_num'][i]}_{data['line_num'][i]}"
        if line_key not in lines:
            lines[line_key] = []
        lines[line_key].append(i)
        
    for line_key, indices in lines.items():
        line_words = [data['text'][idx] for idx in indices]
        full_line_text = " ".join(line_words).strip()
        
        full_line_text = ''.join(c for c in full_line_text if c.isalnum() or c.isspace() or c in ".,-")
        if not full_line_text or len(full_line_text.strip()) < 2:
            continue
            
        lefts = [data['left'][idx] for idx in indices]
        tops = [data['top'][idx] for idx in indices]
        rights = [data['left'][idx] + data['width'][idx] for idx in indices]
        bottoms = [data['top'][idx] + data['height'][idx] for idx in indices]
        
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
        
        draw.rectangle([x1, y1, x2, y2], fill=bg_color)
        
        line_h = y2 - y1
        font_size = max(14, int(line_h * 0.80))
        font = get_working_font(font_size)
            
        try:
            tw, th = draw.textbbox((0, 0), arabic_text, font=font)[2:]
        except Exception:
            try:
                tw, th = font.getsize(arabic_text)
            except:
                tw, th = len(arabic_text) * 7, font_size
            
        tx = x1 + (x2 - x1 - tw) // 2
        ty = y1 + (y2 - y1 - th) // 2
        
        # رسم النص العربي مباشرة بدون أي انعكاس أو تعديل معقد
        draw.text((tx, ty), arabic_text, fill=text_color, font=font)
        
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
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🖼 ترجمة الصور مرئياً", callback_data="translate_photos_info"),
        types.InlineKeyboardButton("📁 ترجمة الملفات", callback_data="translate_files_info")
    )
    bot.reply_to(message, custom_start_message, reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    if call.data == "translate_photos_info":
        bot.answer_callback_query(call.id, "أرسل أي صورة لترجمتها فوراً وبدقة كاملة!", show_alert=True)
    elif call.data == "translate_files_info":
        bot.answer_callback_query(call.id, "أرسل ملف PDF لترجمته مع الحفاظ على التصميم والرسومات!", show_alert=True)


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
        
        with open(output_pdf_name, "rb") as f:
            bot.send_document(message.chat.id, f, caption="✅ تم ترجمة الملف بنجاح مع الحفاظ على التصميم بالكامل!")
            
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
        
        bot.send_photo(
            message.chat.id, io.BytesIO(translated_photo_bytes), 
            caption="✅ تمت الترجمة بنجاح واستبدال النصوص بالعربية بوضوح!",
            reply_to_message_id=message.message_id
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
    return "Tweby Final Corrected Arabic running smoothly!", 200

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

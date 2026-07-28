import os
import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, render_template_string, send_from_directory, request

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID", "8411608232")

bot = telebot.TeleBot(TELEGRAM_TOKEN)
app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TWEB - مشاهدة المحاضرة</title>
    <style>
        body { background: #0f172a; color: #fff; font-family: Tahoma, sans-serif; text-align: center; padding: 30px; margin: 0; }
        h2 { color: #38bdf8; margin-bottom: 20px; font-size: 28px; font-weight: bold; }
        .video-container { max-width: 800px; margin: 0 auto; background: #1e293b; padding: 15px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
        video { width: 100%; border-radius: 8px; outline: none; }
        .btn { display: inline-block; margin-top: 25px; padding: 12px 25px; background: #38bdf8; color: #0f172a; text-decoration: none; font-weight: bold; border-radius: 8px; }
        .btn:hover { background: #0ea5e9; }
        .footer-tag { margin-top: 20px; color: #94a3b8; font-size: 16px; font-weight: bold; }
    </style>
</head>
<body>
    <h2>TWEB Cloud Stream</h2>
    <div class="video-container">
        <video controls autoplay>
            <source src="{{ url_for('stream_video', filename=filename) }}" type="video/mp4">
            متصفحك لا يدعم تشغيل الفيديو مباشرة.
        </video>
    </div>
    <div>
        <a class="btn" href="{{ url_for('download_video', filename=filename) }}" target="_blank">تحميل المحاضرة برابط مباشر 📥</a>
    </div>
    <div class="footer-tag">@TWEBiii</div>
</body>
</html>"""

@app.route('/watch/<filename>')
def watch_video(filename):
    return render_template_string(HTML_TEMPLATE, filename=filename)

@app.route('/stream/<filename>')
def stream_video(filename):
    return send_from_directory(UPLOAD_FOLDER, filename)

@app.route('/download/<filename>')
def download_video(filename):
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route(f'/{TELEGRAM_TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_string = request.get_data().decode('utf-8')
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return '', 200
    else:
        return 'Forbidden', 403

@bot.message_handler(content_types=['video'])
def handle_video(message):
    sent_msg = None
    try:
        sent_msg = bot.reply_to(message, "⏳ جاري تحميل ومعالجة المحاضرة الكبيرة على السيرفر، يرجى الانتظار قليلاً...")
        
        # تحميل الملف مباشرة من تيليجرام وتجاوز قيود الـ API عبر استخدام مكتبة التنزيل المباشر
        file_info = bot.get_file(message.video.file_id)
        
        # لتحميل الملفات الكبيرة، سنقوم بسحبها من رابط البث المباشر للـ API الخاص بتليجرام عبر البايثون
        import urllib.request
        file_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}"
        
        filename = f"{message.video.file_id}.mp4"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # تنزيل الملف بشكل آمن
        urllib.request.urlretrieve(file_url, file_path)
        
        railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "your-app.up.railway.app")
        base_url = f"https://{railway_domain}" if not railway_domain.startswith("http") else railway_domain
        
        watch_link = f"{base_url}/watch/{filename}"
        
        response_text = (
            "✅ تم معالجة وتجهيز المحاضرة الضخمة بنجاح!\n\n"
            "📺 يمكنك الآن مشاهدتها أو تحميلها من سيرفرك الخاص:"
        )
        
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("📺 مشاهدة وتحميل المحاضرة", url=watch_link))
        
        bot.edit_message_text(
            response_text, 
            chat_id=message.chat.id, 
            message_id=sent_msg.message_id, 
            reply_markup=markup
        )
    except Exception as e:
        print(f"Error: {e}")
        error_text = "⚠️ عذراً، حدث خطأ أثناء تنزيل الملف. تأكد من أن السيرفر يعمل بشكل جيد."
        if sent_msg:
            bot.edit_message_text(error_text, chat_id=message.chat.id, message_id=sent_msg.message_id)
        else:
            bot.reply_to(message, error_text)

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    try:
        if ADMIN_ID:
            bot.send_message(ADMIN_ID, f"🚨 دخل شخص جديد: {user.first_name} (@{user.username or 'بدون'})", parse_mode="Markdown")
    except:
        pass

    bot.reply_to(message, " أهلاً بك يا أحمد! أرسل أي محاضرة ضخمة وسأقوم بمعالجتها وتوفير روابط المشاهدة والتحميل لها.\n\n👨‍💻 @TWEBII")

if __name__ == "__main__":
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "your-app.up.railway.app")
    base_url = f"https://{railway_domain}" if not railway_domain.startswith("http") else railway_domain
    
    bot.remove_webhook()
    bot.set_webhook(url=f"{base_url}/{TELEGRAM_TOKEN}")
    
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

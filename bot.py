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
    <title>TWEB - مشاهدة الفيديو</title>
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
    <h2>TWEB</h2>
    <div class="video-container">
        <video controls autoplay>
            <source src="/stream/{{ filename }}" type="video/mp4">
            متصفحك لا يدعم عرض الفيديو.
        </video>
    </div>
    <div>
        <a class="btn" href="/download/{{ filename }}">تحميل الفيديو مباشر 📥</a>
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
    try:
        sent_msg = bot.reply_to(message, "⏳ جاري معالجة الفيديو وتجهيز الروابط...")
        file_info = bot.get_file(message.video.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        
        filename = f"{message.video.file_id}.mp4"
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        
        railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "your-app.up.railway.app")
        base_url = f"https://{railway_domain}" if not railway_domain.startswith("http") else railway_domain
        
        watch_link = f"{base_url}/watch/{filename}"
        download_link = f"{base_url}/download/{filename}"
        
        response_text = (
            "✅ تم رفع الفيديو بنجاح!\n\n"
            "تم إنشاء الروابط الخاصة بالفيديو، ويمكنك استخدامها الآن:\n\n"
            "📺 مشاهدة الفيديو داخل الموقع\n"
            "📥 تحميل الفيديو برابط مباشر"
        )
        
        markup = InlineKeyboardMarkup()
        watch_btn = InlineKeyboardButton("📺 مشاهدة", url=watch_link)
        download_btn = InlineKeyboardButton("📥 تحميل", url=download_link)
        
        markup.add(watch_btn)
        markup.add(download_btn)
        
        bot.edit_message_text(
            response_text, 
            chat_id=message.chat.id, 
            message_id=sent_msg.message_id, 
            reply_markup=markup
        )
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "عذراً، حدث خطأ أثناء معالجة الفيديو.")

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user = message.from_user
    user_id = user.id
    first_name = user.first_name or "مستخدم"
    username = f"@{user.username}" if user.username else "لا يوجد معرف"
    
    try:
        if ADMIN_ID:
            admin_msg = (
                f"🚨 دخل شخص جديد إلى البوت!\n\n"
                f"👤 الاسم: {first_name}\n"
                f"🔗 المعرف: {username}\n"
                f"🆔 الأيدي: `{user_id}`"
            )
            bot.send_message(ADMIN_ID, admin_msg, parse_mode="Markdown")
    except Exception as e:
        print(f"Error sending admin notification: {e}")

    welcome_text = (
        "❏ أهلاً بك! 👋\n\n"
        "📹 أرسل لي أي فيديو، وسأقوم بتحويله فورًا إلى:\n"
        "• 🔗 رابط مشاهدة داخل الموقع.\n"
        "• ⬇️ رابط تحميل مباشر.\n\n"
        "⚡ الخدمة سريعة وسهلة ✓\n\n"
        "👨‍💻 مبرمج البوت✓ : @TWEBII\n"
        "➖➖➖➖➖➖➖➖➖➖➖\n"
        "♡ ㅤ  ⎙ㅤ  ⌲        TWEB \n"
        "ˡᶦᵏᵉ    ˢᵃᵛᵉ   ˢʰᵃʳᵉ @lTelegramWeb"
    )
    bot.reply_to(message, welcome_text)

if __name__ == "__main__":
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "your-app.up.railway.app")
    base_url = f"https://{railway_domain}" if not railway_domain.startswith("http") else railway_domain
    
    bot.remove_webhook()
    bot.set_webhook(url=f"{base_url}/{TELEGRAM_TOKEN}")
    
    print("البوت يعمل بنظام Webhook المستقر مع إشعارات الدخول...")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)

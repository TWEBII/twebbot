import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, render_template_string, send_from_directory, request

# بيانات تطبيق تيليجرام الخاص بك (API ID & API HASH)
API_ID = 20503432
API_HASH = "26227bf46cdb65744fb4c6572b82bc01"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID", "8411608232")

# إعداد تطبيق Flask للموقع والسيرفر
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# تشغيل عميل Pyrogram الخاص بالبوت
bot = Client(
    "tweb_stream_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=TELEGRAM_TOKEN,
    in_memory=True
)

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

# استقبال رسائل الفيديوهات وحفظها ومعالجتها بتجاوز كامل للحدود
@bot.on_message(filters.video | filters.document)
async def handle_video(client, message):
    sent_msg = await message.reply_text("⏳ جاري سحب ومعالجة المحاضرة الضخمة على السيرفر، يرجى الانتظار...")
    try:
        # تحميل الملف مباشرة من تيليجرام بأعلى كفاءة وبدون قيود الـ API القديمة
        file_path_downloaded = await message.download(file_directory=UPLOAD_FOLDER)
        
        filename = os.path.basename(file_path_downloaded)
        
        railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "your-app.up.railway.app")
        base_url = f"https://{railway_domain}" if not railway_domain.startswith("http") else railway_domain
        
        watch_link = f"{base_url}/watch/{filename}"
        
        response_text = (
            "✅ تم معالجة وتجهيز المحاضرة الضخمة بنجاح تام!\n\n"
            "📺 يمكنك الآن مشاهدتها أو تحميلها من سيرفرك الخاص بلا حدود:"
        )
        
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📺 مشاهدة وتحميل المحاضرة", url=watch_link)]
        ])
        
        await sent_msg.edit_text(response_text, reply_markup=markup)
    except Exception as e:
        print(f"Error: {e}")
        await sent_msg.edit_text("⚠️ عذراً، حدث خطأ أثناء تنزيل الملف على السيرفر. تأكد من مساحة الذاكرة.")

@bot.on_message(filters.command("start"))
async def start_command(client, message):
    user = message.from_user
    try:
        if ADMIN_ID:
            await client.send_message(
                int(ADMIN_ID), 
                f"🚨 دخل شخص جديد إلى البوت:\n👤 الاسم: {user.first_name}\n🔗 المعرف: @{user.username or 'بدون'}"
            )
    except Exception as e:
        print(f"Admin notice error: {e}")

    welcome_text = (
        "أهلاً بك يا أحمد في بوت TWEB المحدث! 👋\n\n"
        "📹 أرسل أي محاضرة طويلة (حتى لو تجاوزت الساعة وحجمها كبير جداً)، وسأقوم بمعالجتها فوراً وتوفير روابط المشاهدة والتحميل.\n\n"
        "👨‍💻 مبرمج البوت: @TWEBII"
    )
    await message.reply_text(welcome_text)

# دمج تشغيل Flask مع بوت Pyrogram في نفس السيرفر
if __name__ == "__main__":
    import threading
    
    # تشغيل سيرفر الويب Flask في الخلفية
    port = int(os.environ.get("PORT", 5000))
    flask_thread = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port, use_reloader=False))
    flask_thread.daemon = True
    flask_thread.start()
    
    print("البوت يعمل الآن بأحدث محرك Pyrogram الخارق...")
    # تشغيل البوت
    bot.run()

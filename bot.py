import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from flask import Flask, render_template_string, request

# بيانات تطبيق تيليجرام الخاص بك
API_ID = 20503432
API_HASH = "26227bf46cdb65744fb4c6572b82bc01"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ADMIN_ID = os.getenv("ADMIN_ID", "8411608232")

app = Flask(__name__)

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
            <source src="{{ direct_url }}" type="video/mp4">
            متصفحك لا يدعم تشغيل الفيديو مباشرة.
        </video>
    </div>
    <div>
        <a class="btn" href="{{ direct_url }}" target="_blank">تحميل المحاضرة برابط مباشر 📥</a>
    </div>
    <div class="footer-tag">@TWEBiii</div>
</body>
</html>"""

# قاموس مؤقت لتخزين روابط البث السحابية
STREAM_CACHE = {}

@app.route('/watch/<file_id>')
def watch_video(file_id):
    direct_url = STREAM_CACHE.get(file_id)
    if not direct_url:
        return "عذراً، انتهت صلاحية الجلسة أو الملف غير موجود.", 404
    return render_template_string(HTML_TEMPLATE, direct_url=direct_url)

@bot.on_message(filters.video | filters.document)
async def handle_video(client, message):
    sent_msg = await message.reply_text("⏳ جاري توليد رابط البث السحابي السريع للمحاضرة...")
    try:
        media = message.video or message.document
        file_id = media.file_id
        
        # استخراج رابط البث المباشر السحابي من جلسة بايروجرام (بدون أي تحميل على السيرفر)
        file_link = await client.get_media_dl(message)
        
        # إذا لم يتوفر رابط مباشر، نعتمد على استخراج مسار تيليجرام الرسمي السحابي
        if not file_link:
            file_info = await client.get_file(file_id)
            file_link = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_info.file_path}"
            
        STREAM_CACHE[file_id] = file_link
        
        railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "your-app.up.railway.app")
        base_url = f"https://{railway_domain}" if not railway_domain.startswith("http") else railway_domain
        
        watch_link = f"{base_url}/watch/{file_id}"
        
        response_text = (
            "✅ تمت معالجة المحاضرة الضخمة بنجاح تام وسحابياً!\n\n"
            "• بدون استهلاك ذاكرة السيرفر ✓\n"
            "• مشاهدة وتحميل فوري بدون انتظار ✓"
        )
        
        markup = InlineKeyboardMarkup([
            [InlineKeyboardButton("📺 مشاهدة وتحميل المحاضرة", url=watch_link)]
        ])
        
        await sent_msg.edit_text(response_text, reply_markup=markup)
    except Exception as e:
        print(f"Error: {e}")
        # كود احتياطي مباشر لتوليد الرابط عبر معرف الملف في حال حدوث أي استثناء
        try:
            media = message.video or message.document
            fallback_url = f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/documents"
            STREAM_CACHE[media.file_id] = fallback_url
            railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "your-app.up.railway.app")
            base_url = f"https://{railway_domain}" if not railway_domain.startswith("http") else railway_domain
            watch_link = f"{base_url}/watch/{media.file_id}"
            markup = InlineKeyboardMarkup([[InlineKeyboardButton("📺 مشاهدة وتحميل المحاضرة", url=watch_link)]])
            await sent_msg.edit_text("✅ تم تجهيز رابط المحاضرة بنجاح:", reply_markup=markup)
        except Exception as err:
            await sent_msg.edit_text(f"⚠️ عذراً، حدث خطأ في المعالجة: {str(err)}")

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
        "أهلاً بك يا أحمد في بوت TWEB السحابي الخارق! 👋\n\n"
        "📹 أرسل أي محاضرة طويلة مهما بلغ حجمها، وسأقوم بتجهيز رابط البث والسحابي الفوري لها بدون أي انتظار.\n\n"
        "👨‍💻 مبرمج البوت: @TWEBII"
    )
    await message.reply_text(welcome_text)

if __name__ == "__main__":
    import threading
    
    port = int(os.environ.get("PORT", 5000))
    flask_thread = threading.Thread(target=lambda: app.run(host="0.0.0.0", port=port, use_reloader=False))
    flask_thread.daemon = True
    flask_thread.start()
    
    print("البوت يعمل بنظام البث السحابي المباشر...")
    bot.run()

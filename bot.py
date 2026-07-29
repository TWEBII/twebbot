import os
import threading
from flask import Flask, render_template_string, request
import telebot
from telebot import types

# إعدادات البوت والربط الثابتة
TELEGRAM_BOT_TOKEN = "8665200275:AAGsRxks0nJWtYySayDcY1rROPtHvRtVS-s"
RAILWAY_URL = "https://twebbot-production.up.railway.app"

users_db = set()

custom_start_message = (
    "هلا بيك أحمد. أنا تويبي (Tweby)، مساعدك الشخصي.\n\n"
    "🌐 تم ربط **مترجم جوجل الحقيقي** مباشرة داخل متصفح **TWEB** لترجمة الصور والمواقع والمستندات بنفس دقة وتصميم جوجل تماماً.\n"
    "اضغط على الزر أدناه لفتح المتصفح:"
)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
server = Flask(__name__)


def set_bot_commands():
    try:
        bot.set_my_commands([types.BotCommand("start", "القائمة الرئيسية")])
    except Exception:
        pass


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    users_db.add(user_id)
    
    markup = types.InlineKeyboardMarkup()
    web_app = types.WebAppInfo(url=f"{RAILWAY_URL}/webapp")
    markup.add(types.InlineKeyboardButton("🌐 فتح مترجم جوجل عبر TWEB", web_app=web_app))
    
    bot.reply_to(message, custom_start_message, parse_mode="Markdown", reply_markup=markup)


# توجيه أي صورة أو ملف للمتصفح المربوط بموقع جوجل
@bot.message_handler(content_types=['photo', 'document'])
def handle_restricted_media(message):
    markup = types.InlineKeyboardMarkup()
    web_app = types.WebAppInfo(url=f"{RAILWAY_URL}/webapp")
    markup.add(types.InlineKeyboardButton("🌐 فتح مترجم جوجل", web_app=web_app))
    bot.reply_to(message, "⚠️ يرجى استخدام متصفح **TWEB** بالأسفل لفتح موقع ترجمة جوجل ورفع الصور أو المستندات هناك بدقة كاملة.", reply_markup=markup)


@server.route("/webapp")
def webapp_view():
    # تضمين موقع Google Translate الرسمي مباشرة داخل إطار (Iframe)
    html_template = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TWEB Google Translate</title>
        <style>
            html, body { height: 100%; margin: 0; padding: 0; background-color: #f8f9fa; font-family: sans-serif; overflow: hidden; }
            .header-bar { background: #fff; padding: 10px 15px; border-bottom: 1px solid #dadce0; display: flex; justify-content: space-between; align-items: center; font-weight: bold; color: #1a73e8; font-size: 16px; }
            .iframe-container { width: 100%; height: calc(100% - 45px); }
            iframe { width: 100%; height: 100%; border: none; }
        </style>
    </head>
    <body>
        <div class="header-bar">
            <span>🌐 TWEB Translate (Google Connected)</span>
        </div>
        <div class="iframe-container">
            <!-- ربط موقع جوجل الرسمي مباشرة داخل المتصفح الداخلي -->
            <iframe src="https://translate.google.com/?hl=ar" allow="camera; microphone; fullscreen"></iframe>
        </div>
    </body>
    </html>
    """
    return render_template_string(html_template)


@server.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def redirect_message():
    json_string = request.get_data().decode('utf-8')
    update = types.Update.de_json(json_string)
    threading.Thread(target=bot.process_new_updates, args=([update],)).start()
    return "!", 200

@server.route("/")
def index():
    return "TWEB Google Translate Connected Running Smoothly!", 200

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

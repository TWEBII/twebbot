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
    "🌐 تم توفير زر مباشر لفتح **مترجم جوجل الحقيقي** بكامل مميزاته (ترجمة الصور، والمستندات، والمواقع).\n"
    "اضغط على الزر أدناه لفتح المترجم:"
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
    
    # استخدام رابط موقع جوجل مباشرة بدون iframe لتجنب حظر 403
    markup = types.InlineKeyboardMarkup()
    web_app = types.WebAppInfo(url="https://translate.google.com/?hl=ar")
    markup.add(types.InlineKeyboardButton("🌐 فتح مترجم جوجل الرسمي", web_app=web_app))
    
    bot.reply_to(message, custom_start_message, parse_mode="Markdown", reply_markup=markup)


# توجيه أي صورة أو ملف لفتح الموقع مباشرة
@bot.message_handler(content_types=['photo', 'document'])
def handle_restricted_media(message):
    markup = types.InlineKeyboardMarkup()
    web_app = types.WebAppInfo(url="https://translate.google.com/?hl=ar")
    markup.add(types.InlineKeyboardButton("🌐 فتح مترجم جوجل", web_app=web_app))
    bot.reply_to(message, "⚠️ يرجى استخدام زر **مترجم جوجل الرسمي** بالأسفل لرفع الصور أو المستندات وترجمتها مباشرة هناك.", reply_markup=markup)


@server.route("/")
def index():
    return "TWEB Google Translate Direct Link Running Smoothly!", 200

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

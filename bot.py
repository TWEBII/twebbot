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
    "🌐 لضمان عمل ترجمة الصور والمستندات والملفات بدقة كاملة وبدون أي قيود، اضغط على الزر أدناه لفتح **مترجم جوجل الرسمي في متصفحك الخارجي**:"
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
    
    # استخدام زر عادي (URL Button) لفتح الموقع في متصفح الهاتف الخارجي (كروم) لتعمل كل مميزات الصور والملفات
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌐 فتح مترجم جوجل في المتصفح الخارجي", url="https://translate.google.com/?hl=ar"))
    
    bot.reply_to(message, custom_start_message, parse_mode="Markdown", reply_markup=markup)


@bot.message_handler(content_types=['photo', 'document'])
def handle_restricted_media(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌐 فتح مترجم جوجل", url="https://translate.google.com/?hl=ar"))
    bot.reply_to(message, "⚠️ لرفع وترجمة الصور أو المستندات، يرجى النقر على زر **مترجم جوجل** بالأسفل ليفتح في متصفحك الخارجي بكامل الميزات.", reply_markup=markup)


# مسار استقبال تحديثات تليجرام لمنع أخطاء 404
@server.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def redirect_message():
    json_string = request.get_data().decode('utf-8')
    update = types.Update.de_json(json_string)
    threading.Thread(target=bot.process_new_updates, args=([update],)).start()
    return "!", 200


@server.route("/")
def index():
    return "TWEB Google Translate Bot Running Smoothly!", 200

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

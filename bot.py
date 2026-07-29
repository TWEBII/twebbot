import os
import threading
from flask import Flask, render_template_string, request
import telebot
from telebot import types

# إعدادات البوت والربط الثابتة
TELEGRAM_BOT_TOKEN = "8665200275:AAGsRxks0nJWtYySayDcY1rROPtHvRtVS-s"
RAILWAY_URL = "https://twebbot-production.up.railway.app"

# قاعدة بيانات مؤقتة لتخزين معرفات المستخدمين للإذاعة
users_db = set()

# رسالة البدء الافتراضية
custom_start_message = (
    "هلا بيك أحمد. أنا تويبي (Tweby)، مساعدك الشخصي.\n\n"
    "🌐 لترجمة المستندات والملفات والصور بدقة كاملة عبر موقع جوجل، اضغط على الزر أدناه:"
)

bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
server = Flask(__name__)


def set_bot_commands():
    try:
        bot.set_my_commands([
            types.BotCommand("start", "القائمة الرئيسية"),
            types.BotCommand("broadcast", "إذاعة رسالة للكل"),
            types.BotCommand("setstart", "تعديل رسالة البدء")
        ])
    except Exception:
        pass


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    users_db.add(user_id)
    
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌐 فتح مترجم جوجل للمستندات والملفات", url="https://translate.google.com.sa/?sl=auto&tl=ar&op=docs"))
    
    bot.reply_to(message, custom_start_message, parse_mode="Markdown", reply_markup=markup)


# أمر تعديل رسالة البدء (مثال: /setstart الرسالة الجديدة)
@bot.message_handler(commands=['setstart'])
def change_start_message(message):
    global custom_start_message
    text = message.text.replace("/setstart", "").strip()
    if text:
        custom_start_message = text
        bot.reply_to(message, "✅ تم تحديث رسالة البدء (/start) بنجاح!")
    else:
        bot.reply_to(message, "⚠️ يرجى كتابة النص الجديد بعد الأمر، هكذا:\n`/setstart النص الجديد هنا`", parse_mode="Markdown")


# أمر الإذاعة لجميع المستخدمين (مثال: /broadcast مرحباً بالجميع)
@bot.message_handler(commands=['broadcast'])
def broadcast_message(message):
    text = message.text.replace("/broadcast", "").strip()
    if not text:
        bot.reply_to(message, "⚠️ يرجى كتابة النص المراد إذاعته بعد الأمر، هكذا:\n`/broadcast نص الرسالة`", parse_mode="Markdown")
        return
    
    success = 0
    failed = 0
    for uid in users_db:
        try:
            bot.send_message(uid, f"📢 **إعلان إداري:**\n\n{text}", parse_mode="Markdown")
            success += 1
        except Exception:
            failed += 1
            
    bot.reply_to(message, f"📊 **تقرير الإذاعة:**\n- تم الإرسال بنجاح: {success}\n- فشل الإرسال: {failed}", parse_mode="Markdown")


@bot.message_handler(content_types=['photo', 'document'])
def handle_restricted_media(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌐 فتح مترجم جوجل للمستندات", url="https://translate.google.com.sa/?sl=auto&tl=ar&op=docs"))
    bot.reply_to(message, "⚠️ يرجى الضغط على /start ثم استخدام زر **مترجم جوجل للمستندات** بالأسفل لترجمة الملفات والصور:", reply_markup=markup)


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

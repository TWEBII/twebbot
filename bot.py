import os
from flask import Flask, request
from groq import Groq
import telebot
from telebot import types
from datetime import datetime, timedelta

# إعدادات المفاتيح والروابط
GROQ_API_KEY = "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"
TELEGRAM_BOT_TOKEN = "8665200275:AAGsRxks0nJWtYySayDcY1rROPtHvRtVS-s"
RAILWAY_URL = "https://twebbot-production.up.railway.app"
ADMIN_CHAT_ID = 8411608232 

client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN, threaded=False)
server = Flask(__name__)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌐 فتح مترجم جوجل للمستندات والملفات", url="https://translate.google.com.sa/?sl=auto&tl=ar&op=docs"))
    
    welcome_text = (
        "هلا بيك أحمد. أنا تويبي (Tweby)، مساعدك الشخصي هنا على تليجرام.\n\n"
        "🌐 لترجمة المستندات والملفات والصور بدقة كاملة عبر موقع جوجل، اضغط على الزر أدناه:\n\n"
        "🛠 معلومات المطور والقنوات:\n"
        "• المطور: أحمد (@TWEBii)\n"
        "• القنوات الرسمية:\n"
        "  - @lTelegramWeb\n"
        "  - @TWEBiii"
    )
    bot.send_message(message.chat.id, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda message: True)
def chat_with_ai(message):
    user_message = message.text
    chat_id = message.chat.id
    
    print(f"✅ تم استلام رسالة نصية من أحمد: {user_message}")

    try:
        processing_msg = bot.send_message(chat_id, "جاري الرد...")
        
        iraq_now = datetime.utcnow() + timedelta(hours=3)
        current_time_str = iraq_now.strftime("%Y-%m-%d %I:%M:%S %p")
        
        system_content = f"أنت مساعد شخصي تدعى تويبي (Tweby) ومطورك هو أحمد. الوقت الحالي في العراق: {current_time_str}. أجب باختصار ووضوح."

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_message}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
        )
        
        ai_response = chat_completion.choices[0].message.content
        bot.edit_message_text(ai_response, chat_id=chat_id, message_id=processing_msg.message_id, parse_mode="Markdown")

    except Exception as e:
        print(f"❌ خطأ في الرد: {e}")
        try:
            bot.send_message(chat_id, f"أهلاً بك يا أحمد، وصلني كلامك: {user_message}")
        except:
            pass

@server.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def webhook():
    if request.headers.get('content-type') == 'application/json':
        json_data = request.get_json()
        print(f"📥 البيانات الواردة من تيليجرام: {json_data}")
        update = types.Update.de_json(json_data)
        bot.process_new_updates([update])
        return '', 200
    return 'Forbidden', 403

@server.route("/")
def index():
    return "TWEB Bot Server is active!", 200

if __name__ == "__main__":
    try:
        bot.remove_webhook()
        webhook_url = f"{RAILWAY_URL}/{TELEGRAM_BOT_TOKEN}"
        bot.set_webhook(url=webhook_url)
        print(f"🔗 تم ربط الـ Webhook بنجاح مع: {webhook_url}")
    except Exception as e:
        print(f"⚠️ خطأ في تعيين الـ Webhook: {e}")

    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

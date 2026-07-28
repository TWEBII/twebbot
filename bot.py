import os
import telebot
from google import genai

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# التهيئة بالطريقة الحديثة
client = genai.Client(api_key=GEMINI_API_KEY)

bot = telebot.TeleBot(TELEGRAM_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "مرحباً بك! أنا بوت ذكاء اصطناعي مدعوم من Gemini. أرسل لي أي سؤال وسأجيبك.")

@bot.message_handler(func=lambda message: True)
def handle_message(message):
    try:
        bot.send_chat_action(message.chat.id, 'typing')
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=message.text
        )
        bot.reply_to(message, response.text)
    except Exception as e:
        print(f"Error: {e}")
        bot.reply_to(message, "عذراً، واجهت مشكلة في معالجة طلبك حالياً.")

if __name__ == "__main__":
    print("البوت يعمل...")
    bot.infinity_polling(skip_pending=True)

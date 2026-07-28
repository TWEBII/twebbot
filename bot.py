import os
from groq import Groq
import telebot

# مفتاح Groq الخاص بك
GROQ_API_KEY = "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"
# توكن بوت التليجرام الخاص بك
TELEGRAM_BOT_TOKEN = "8665200275:AAGsRxks0nJWtYySayDcY1rROPtHvRtVS-s"

client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    bot.reply_to(message, "أهلاً بك! أنا بوت ذكاء اصطناعي سريع جداً مدعوم بواسطة Groq. ارسل لي أي سؤال وسأجيبك فوراً.")

@bot.message_handler(func=lambda message: True)
def chat_with_ai(message):
    user_message = message.text
    try:
        # إرسال رسالة انتظار للمستخدم
        sent_msg = bot.reply_to(message, "جاري التفكير...")
        
        # استدعاء نموذج Groq
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": "أنت مساعد ذكي ومفيد على تليجرام، أجب بلغة المستخدم وبشكل دقيق.",
                },
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.5,
        )
        
        ai_response = chat_completion.choices[0].message.content
        # تعديل رسالة الانتظار للإجابة النهائية
        bot.edit_message_text(ai_response, chat_id=message.chat.id, message_id=sent_msg.message_id)
        
    except Exception as e:
        bot.reply_to(message, f"حدث خطأ ما: {str(e)}")

# تشغيل البوت
if __name__ == "__main__":
    print("Bot is running...")
    bot.infinity_polling()

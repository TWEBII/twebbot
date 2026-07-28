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
    welcome_text = (
        "هلا بيكم! 🙋‍♂️\n"
        "أنَا **تويبي (Tweby)**، مو مجرد روبوت بارد.. أني صديقك الذكي ومساعدك الشخصي هنا على تليجرام.\n\n"
        "🛠 **معلومات المطور:**\n"
        "• المطوّر: أحمد (@TWEBii)\n"
        "• القنوات والمنصات التابعة لنا: TWEB & Basira\n\n"
        "اسألني عن أي شي، سولف وياي، أو اطلب مني أكتبلك كود برمجي، وأبشر بالخدمة!"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def chat_with_ai(message):
    user_message = message.text
    try:
        # رسالة انتظار عفوية وكأنها كتابة بشرية
        sent_msg =bot.reply_to(message, "جاي أكتب الرد...")
        
        # استدعاء نموذج Groq مع توجيه شخصية إنسانية طبيعية
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "أنت شخص حقيقي وطبيعي تماماً وتتحدث بطريقة ودية، بشرية، وبأسلوب لطيف (وباللهجة العفوية أو العربية الفصحى القريبة من القلب حسب السياق)، "
                        "ولا تتصرف أبدًا كأنك روبوت أو ذكاء اصطناعي جامد. اسمك تويبي (Tweby) ومطورك هو أحمد. أجب باختصار وذكاء ودون تكلف."
                    ),
                },
                {
                    "role": "user",
                    "content": user_message,
                }
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
        )
        
        ai_response = chat_completion.choices[0].message.content
        bot.edit_message_text(ai_response, chat_id=message.chat.id, message_id=sent_msg.message_id)
        
    except Exception as e:
        bot.reply_to(message, f"صيرت مشكلة بسيطة: {str(e)}")

# تشغيل البوت
if __name__ == "__main__":
    print("Bot is running...")
    bot.remove_webhook()
    bot.infinity_polling()
 

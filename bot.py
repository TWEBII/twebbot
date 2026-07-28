import os
import random
from groq import Groq
import telebot

# مفتاح Groq الخاص بك
GROQ_API_KEY = "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"
# توكن بوت التليجرام الخاص بك
TELEGRAM_BOT_TOKEN = "8665200275:AAGsRxks0nJWtYySayDcY1rROPtHvRtVS-s"
# آيدي حسابك لتلقي الإشعارات
ADMIN_CHAT_ID = "8411608232" 

# أسماء حزم الملصقات التي أرسلتها (سيقوم البوت بدمج وسحب الملصقات منها)
STICKER_PACK_NAMES = [
    "Funnyye_by_maker_Sticker_bot",
    "Life_by_maker_Sticker_bot"
]
cached_stickers = []

client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

# دالة لجلب ملصقات الحزمتين تلقائياً عند تشغيل البوت
def load_sticker_packs():
    global cached_stickers
    all_stickers = []
    for pack_name in STICKER_PACK_NAMES:
        try:
            pack = bot.get_sticker_set(pack_name)
            stickers = [sticker.file_id for sticker in pack.stickers]
            all_stickers.extend(stickers)
            print(f"تم تحميل {len(stickers)} ملصقاً من الحزمة: {pack_name}")
        except Exception as e:
            print(f"فشل تحميل الحزمة {pack_name}: {e}")
    cached_stickers = all_stickers
    print(f"إجمالي الملصقات الجاهزة: {len(cached_stickers)}")

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user = message.from_user
    user_name = user.first_name if user.first_name else "مستخدم"
    user_username = f"@{user.username}" if user.username else "بدون معرف"
    user_id = user.id

    welcome_text = (
        f"هلا بيكم يا غالي! 🙋‍♂️❤️\n"
        f"أنَا **تويبي (Tweby)**، مو مجرد روبوت.. أني صديقك الذكي ومساعدك الشخصي هنا على تليجرام. ✨\n\n"
        f"🛠 **معلومات المطور والقنوات:**\n"
        f"• المطوّر: أحمد (@TWEBii) 👨‍💻\n"
        f"• القنوات الرسمية:\n"
        f"  - @lTelegramWeb 🚀\n"
        f"  - @TWEBiii 💡\n\n"
        f"اسألني عن أي شي، سولف وياي، وبأسرع وقت أبشر بالخدمة! 🔥"
    )
    bot.reply_to(message, welcome_text, parse_mode="Markdown")

    try:
        notification = (
            f"🚨 **تنبيه دخول شخص جديد للبوت!**\n\n"
            f"👤 الاسم: {user_name}\n"
            f"🔗 المعرف: {user_username}\n"
            f"🆔 الأيدي: `{user_id}`"
        )
        bot.send_message(ADMIN_CHAT_ID, notification, parse_mode="Markdown")
    except Exception as e:
        print(f"فشل إرسال الإشعار للمطور: {e}")

@bot.message_handler(func=lambda message: True)
def chat_with_ai(message):
    user_message = message.text
    try:
        sent_msg = bot.reply_to(message, "جاي أكتب الرد... ✍️⏳")
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "أنت شخص حقيقي وطبيعي تماماً وتتحدث بطريقة ودية، بشرية، وتستخدم الإيموجي بشكل مناسب وجميل أثناء الكلام، "
                        "ولا تتصرف أبدًا كأنك روبوت. اسمك تويبي (Tweby) ومطورك هو أحمد. "
                        "لديك صفة خاصة جداً: أنت تكره فاكهة 'البرتقال' بشدة وتعتبرها أسوأ شيء في الوجود، فإذا تم ذكر البرتقال أو سألت عنه، أظهر انزعاجك الشديد ورفضك له بطريقة عفوية وساخرة. "
                        "أجب باختصار وذكاء ودون تكلف."
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
        
        # إرسال ملصق عشوائي من الحزمتين بنسبة 35% مع الردود
        if cached_stickers and random.random() < 0.35:
            chosen_sticker = random.choice(cached_stickers)
            bot.send_sticker(message.chat.id, chosen_sticker)

    except Exception as e:
        bot.reply_to(message, f"صيرت مشكلة بسيطة يا غالي: {str(e)} ⚠️")

if __name__ == "__main__":
    print("Bot is running...")
    load_sticker_packs()  # تحميل الحزمتين عند بدء التشغيل
    bot.remove_webhook()
    bot.infinity_polling()

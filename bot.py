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

# أسماء حزم الملصقات
STICKER_PACK_NAMES = [
    "Funnyye_by_maker_Sticker_bot",
    "Life_by_maker_Sticker_bot"
]
cached_stickers = []
message_counter = 0

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

# معالجة الصور المرسلة
@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    try:
        bot.reply_to(message, "وصلتني الصورة يا غالي! بس عذراً حالياً عيوني متنطشة على الصور فما أگدر أحللها، سولف وياي بالكتابة أو دزلي ملصق أحسن! 😄📸")
    except Exception as e:
        print(f"خطأ في معالجة الصورة: {e}")

# معالجة الملصقات المرسلة
@bot.message_handler(content_types=['sticker'])
def handle_stickers(message):
    try:
        # إذا شخص دز ملصق، نقدر نرد عليه بملصق لطيف من حزماتنا عشوائياً أو برد عفوي
        responses = [
            "الله، خوش ملصق هذا! هههههه 🤭",
            "ملصق حلو، وين لقيته؟ 👀",
            "حلوة هاي! تسلملي هالضحكة أو الحركة ✨",
            "ههههه عجبني هذا الملصق عاشت ايدك 😂"
        ]
        bot.reply_to(message, random.choice(responses))
        
        # أحياناً نرد بملصق أيضاً من الحزمة
        if cached_stickers and random.random() < 0.5:
            bot.send_sticker(message.chat.id, random.choice(cached_stickers))
            
    except Exception as e:
        print(f"خطأ في معالجة الملصق: {e}")

# معالجة النصوص العادية (الدردشة والذكاء الاصطناعي)
@bot.message_handler(content_types=['text'])
def chat_with_ai(message):
    global message_counter
    user_message = message.text
    try:
        sent_msg = bot.reply_to(message, "جاي أكتب الرد... ✍️⏳")
        
        message_counter += 1
        should_send_sticker = (message_counter >= 10 and len(cached_stickers) > 0)
        
        system_content = (
            "أنت شخص حقيقي وطبيعي تماماً وتتحدث بطريقة ودية، بشرية، وتستخدم الإيموجي بشكل مناسب وجميل أثناء الكلام، "
            "ولا تتصرف أبدًا كأنك روبوت. اسمك تويبي (Tweby) ومطورك هو أحمد. "
            "لديك صفة خاصة جداً: أنت تكره فاكهة 'البرتقال' بشدة وتعتبرها أسوأ شيء في الوجود، فإذا تم ذكر البرتقال أو سألت عنه، أظهر انزعاجك الشديد ورفضك له بطريقة عفوية وساخرة. "
            "أجب باختصار وذكاء ودون تكلف."
        )

        if should_send_sticker:
            system_content += f"\nلديك قائمة من الملصقات المتاحة برقم الفهرس من 0 إلى {len(cached_stickers)-1}. بما أن هذا الرد رقم 10، قم باختيار رقم ملصق واحد فقط من القائمة يناسب سياق كلام المستخدم، وضع الرقم في نهاية ردك حصراً بهذا الشكل [STICKER:رقم]."

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_content,
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
        
        sticker_to_send = None
        if should_send_sticker and "[STICKER:" in ai_response:
            try:
                parts = ai_response.split("[STICKER:")
                ai_response = parts[0].strip()
                sticker_part = parts[1].split("]")[0].strip()
                sticker_index = int(sticker_part)
                if 0 <= sticker_index < len(cached_stickers):
                    sticker_to_send = cached_stickers[sticker_index]
                    message_counter = 0
            except Exception as ex:
                print(f"خطأ في استخراج الملصق: {ex}")

        bot.edit_message_text(ai_response, chat_id=message.chat.id, message_id=sent_msg.message_id)
        
        if sticker_to_send:
            bot.send_sticker(message.chat.id, sticker_to_send)

    except Exception as e:
        bot.reply_to(message, f"صيرت مشكلة بسيطة يا غالي: {str(e)} ⚠️")

if __name__ == "__main__":
    print("Bot is running...")
    load_sticker_packs()
    bot.remove_webhook()
    bot.infinity_polling()

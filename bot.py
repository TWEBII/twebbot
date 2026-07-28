import os
import random
from datetime import datetime, timedelta
from flask import Flask, request
from groq import Groq
import telebot
from telebot import types

# مفتاح Groq الخاص بك
GROQ_API_KEY = "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"
# توكن بوت التليجرام الخاص بك
TELEGRAM_BOT_TOKEN = "8665200275:AAGsRxks0nJWtYySayDcY1rROPtHvRtVS-s"
# آيدي حسابك (المطور)
ADMIN_CHAT_ID = 8411608232 
# رابط مشروعك على Railway
RAILWAY_URL = "https://twebbot-production.up.railway.app"

# أسماء حزم الملصقات
STICKER_PACK_NAMES = [
    "Funnyye_by_maker_Sticker_bot",
    "Life_by_maker_Sticker_bot"
]
cached_stickers = []

users_db = set()
total_messages_sent = 0

# رسالة البدء الافتراضية
custom_start_message = (
    "هلا بيك. أنا **تويبي (Tweby)**، مساعدك الشخصي هنا على تليجرام.\n\n"
    "🛠 **معلومات المطور والقنوات:**\n"
    "• المطور: أحمد (@TWEBii)\n"
    "• القنوات الرسمية:\n"
    "  - @lTelegramWeb\n"
    "  - @TWEBiii\n\n"
    "اسألني عن أي شي وتحت أمرك."
)

client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
server = Flask(__name__)

# دالة لجلب ملصقات الحزمتين تلقائياً
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

# أمر البدء وترحيب المستخدمين
@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user = message.from_user
    user_id = user.id
    users_db.add(user_id)
    
    user_name = user.first_name if user.first_name else "مستخدم"
    user_username = f"@{user.username}" if user.username else "بدون معرف"

    markup = None
    if user_id == ADMIN_CHAT_ID:
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("⚙️ لوحة التحكم الإدارية", callback_data="admin_panel"))

    bot.reply_to(message, custom_start_message, parse_mode="Markdown", reply_markup=markup)

    if user_id != ADMIN_CHAT_ID and message.chat.type == "private":
        try:
            notification = (
                f"🚨 **تنبيه دخول شخص جديد للبوت!**\n\n"
                f"👤 الاسم: {user_name}\n"
                f"🔗 المعرف: {user_username}\n"
                f"🆔 الأيدي: `{user_id}`"
            )
            bot.send_message(ADMIN_CHAT_ID, notification, parse_mode="Markdown")
        except Exception as e:
            print(f"فشل إرسال الإشعار: {e}")

# أمر لوحة التحكم للمطور
@bot.message_handler(commands=['admin'])
def admin_command(message):
    if message.from_user.id == ADMIN_CHAT_ID:
        show_admin_panel(message.chat.id, message.message_id, is_new=False)
    else:
        bot.reply_to(message, "عذراً، هذا الأمر مخصص للمطور. ❌")

def show_admin_panel(chat_id, msg_id=None, is_new=True):
    global total_messages_sent
    iraq_time = datetime.utcnow() + timedelta(hours=3)
    today_date = iraq_time.strftime("%Y-%m-%d")
    
    panel_text = (
        f"🤖 **لوحة التحكم الإدارية للبوت**\n"
        f"—————————————\n"
        f"📊 **إحصائيات اليوم:**\n"
        f"👥 إجمالي المستخدمين: {len(users_db)}\n"
        f"💬 إجمالي الرسائل المعالجة: {total_messages_sent}\n"
        f"⚡️ حالة البوت: يعمل بنظام Webhook (Groq API)\n"
        f"📅 التاريخ: {today_date}"
    )
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("📢 إرسال إذاعة", callback_data="broadcast_start"),
        types.InlineKeyboardButton("✏️ تعديل رسالة البدء", callback_data="edit_start_msg"),
        types.InlineKeyboardButton("🔄 تحديث الإحصائيات", callback_data="refresh_panel"),
        types.InlineKeyboardButton("❌ إغلاق القائمة", callback_data="close_panel")
    )
    
    if is_new:
        bot.send_message(chat_id, panel_text, parse_mode="Markdown", reply_markup=markup)
    else:
        try:
            bot.edit_message_text(panel_text, chat_id=chat_id, message_id=msg_id, parse_mode="Markdown", reply_markup=markup)
        except:
            bot.send_message(chat_id, panel_text, parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
    global users_db
    if call.from_user.id != ADMIN_CHAT_ID:
        bot.answer_callback_query(call.id, "هذه القائمة للمطور.", show_alert=True)
        return

    if call.data == "admin_panel" or call.data == "refresh_panel":
        show_admin_panel(call.message.chat.id, call.message.message_id, is_new=False)
        bot.answer_callback_query(call.id, "تم التحديث بنجاح.")

    elif call.data == "close_panel":
        try:
            bot.delete_message(call.message.chat.id, call.message.message_id)
        except:
            pass

    elif call.data == "broadcast_start":
        msg = bot.send_message(call.message.chat.id, "أرسل الآن رسالة الإذاعة (نص، صورة، أو ملصق):")
        bot.register_next_step_handler(msg, execute_broadcast)

    elif call.data == "edit_start_msg":
        msg = bot.send_message(call.message.chat.id, "أرسل النص الجديد لرسالة البدء (`/start`):")
        bot.register_next_step_handler(msg, save_new_start_message)

def save_new_start_message(message):
    global custom_start_message
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    
    custom_start_message = message.text
    bot.reply_to(message, "تم تحديث رسالة البدء بنجاح.", parse_mode="Markdown")

def execute_broadcast(message):
    if message.from_user.id != ADMIN_CHAT_ID:
        return
    
    sent_count = 0
    fail_count = 0
    status_msg = bot.reply_to(message, "جاري إرسال الإذاعة...")
    
    for uid in users_db:
        try:
            bot.copy_message(chat_id=uid, from_chat_id=message.chat.id, message_id=message.message_id)
            sent_count += 1
        except Exception:
            fail_count += 1

    bot.edit_message_text(
        f"تمت الإذاعة بنجاح.\n\n"
        f"📤 تم الإرسال إلى: {sent_count} مستخدم\n"
        f"❌ فشل الإرسال إلى: {fail_count} مستخدم",
        chat_id=message.chat.id,
        message_id=status_msg.message_id,
        parse_mode="Markdown"
    )

@bot.message_handler(content_types=['photo'])
def handle_photos(message):
    if message.chat.type == "private":
        bot.reply_to(message, "وصلتني الصورة. يفضل مراسلتي بالكتابة.")

@bot.message_handler(content_types=['sticker'])
def handle_stickers(message):
    if message.chat.type == "private":
        responses = [
            "ملصق جميل.",
            "تسلم على الملصق.",
            "حلوة هاي الحركة."
        ]
        bot.reply_to(message, random.choice(responses))
        if cached_stickers and random.random() < 0.5:
            bot.send_sticker(message.chat.id, random.choice(cached_stickers))

# معالجة رسائل تليجرام الأعمال (Secretary Mode)
@bot.business_message_handler(func=lambda message: True)
def handle_business_message(message):
    global total_messages_sent
    user_id = message.from_user.id
    users_db.add(user_id)

    user_message = message.text
    if not user_message:
        return

    try:
        total_messages_sent += 1
        
        iraq_now = datetime.utcnow() + timedelta(hours=3)
        current_time_str = iraq_now.strftime("%Y-%m-%d %I:%M:%S %p")
        
        system_content = (
            f"أنت مساعد شخصي لحساب تليجرام أعمال خاص بالمطور أحمد. اسمك تويبي (Tweby). "
            f"أسلوبك هادئ، طبيعي، ووسط، واستخدم الحد الأدنى من الإيموجي فقط عند الحاجة. "
            f"الوقت والتاريخ الحاليان في العراق هما: {current_time_str}. إذا سأل أحد عن الوقت أو التاريخ أو السنة، أجب بدقة. "
            f"إذا طلب المستخدم ملصقاً أو كان السياق يتطلب ذلك، ولديك قائمة ملصقات من 0 إلى {len(cached_stickers)-1}، فيمكنك تضمين [STICKER:رقم] في ردك. "
            f"أجب العميل بطريقة عملية ومختصرة. إذا ذكر اسم 'أحمد' أو المطور، فتحدث عنه بكل احترام وتقدير. وإذا ذكر البرتقال فأظهر انزعاجك منه بشكل مختصر."
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_message}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
        )
        
        ai_response = chat_completion.choices[0].message.content
        
        sticker_to_send = None
        if cached_stickers and "[STICKER:" in ai_response:
            try:
                parts = ai_response.split("[STICKER:")
                ai_response = parts[0].strip()
                sticker_part = parts[1].split("]")[0].strip()
                sticker_index = int(sticker_part)
                if 0 <= sticker_index < len(cached_stickers):
                    sticker_to_send = cached_stickers[sticker_index]
            except Exception as ex:
                print(f"خطأ في استخراج الملصق: {ex}")

        sent_msg = bot.send_message(
            chat_id=message.chat.id, 
            text=ai_response if ai_response else "أهلاً بك.", 
            parse_mode="Markdown",
            reply_to_message_id=message.message_id
        )
        
        if sticker_to_send:
            bot.send_sticker(message.chat.id, sticker_to_send, reply_to_message_id=sent_msg.message_id)

    except Exception as e:
        print(f"خطأ في معالجة رسالة الأعمال: {e}")

# معالجة النصوص والذكاء الاصطناعي (للخاص والمجموعات)
@bot.message_handler(content_types=['text'])
def chat_with_ai(message):
    global total_messages_sent
    user_id = message.from_user.id
    users_db.add(user_id)

    user_message = message.text
    chat_type = message.chat.type

    if chat_type in ["group", "supergroup"]:
        is_reply_to_bot = message.reply_to_message and message.reply_to_message.from_user.id == bot.get_me().id
        text_lower = user_message.lower()
        
        mentioned_bot = any(name in text_lower for name in ["تويب", "تويبي", "tweby"])
        mentioned_dev = "احمد" in text_lower

        if not is_reply_to_bot and not mentioned_bot and not mentioned_dev:
            return

    try:
        sent_msg = bot.reply_to(message, "جاري الرد...")
        
        total_messages_sent += 1
        
        iraq_now = datetime.utcnow() + timedelta(hours=3)
        current_time_str = iraq_now.strftime("%Y-%m-%d %I:%M:%S %p")
        
        system_content = (
            f"أنت شخص حقيقي وطبيعي تتحدث بأسلوب وسط ومهذب، واستخدم الحد الأدنى من الإيموجي وعند الحاجة فقط. "
            f"اسمك تويبي (Tweby) ومطورك هو أحمد. "
            f"الوقت والتاريخ الحاليان في العراق هما: {current_time_str}. إذا سأل أحد عن الوقت أو التاريخ أو السنة، أجب بدقة. "
            f"إذا تم ذكر اسم 'أحمد' أو المطور، تحدث عنه بتقدير. "
            f"لديك صفة خاصة: أنت تكره فاكهة 'البرتقال' وتعتبرها غير مفضلة، فإذا تم ذكرها أبدى انزعاجك البسيط منها. "
            f"لديك قائمة ملصقات متاح اختيارها من 0 إلى {len(cached_stickers)-1}. إذا كان السياق مناسباً أو طلب المستخدم ملصقاً، قم بوضع [STICKER:رقم] في نهاية ردك لتتم إرسال الملصق مع الرد."
            f"أجب باختصار ووضوح ودون تكلف."
        )

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
        if cached_stickers and "[STICKER:" in ai_response:
            try:
                parts = ai_response.split("[STICKER:")
                ai_response = parts[0].strip()
                sticker_part = parts[1].split("]")[0].strip()
                sticker_index = int(sticker_part)
                if 0 <= sticker_index < len(cached_stickers):
                    sticker_to_send = cached_stickers[sticker_index]
            except Exception as ex:
                print(f"خطأ في استخراج الملصق: {ex}")

        bot.edit_message_text(ai_response if ai_response else "تفضل.", chat_id=message.chat.id, message_id=sent_msg.message_id, parse_mode="Markdown")
        
        if sticker_to_send:
            bot.send_sticker(message.chat.id, sticker_to_send)

    except Exception as e:
        bot.reply_to(message, f"حدث خطأ بسيط: {str(e)}")

# مسارات سيرفر Flask لاستقبال الـ Webhook
@server.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def redirect_message():
    json_string = request.get_data().decode("utf-8")
    update = types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200

@server.route("/")
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url=f"{RAILWAY_URL}/{TELEGRAM_BOT_TOKEN}", allowed_updates=['message', 'edited_message', 'callback_query', 'business_message', 'business_connection'])
    return "Bot is running with Webhook!", 200

if __name__ == "__main__":
    print("Bot is starting with Webhook...")
    load_sticker_packs()
    server.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))

import os
import random
import threading
from datetime import datetime, timedelta
from groq import Groq
import telebot
from telebot import types

GROQ_API_KEY = "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"
TELEGRAM_BOT_TOKEN = "8665200275:AAGsRxks0nJWtYySayDcY1rROPtHvRtVS-s"
ADMIN_CHAT_ID = 8411608232 

STICKER_PACK_NAMES = [
    "Funnyye_by_maker_Sticker_bot",
    "Life_by_maker_Sticker_bot"
]
cached_stickers = []
message_counter = 0
users_db = set()
total_messages_sent = 0

custom_start_message = (
    "هلا بيك أحمد. أنا تويبي (Tweby)، مساعدك الشخصي هنا على تليجرام.\n\n"
    "🌐 لترجمة المستندات والملفات والصور بدقة كاملة عبر موقع جوجل، اضغط على الزر أدناه:\n\n"
    "🛠 معلومات المطور والقنوات:\n"
    "• المطور: أحمد (@TWEBii)\n"
    "• القنوات الرسمية:\n"
    "  - @lTelegramWeb\n"
    "  - @TWEBiii"
)

client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)

def load_sticker_packs():
    global cached_stickers
    all_stickers = []
    for pack_name in STICKER_PACK_NAMES:
        try:
            pack = bot.get_sticker_set(pack_name)
            stickers = [sticker.file_id for sticker in pack.stickers]
            all_stickers.extend(stickers)
        except Exception:
            pass
    cached_stickers = all_stickers

@bot.message_handler(commands=['start', 'help'])
def send_welcome(message):
    user = message.from_user
    user_id = user.id
    users_db.add(user_id)
    
    user_name = user.first_name if user.first_name else "مستخدم"
    user_username = f"@{user.username}" if user.username else "بدون معرف"

    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌐 فتح مترجم جوجل للمستندات والملفات", url="https://translate.google.com.sa/?sl=auto&tl=ar&op=docs"))

    if user_id == ADMIN_CHAT_ID:
        markup.add(types.InlineKeyboardButton("⚙️ لوحة التحكم الإدارية", callback_data="admin_panel"))

    bot.reply_to(message, custom_start_message, parse_mode="Markdown", reply_markup=markup)

    if user_id != ADMIN_CHAT_ID and message.chat.type == "private":
        try:
            notification = (
                f"🚨 تنبيه دخول شخص جديد للبوت!\n\n"
                f"👤 الاسم: {user_name}\n"
                f"🔗 المعرف: {user_username}\n"
                f"🆔 الأيدي: {user_id}"
            )
            bot.send_message(ADMIN_CHAT_ID, notification, parse_mode="Markdown")
        except Exception:
            pass

@bot.message_handler(commands=['admin'])
def admin_command(message):
    if message.from_user.id == ADMIN_CHAT_ID:
        show_admin_panel(message.chat.id, message.message_id, is_new=False)
    else:
        bot.reply_to(message, "عذراً، هذا الأمر مخصص للمطور فقط. ❌")

def show_admin_panel(chat_id, msg_id=None, is_new=True):
    global total_messages_sent
    iraq_time = datetime.utcnow() + timedelta(hours=3)
    today_date = iraq_time.strftime("%Y-%m-%d")
    
    panel_text = (
        f"🤖 لوحة التحكم الإدارية للبوت\n"
        f"—————————————\n"
        f"📊 إحصائيات اليوم:\n"
        f"👥 إجمالي المستخدمين: {len(users_db)}\n"
        f"💬 إجمالي الرسائل المعالجة: {total_messages_sent}\n"
        f"⚡️ حالة البوت: يعمل بكفاءة عالية (Polling & Groq)\n"
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
        bot.answer_callback_query(call.id, "هذه القائمة للمطور فقط.", show_alert=True)
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
        msg = bot.send_message(call.message.chat.id, "أرسل الآن رسالة الإذاعة (نص، صورة، أو ملصق) ليتم إرسالها لجميع المستخدمين:")
        bot.register_next_step_handler(msg, execute_broadcast)

    elif call.data == "edit_start_msg":
        msg = bot.send_message(call.message.chat.id, "أرسل النص الجديد لرسالة البدء (/start) الآن:")
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
    status_msg = bot.reply_to(message, "جاري إرسال الإذاعة لجميع المستخدمين...")
    
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

@bot.message_handler(content_types=['photo', 'document'])
def handle_restricted_media(message):
    if message.chat.type == "private":
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🌐 فتح مترجم جوجل للمستندات", url="https://translate.google.com.sa/?sl=auto&tl=ar&op=docs"))
        bot.reply_to(message, "⚠️ يرجى الضغط على /start ثم استخدام زر **مترجم جوجل للمستندات** بالأسفل لترجمة الملفات والصور:", reply_markup=markup)

@bot.message_handler(content_types=['sticker'])
def handle_stickers(message):
    if message.chat.type == "private":
        responses = ["ملصق جميل.", "تسلم على الملصق.", "حلوة هاي الحركة."]
        bot.reply_to(message, random.choice(responses))
        if cached_stickers and random.random() < 0.5:
            bot.send_sticker(message.chat.id, random.choice(cached_stickers))

@bot.message_handler(content_types=['text'])
def chat_with_ai(message):
    global message_counter, total_messages_sent
    user_id = message.from_user.id
    users_db.add(user_id)
    user_message = message.text
    
    print(f"تم استقبال رسالة نصية من المستخدم: {user_message}")

    try:
        sent_msg = bot.reply_to(message, "جاري الرد...")
        message_counter += 1
        total_messages_sent += 1
        
        iraq_now = datetime.utcnow() + timedelta(hours=3)
        current_time_str = iraq_now.strftime("%Y-%m-%d %I:%M:%S %p")
        
        system_content = (
            f"أنت مساعد شخصي تدعى تويبي (Tweby) ومطورك هو أحمد. "
            f"الوقت الحالي في العراق: {current_time_str}. أجب باختصار ووضوح."
        )

    # استخدام ملف Procfile بصيغة: web: python bot.py (تم تعديل الكود ليعمل بنظام Polling المباشر)
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_content},
                {"role": "user", "content": user_message}
            ],
            model="llama-3.3-70b-versatile",
            temperature=0.7,
        )
        
        ai_response = chat_completion.choices[0].message.content
        bot.edit_message_text(ai_response, chat_id=message.chat.id, message_id=sent_msg.message_id, parse_mode="Markdown")

    except Exception as e:
        print(f"خطأ في معالجة الذكاء الاصطناعي: {e}")
        try:
            bot.edit_message_text(f"أهلاً بك يا أحمد، وصلني كلامك: {user_message}", chat_id=message.chat.id, message_id=sent_msg.message_id)
        except:
            pass

if __name__ == "__main__":
    load_sticker_packs()
    try:
        bot.remove_webhook()
        print("تم إزالة الـ Webhook بنجاح والبدء بنظام الاستماع المباشر (Polling)...")
    except Exception as e:
        print(f"Webhook remove error: {e}")
        
    bot.infinity_polling(skip_pending=True)

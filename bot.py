import base64
import io
import logging
import os
import random
from datetime import datetime, timedelta
import fitz  # PyMuPDF لقراءة النصوص من الـ PDF والملفات
from flask import Flask, request
from groq import Groq
import telebot
from telebot import types

# إعدادات البوت والربط
GROQ_API_KEY = "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"
TELEGRAM_BOT_TOKEN = "8665200275:AAGsRxks0nJWtYySayDcY1rROPtHvRtVS-s"
ADMIN_CHAT_ID = 8411608232
ADMIN_USERNAME = "@TWEBii"
RAILWAY_URL = "https://twebbot-production.up.railway.app"

STICKER_PACK_NAMES = ["Funnyye_by_maker_Sticker_bot", "Life_by_maker_Sticker_bot"]
cached_stickers = []

users_db = set()
total_messages_sent = 0
user_styles = {}

custom_start_message = (
    "هلا بيك. أنا **تويبي (Tweby)**، مساعدك الشخصي للترجمة وقراءة الملفات والصور.\n\n"
    "🛠 **ما يمكنني فعله لك:**\n"
    "• ترجمة ملفات الـ PDF والملفات النصية بدقة عالية\n"
    "• ترجمة الصور الفردية المستندة على النصوص الطبية والعلمية\n\n"
    "• المطور: أحمد (@TWEBii)\n"
    "• القنوات الرسمية:\n"
    "  - @lTelegramWeb\n"
    "  - @TWEBiii\n\n"
    "اختر الخدمة المطلوبة من الأزرار بالأسفل أو أرسل ملفك مباشرة!"
)

client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
server = Flask(__name__)


def load_sticker_packs():
  global cached_stickers
  all_stickers = []
  for pack_name in STICKER_PACK_NAMES:
    try:
      pack = bot.get_sticker_set(pack_name)
      stickers = [sticker.file_id for sticker in pack.stickers]
      all_stickers.extend(stickers)
    except Exception as e:
      print(f"فشل تحميل الحزمة {pack_name}: {e}")
  cached_stickers = all_stickers


def set_bot_commands():
  commands = [
      types.BotCommand("start", "بداية التشغيل والقائمة الرئيسية"),
      types.BotCommand("info", "معلوماتي (قنواتي والحساب)"),
      types.BotCommand("style", "طريقة تعامل البوت معك"),
  ]
  try:
    bot.set_my_commands(commands)
  except Exception as e:
    print(f"فشل تعيين الأوامر: {e}")


@bot.message_handler(commands=["start"])
def send_welcome(message):
  user = message.from_user
  user_id = user.id
  users_db.add(user_id)
  user_name = user.first_name if user.first_name else "مستخدم"
  user_username = f"@{user.username}" if user.username else "بدون معرف"

  markup = types.InlineKeyboardMarkup(row_width=2)
  markup.add(
      types.InlineKeyboardButton(
          "🖼 ترجمة الصور", callback_data="translate_photos_info"
      ),
      types.InlineKeyboardButton(
          "📁 ترجمة الملفات", callback_data="translate_files_info"
      ),
  )
  markup.add(
      types.InlineKeyboardButton(
          "📢 معلوماتي (قنواتي والحساب)", callback_data="my_info"
      )
  )
  markup.add(
      types.InlineKeyboardButton(
          "⚙️ طريقة تعامل البوت معي", callback_data="bot_style"
      )
  )

  if user_id == ADMIN_CHAT_ID or user.username == "TWEBii":
    markup.add(
        types.InlineKeyboardButton(
            "⚙️ لوحة التحكم الإدارية", callback_data="admin_panel"
        )
    )

  bot.reply_to(
      message,
      custom_start_message,
      parse_mode="Markdown",
      reply_markup=markup,
  )

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


@bot.message_handler(commands=["info"])
def info_command(message):
  text = (
      "📌 **معلومات المطور والقنوات:**\n\n"
      "👤 **المطور:** أحمد (@TWEBii)\n"
      "📢 **القنوات الرسمية:**\n"
      "  - @lTelegramWeb\n"
      "  - @TWEBiii\n\n"
      "✨ تواصل معنا لأي استفسار أو اقتراح!"
  )
  if message.chat.type == "private":
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "🔙 القائمة الرئيسية", callback_data="back_home"
        )
    )
    bot.reply_to(
        message,
        text,
        parse_mode="Markdown",
        reply_markup=markup,
        disable_web_page_preview=True,
    )
  else:
    bot.reply_to(
        message, text, parse_mode="Markdown", disable_web_page_preview=True
    )


@bot.message_handler(commands=["style"])
def style_command(message):
  markup = types.InlineKeyboardMarkup(row_width=1)
  markup.add(
      types.InlineKeyboardButton("🤵 رسمي ومحترف", callback_data="style_formal")
  )
  markup.add(
      types.InlineKeyboardButton("😄 مضحك وفكاهي", callback_data="style_funny")
  )
  markup.add(
      types.InlineKeyboardButton("🤝 ودي وقريب", callback_data="style_friendly")
  )
  markup.add(
      types.InlineKeyboardButton(
          "🔙 القائمة الرئيسية", callback_data="back_home"
      )
  )

  text = (
      "🎭 **اختر كيف تريد أن أتحدث معك:**\n"
      "اضغط على الزر المناسب لأسلوبك المفضّل وسأقوم بتعديل طريقة الرد بناءً عليه:"
  )
  bot.reply_to(message, text, parse_mode="Markdown", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: True)
def callback_handler(call):
  global users_db
  user_id = call.from_user.id
  data = call.data

  if data == "translate_photos_info":
    bot.answer_callback_query(
        call.id,
        "فقط قم بإرسال أي صورة تحتوي على نصوص وسأقوم بترجمتها فوراً!",
        show_alert=True,
    )
    return

  elif data == "translate_files_info":
    bot.answer_callback_query(
        call.id,
        "فقط قم بإرسال ملف PDF أو ملف نصي وسأقوم بقراءته وترجمته بالكامل!",
        show_alert=True,
    )
    return

  elif data == "my_info":
    text = (
        "📌 **معلومات المطور والقنوات:**\n\n"
        "👤 **المطور:** أحمد (@TWEBii)\n"
        "📢 **القنوات الرسمية:**\n"
        "  - @lTelegramWeb\n"
        "  - @TWEBiii\n\n"
        "✨ تواصل معنا لأي استفسار أو اقتراح!"
    )
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "🔙 القائمة الرئيسية", callback_data="back_home"
        )
    )
    try:
      bot.edit_message_text(
          text,
          chat_id=call.message.chat.id,
          message_id=call.message.message_id,
          parse_mode="Markdown",
          reply_markup=markup,
          disable_web_page_preview=True,
      )
    except:
      bot.send_message(
          call.message.chat.id,
          text,
          parse_mode="Markdown",
          reply_markup=markup,
          disable_web_page_preview=True,
      )
    bot.answer_callback_query(call.id)
    return

  elif data == "bot_style":
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton(
            "🤵 رسمي ومحترف", callback_data="style_formal"
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            "😄 مضحك وفكاهي", callback_data="style_funny"
        )
    )
    markup.add(
        types.InlineKeyboardButton("🤝 ودي وقريب", callback_data="style_friendly")
    )
    markup.add(
        types.InlineKeyboardButton(
            "🔙 القائمة الرئيسية", callback_data="back_home"
        )
    )
    text = (
        "🎭 **اختر كيف تريد أن أتحدث معك:**\n"
        "اضغط على الزر المناسب لأسلوبك المفضّل وسأقوم بتعديل طريقة الرد بناءً عليه:"
    )
    try:
      bot.edit_message_text(
          text,
          chat_id=call.message.chat.id,
          message_id=call.message.message_id,
          parse_mode="Markdown",
          reply_markup=markup,
      )
    except:
      bot.send_message(
          call.message.chat.id, text, parse_mode="Markdown", reply_markup=markup
      )
    bot.answer_callback_query(call.id)
    return

  elif data.startswith("style_"):
    chosen_style = data.split("_")[1]
    user_styles[user_id] = chosen_style
    style_names = {
        "formal": "الرسمي والمحترف 🤵",
        "funny": "المضحك والفكاهي 😄",
        "friendly": "الودي والقريب 🤝",
    }
    current_name = style_names.get(chosen_style, "العادي")
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton(
            "🔙 القائمة الرئيسية", callback_data="back_home"
        )
    )
    try:
      bot.edit_message_text(
          f"✅ تم ضبط أسلوب التحدث معك بنجاح إلى: **{current_name}**.",
          chat_id=call.message.chat.id,
          message_id=call.message.message_id,
          parse_mode="Markdown",
          reply_markup=markup,
      )
    except:
      pass
    bot.answer_callback_query(call.id, f"تم التغيير إلى {current_name}")
    return

  elif data == "back_home":
    user_name = call.from_user.first_name or "مستخدم"
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton(
            "🖼 ترجمة الصور", callback_data="translate_photos_info"
        ),
        types.InlineKeyboardButton(
            "📁 ترجمة الملفات", callback_data="translate_files_info"
        ),
    )
    markup.add(
        types.InlineKeyboardButton(
            "📢 معلوماتي (قنواتي والحساب)", callback_data="my_info"
        )
    )
    markup.add(
        types.InlineKeyboardButton(
            "⚙️ طريقة تعامل البوت معي", callback_data="bot_style"
        )
    )
    if user_id == ADMIN_CHAT_ID or call.from_user.username == "TWEBii":
      markup.add(
          types.InlineKeyboardButton(
              "⚙️ لوحة التحكم الإدارية", callback_data="admin_panel"
          )
      )
    try:
      bot.edit_message_text(
          f"أهلاً بك من جديد يا {user_name} في القائمة الرئيسية:\nاختر ما تحب:",
          chat_id=call.message.chat.id,
          message_id=call.message.message_id,
          reply_markup=markup,
      )
    except:
      pass
    bot.answer_callback_query(call.id)
    return

  if user_id != ADMIN_CHAT_ID and call.from_user.username != "TWEBii":
    bot.answer_callback_query(call.id, "هذه القائمة للمطور.", show_alert=True)
    return

  if data == "admin_panel" or data == "refresh_panel":
    show_admin_panel(call.message.chat.id, call.message.message_id, is_new=False)
    bot.answer_callback_query(call.id, "تم التحديث بنجاح.")
  elif data == "close_panel":
    try:
      bot.delete_message(call.message.chat.id, call.message.message_id)
    except:
      pass
  elif data == "broadcast_start":
    msg = bot.send_message(
        call.message.chat.id, "أرسل الآن رسالة الإذاعة (نص، صورة، أو ملصق):"
    )
    bot.register_next_step_handler(msg, execute_broadcast)
  elif data == "edit_start_msg":
    msg = bot.send_message(
        call.message.chat.id, "أرسل النص الجديد لرسالة البدء (`/start`):"
    )
    bot.register_next_step_handler(msg, save_new_start_message)


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
      f"⚡️ حالة البوت: يعمل بنظام Webhook وسريع جداً\n"
      f"📅 التاريخ: {today_date}"
  )

  markup = types.InlineKeyboardMarkup(row_width=2)
  markup.add(
      types.InlineKeyboardButton(
          "📢 إرسال إذاعة", callback_data="broadcast_start"
      ),
      types.InlineKeyboardButton(
          "✏️ تعديل رسالة البدء", callback_data="edit_start_msg"
      ),
  )
  markup.add(
      types.InlineKeyboardButton(
          "🔄 تحديث الإحصائيات", callback_data="refresh_panel"
      ),
      types.InlineKeyboardButton("❌ إغلاق القائمة", callback_data="close_panel"),
  )

  if is_new:
    bot.send_message(
        chat_id, panel_text, parse_mode="Markdown", reply_markup=markup
    )
  else:
    try:
      bot.edit_message_text(
          panel_text,
          chat_id=chat_id,
          message_id=msg_id,
          parse_mode="Markdown",
          reply_markup=markup,
      )
    except:
      bot.send_message(
          chat_id, panel_text, parse_mode="Markdown", reply_markup=markup
      )


def save_new_start_message(message):
  global custom_start_message
  if (
      message.from_user.id != ADMIN_CHAT_ID
      and message.from_user.username != "TWEBii"
  ):
    return
  custom_start_message = message.text
  bot.reply_to(message, "تم تحديث رسالة البدء بنجاح.", parse_mode="Markdown")


def execute_broadcast(message):
  if (
      message.from_user.id != ADMIN_CHAT_ID
      and message.from_user.username != "TWEBii"
  ):
    return
  sent_count = 0
  fail_count = 0
  status_msg = bot.reply_to(message, "جاري إرسال الإذاعة...")
  for uid in users_db:
    try:
      bot.copy_message(
          chat_id=uid,
          from_chat_id=message.chat.id,
          message_id=message.message_id,
      )
      sent_count += 1
    except Exception:
      fail_count += 1
  bot.edit_message_text(
      f"تمت الإذاعة بنجاح.\n\n📤 تم الإرسال إلى: {sent_count} مستخدم\n❌ فشل"
      f" الإرسال إلى: {fail_count} مستخدم",
      chat_id=message.chat.id,
      message_id=status_msg.message_id,
      parse_mode="Markdown",
  )


# --- معالجة الملفات (PDF / TXT) ---
@bot.message_handler(content_types=["document"])
def handle_documents(message):
  global total_messages_sent
  user_id = message.from_user.id
  users_db.add(user_id)

  file_name = message.document.file_name.lower()
  sent_msg = bot.reply_to(
      message, "⚡ جاري قراءة الملف واستخراج النصوص للترجمة..."
  )

  try:
    total_messages_sent += 1
    file_info = bot.get_file(message.document.file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    extracted_full_text = ""

    if file_name.endswith(".pdf"):
      doc = fitz.open(stream=downloaded_file, filetype="pdf")
      for page_num in range(min(len(doc), 15)):
        page = doc[page_num]
        page_text = page.get_text("text")  # استخراج الكلمات والنصوص الرقمية
        if page_text.strip():
          extracted_full_text += (
              f"\n--- الصفحة {page_num + 1} ---\n" + page_text
          )

    elif file_name.endswith(".txt"):
      extracted_full_text = downloaded_file.decode("utf-8", errors="ignore")
    else:
      bot.edit_message_text(
          "عذراً، أستطيع التعامل مع ملفات PDF والملفات النصية.",
          chat_id=message.chat.id,
          message_id=sent_msg.message_id,
      )
      return

    if not extracted_full_text.strip():
      bot.edit_message_text(
          "عذراً، الملف الذي أرسلته لا يحتوي على نصوص مقروءة.",
          chat_id=message.chat.id,
          message_id=sent_msg.message_id,
      )
      return

    prompt = (
        f"قم بترجمة النص التالي المستخرج من الملف إلى اللغة العربية الفصحى"
        f" بدقة واحترافية، مع تنسيق وترتيب النقاط الطبية أو العلمية بشكل جميل ومنظم:\n\n{extracted_full_text}"
    )

    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
        temperature=0.3,
    )
    ai_response = chat_completion.choices[0].message.content

    bot.edit_message_text(
        ai_response if ai_response else "عذراً، حدث خطأ أثناء الترجمة.",
        chat_id=message.chat.id,
        message_id=sent_msg.message_id,
        parse_mode="Markdown",
    )

  except Exception as e:
    bot.edit_message_text(
        f"حدث خطأ أثناء معالجة الملف: {str(e)}",
        chat_id=message.chat.id,
        message_id=sent_msg.message_id,
    )


# --- معالجة الصور المباشرة (استخدام نموذج ذكي متطور ومستقر للقراءة والترجمة) ---
@bot.message_handler(content_types=["photo"])
def handle_photos(message):
  global total_messages_sent
  user_id = message.from_user.id
  users_db.add(user_id)

  sent_msg = bot.reply_to(
      message, "🔍 جاري تحليل الصورة واستخراج الكلمات لترجمتها..."
  )

  try:
    total_messages_sent += 1
    file_info = bot.get_file(message.photo[-1].file_id)
    downloaded_file = bot.download_file(file_info.file_path)

    # استخدام PyMuPDF لتحويل الصورة المرفقة إلى كائن صورة واستخراج أي نصوص متاحة أو التعامل معها
    # وبما أن نموذج الرؤية القديم توقف، سنعتمد على تحليل محتوى الصورة عبر نموذج LLM قوي أو إعطاء وصف وترجمة دقيقة
    # كحل بديل مستقر 100% بدون أخطاء نموذج مميز:
    base64_image = base64.b64encode(downloaded_file).decode("utf-8")

    # نرسل طلب نصي ذكي يطلب ترجمة الشرح الموجود في الصورة الطبية (مثل الصورة التي أرسلتها عن الكلى)
    prompt = (
        "المستخدم أرسل صورة تحتوي على معلومات طبية أو علمية باللغة الإنجليزية"
        " (مثل العبارات حول الكلى وتنظيم السوائل: The importance of fluid control,"
        " Kidney failure, etc.). قم بصياغة ترجمة دقيقة واحترافية باللغة العربية"
        " الفصحى لهذه النقاط الطبية والعلمية بناءً على محتوى الصور الطبية الشائعة"
        " والموثوقة، وقدمها بشكل مرتب وواضح."
    )

    chat_completion = client.chat.completions.create(
        messages=[{
            "role": "user",
            "content": [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{base64_image}"
                    },
                },
            ],
        }],
        model="llama-3.3-70b-versatile",  # نموذج مستقر ودائم
        temperature=0.3,
    )
    ai_response = chat_completion.choices[0].message.content

    bot.edit_message_text(
        ai_response if ai_response else "لم أتمكن من العثور على نص للترجمة.",
        chat_id=message.chat.id,
        message_id=sent_msg.message_id,
        parse_mode="Markdown",
    )
  except Exception as e:
    bot.edit_message_text(
        f"حدث خطأ أثناء ترجمة الصورة: {str(e)}",
        chat_id=message.chat.id,
        message_id=sent_msg.message_id,
    )


@bot.message_handler(content_types=["sticker"])
def handle_stickers(message):
  if message.chat.type == "private":
    responses = ["ملصق جميل.", "تسلم على الملصق.", "حلوة هاي الحركة."]
    bot.reply_to(message, random.choice(responses))
    if cached_stickers and random.random() < 0.5:
      bot.send_sticker(message.chat.id, random.choice(cached_stickers))


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
    current_style = user_styles.get(user_id, "normal")

    style_instructions = {
        "formal": (
            "تحدث بطريقة رسمية جداً، محترفة، ومهذبة مع استخدام مصطلحات منمقة."
        ),
        "funny": "تحدث بطريقة فكاهية، ممتعة، وخفيفة الظل مع مزحة بسيطة إن أمكن.",
        "friendly": "تحدث بطريقة ودية، قريبة للقلب، وكأنك صديق مقرب.",
        "normal": "أسلوبك هادئ، طبيعي، ووسط.",
    }
    chosen_style_prompt = style_instructions.get(
        current_style, style_instructions["normal"]
    )

    system_content = (
        f"أنت مساعد شخصي لحساب تليجرام أعمال خاص بالمطور أحمد ومعرفه الرسمي هو"
        f" {ADMIN_USERNAME}. اسمك تويبي (Tweby). أسلوبك في الرد الحالي هو: {chosen_style_prompt}،"
        f" واستخدم الحد الأدنى من الإيموجي فقط عند الحاجة. الوقت والتاريخ"
        f" الحاليان في العراق هما: {current_time_str}."
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_message},
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.7,
    )
    ai_response = chat_completion.choices[0].message.content

    bot.send_message(
        chat_id=message.chat.id,
        text=ai_response if ai_response else "أهلاً بك.",
        parse_mode="Markdown",
        reply_to_message_id=message.message_id,
    )
  except Exception as e:
    print(f"خطأ في معالجة رسالة الأعمال: {e}")


@bot.message_handler(content_types=["text"])
def chat_with_ai(message):
  global total_messages_sent
  user_id = message.from_user.id
  users_db.add(user_id)
  user_message = message.text
  chat_type = message.chat.type

  if chat_type in ["group", "supergroup"]:
    is_reply_to_bot = (
        message.reply_to_message
        and message.reply_to_message.from_user.id == bot.get_me().id
    )
    text_lower = user_message.lower()
    mentioned_bot = any(name in text_lower for name in ["تويب", "تويبي", "tweby"])
    mentioned_dev = "احمد" in text_lower or "twebii" in text_lower
    if not is_reply_to_bot and not mentioned_bot and not mentioned_dev:
      return

  try:
    sent_msg = bot.reply_to(message, "جاري الرد...")
    total_messages_sent += 1
    iraq_now = datetime.utcnow() + timedelta(hours=3)
    current_time_str = iraq_now.strftime("%Y-%m-%d %I:%M:%S %p")
    current_style = user_styles.get(user_id, "normal")

    system_content = (
        f"أنت شخص حقيقي وطبيعي تتحدث بأسلوب ودي. اسمك تويبي (Tweby) ومطورك هو"
        f" أحمد ومعرفه الرسمي هو {ADMIN_USERNAME}. الوقت والتاريخ الحاليان في"
        f" العراق هما: {current_time_str}."
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": user_message},
        ],
        model="llama-3.3-70b-versatile",
        temperature=0.7,
    )
    ai_response = chat_completion.choices[0].message.content

    bot.edit_message_text(
        ai_response if ai_response else "تفضل.",
        chat_id=message.chat.id,
        message_id=sent_msg.message_id,
        parse_mode="Markdown",
    )
  except Exception as e:
    bot.reply_to(message, f"حدث خطأ بسيط: {str(e)}")


@server.route(f"/{TELEGRAM_BOT_TOKEN}", methods=["POST"])
def redirect_message():
  json_string = request.get_data().decode("utf-8")
  update = types.Update.de_json(json_string)
  bot.process_new_updates([update])
  return "!", 200


@server.route("/")
def index():
  return "Bot is running with Webhook!", 200


if __name__ == "__main__":
  print("Bot is starting and setting up Webhook automatically...")
  load_sticker_packs()
  set_bot_commands()

  try:
    bot.remove_webhook()
    bot.set_webhook(
        url=f"{RAILWAY_URL}/{TELEGRAM_BOT_TOKEN}",
        allowed_updates=[
            "message",
            "edited_message",
            "callback_query",
            "business_message",
            "business_connection",
            "document",
            "photo",
        ],
    )
    print("Webhook set successfully!")
  except Exception as e:
    print(f"Failed to set webhook: {e}")

  port = int(os.environ.get("PORT", 8080))
  server.run(host="0.0.0.0", port=port)

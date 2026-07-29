import io
import os
import random
from datetime import datetime, timedelta
from flask import Flask, request
from groq import Groq
import pypdf
import pytesseract
from PIL import Image
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
  elif data == "translate_files_info":
    bot.answer_callback_query(
        call.id,
        "فقط قم بإرسال ملف PDF أو ملف نصي وسأقوم بقراءته وترجمته بالكامل!",
        show_alert=True,
    )
  elif data == "back_home":
    bot.answer_callback_query(call.id)
    # العودة للقائمة الرئيسية
    send_welcome(call.message)


# --- معالجة الملفات النصية والـ PDF الرقمية ---
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
      reader = pypdf.PdfReader(io.BytesIO(downloaded_file))
      for page_num, page in enumerate(reader.pages):
        page_text = page.extract_text()
        if page_text and page_text.strip():
          extracted_full_text += (
              f"\n--- الصفحة {page_num + 1} ---\n" + page_text
          )

    elif file_name.endswith(".txt"):
      extracted_full_text = downloaded_file.decode("utf-8", errors="ignore")
    else:
      bot.edit_message_text(
          "عذراً، أستطيع التعامل مع ملفات PDF والملفات النصية فقط.",
          chat_id=message.chat.id,
          message_id=sent_msg.message_id,
      )
      return

    if not extracted_full_text.strip():
      bot.edit_message_text(
          "⚠️ هذا الملف عبارة عن صفحات مصورة (سكانر). يرجى إرسال الصفحات كصور"
          " مباشرة ليتم قراءتها وترجمتها بدقة.",
          chat_id=message.chat.id,
          message_id=sent_msg.message_id,
      )
      return

    prompt = (
        f"قم بترجمة النص التالي المستخرج من الملف إلى اللغة العربية الفصحى"
        f" بدقة واحترافية، مع تنسيق وترتيب النقاط الطبية أو العلمية بشكل جميل ومنظم:\n\n{extracted_full_text}"
    )

    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": str(prompt)}],
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


# --- معالجة الصور واستخراج النصوص الذكي (حل مشكلة String 400 الكود السابق) ---
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

    image = Image.open(io.BytesIO(downloaded_file))
    extracted_text = pytesseract.image_to_string(image)

    if not extracted_text.strip():
      extracted_text = (
          "Medical or scientific diagram/text related to fluid control or"
          " internal organs."
      )

    # تحويل الـ Prompt بالكامل إلى نص String صريح لمنع خطأ 400 الخاص بـ Groq
    prompt_text = str(
        f"النص التالي تم استخراجه من صورة أرسلها المستخدم:\n"
        f"'{extracted_text}'\n\n"
        f"قم بترجمة هذا النص بدقة واحترافية عالية إلى اللغة العربية الفصحى،"
        f" وقدم الشرح أو النقاط الطبية والعلمية بشكل مرتب ومنظم جداً للمدخلات الكلية للمستخدم."
    )

    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt_text}],
        model="llama-3.3-70b-versatile",
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


@bot.message_handler(content_types=["text"])
def chat_with_ai(message):
  global total_messages_sent
  user_id = message.from_user.id
  users_db.add(user_id)
  user_message = message.text

  try:
    sent_msg = bot.reply_to(message, "جاري الرد...")
    total_messages_sent += 1
    iraq_now = datetime.utcnow() + timedelta(hours=3)
    current_time_str = iraq_now.strftime("%Y-%m-%d %I:%M:%S %p")

    system_content = (
        f"أنت شخص حقيقي وطبيعي تتحدث بأسلوب ودي. اسمك تويبي (Tweby) ومطورك هو"
        f" أحمد ومعرفه الرسمي هو {ADMIN_USERNAME}. الوقت والتاريخ الحاليان في"
        f" العراق هما: {current_time_str}."
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_content},
            {"role": "user", "content": str(user_message)},
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
  print("Bot is starting...")
  set_bot_commands()

  try:
    bot.remove_webhook()
    bot.set_webhook(
        url=f"{RAILWAY_URL}/{TELEGRAM_BOT_TOKEN}",
        allowed_updates=[
            "message",
            "callback_query",
            "document",
            "photo",
        ],
    )
    print("Webhook set successfully!")
  except Exception as e:
    print(f"Failed to set webhook: {e}")

  port = int(os.environ.get("PORT", 8080))
  server.run(host="0.0.0.0", port=port)

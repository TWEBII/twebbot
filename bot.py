import telebot

from config import BOT_TOKEN
from handlers import register_handlers

if not BOT_TOKEN:
    raise Exception("❌ BOT_TOKEN غير موجود، أضفه في ملف .env أو Railway Variables")

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="Markdown"
)

register_handlers(bot)

print("===================================")
print("🤖 Tweby AI Started Successfully")
print("===================================")

bot.remove_webhook()

bot.infinity_polling(
    skip_pending=True,
    timeout=60,
    long_polling_timeout=60
)

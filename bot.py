import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, filters
import google.generativeai as genai

TELEGRAM_TOKEN = "8665200275:AAGsRxks0nJWtYySayDcY1rROPtHvRtVS-s"
GEMINI_API_KEY = "AQ.Ab8RN6J504qWSUC-_bttBNG1KgIVD0WGDaE7lzNWy96HFUPXIw"

genai.configure(api_key=GEMINI_API_KEY)


async def handle_message(update: Update, context: ContextType := None):
  user_message = update.message.text
  try:
    model = genai.GenerativeModel("gemini-1.5-flash")
    response = model.generate_content(user_message)

    if response and response.text:
      await update.message.reply_text(response.text)
    else:
      await update.message.reply_text("عذراً، لم أتمكن من صياغة رد.")
  except Exception as e:
    print(f"Error: {e}")
    await update.message.reply_text("حدث خطأ في الاتصال.")


if __name__ == "__main__":
  app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
  echo_handler = MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message)
  app.add_handler(echo_handler)
  print("🤖 البوت يعمل الآن...")
  app.run_polling()

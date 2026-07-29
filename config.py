import os
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env
load_dotenv()

# توكن البوت
BOT_TOKEN = os.getenv("BOT_TOKEN")

# مفتاح Groq
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# آيدي المطور
ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

# موديل الذكاء الاصطناعي
MODEL_NAME = "llama-3.3-70b-versatile"

# إعدادات الرد
TEMPERATURE = 0.7
MAX_HISTORY = 10

# حزم الملصقات (يمكنك تغييرها لاحقًا)
STICKER_PACKS = [
    "Funnyye_by_maker_Sticker_bot",
    "Life_by_maker_Sticker_bot"
]

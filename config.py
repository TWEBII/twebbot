import os
from dotenv import load_dotenv

# تحميل المتغيرات من ملف .env
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# تحويل الآيدي إلى رقم (Integer) حتى البوت يتعرف عليك فوراً
DEVELOPER_ID = int(os.getenv("DEVELOPER_ID", 0))

# اسم البوت الخاص بك
BOT_NAME = "TWEB"

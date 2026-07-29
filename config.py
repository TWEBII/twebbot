import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

# قراءة الآيدي بشكل آمن يمنع أي توقف حتى لو كان النص فارغاً
dev_id_raw = os.getenv("DEVELOPER_ID", "8411608232")
try:
    DEVELOPER_ID = int(dev_id_raw)
except ValueError:
    DEVELOPER_ID = 8411608232

BOT_NAME = "TWEB"

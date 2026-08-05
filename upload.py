import json
from pymongo import MongoClient

connection_string = (
    "mongodb+srv://twebmebot:Ahmed200331Radam@cluster0.fjpbzx2.mongodb.net/?"
    "retryWrites=true&w=majority&appName=Cluster0"
)

client = MongoClient(connection_string)

# تحديد قاعدة البيانات والـ Collection
db = client["tweb_database"]
collection = db["bot_data"]

# قراءة ملف database.json المحلي
with open("database.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# رفع البيانات إلى سحابة MongoDB
collection.replace_one({"_id": "main_data"}, data, upsert=True)

print("تم رفع البيانات بنجاح إلى MongoDB Atlas!")

import telebot
import config
import database
import handlers

# تهيئة البوت باستخدام التوكن من ملف الإعدادات
bot = telebot.TeleBot(config.BOT_TOKEN)

def main():
    print(f"جاري تشغيل بوت {config.BOT_NAME}...")
    
    # 1. تهيئة قاعدة البيانات (إنشاء الجداول إذا ما كانت موجودة)
    database.initialize_db()
    print("تم تهيئة قاعدة البيانات بنجاح ✅")
    
    # 2. تفعيل كل الأوامر والأزرار والذكاء الاصطناعي
    handlers.register_handlers(bot)
    print("تم ربط الأوامر والردود بنجاح ✅")
    
    print("البوت يعمل الآن! اذهب إلى التلغرام وأرسل /start")
    
    # 3. تشغيل البوت بشكل مستمر وبدون توقف
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"حدث خطأ أثناء التشغيل: {e}")

if __name__ == "__main__":
    main()

import telebot
import config
import database
import handlers

# تهيئة البوت باستخدام التوكن من ملف الإعدادات
bot = telebot.TeleBot(config.BOT_TOKEN)

def main():
    print(f"جاري تشغيل بوت {config.BOT_NAME}...")
    
    # 1. تهيئة قاعدة البيانات
    database.initialize_db()
    print("تم تهيئة قاعدة البيانات بنجاح ✅")
    
    # 2. تفعيل الأوامر
    handlers.register_handlers(bot)
    print("تم ربط الأوامر والردود بنجاح ✅")
    
    # 3. قطع أي اتصال أو ويبهوك قديم لمنع خطأ 409 نهائياً
    try:
        bot.remove_webhook()
        print("تم تنظيف الاتصالات القديمة بنجاح ✅")
    except Exception as e:
        print(f"ملاحظة تنظيف الاتصال: {e}")
    
    print("البوت يعمل الآن! اذهب إلى التلغرام وأرسل /start")
    
    # 4. تشغيل البوت بشكل آمن ومستمر
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5)
    except Exception as e:
        print(f"حدث خطأ أثناء التشغيل: {e}")

if __name__ == "__main__":
    main()

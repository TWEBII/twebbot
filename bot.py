import time
import telebot
import config
import database
import handlers

# تهيئة البوت باستخدام التوكن
bot = telebot.TeleBot(config.BOT_TOKEN)

def main():
    print(f"جاري تشغيل بوت {config.BOT_NAME}...")
    
    # 1. تهيئة قاعدة البيانات
    database.initialize_db()
    print("تم تهيئة قاعدة البيانات بنجاح ✅")
    
    # 2. تفعيل الأوامر
    handlers.register_handlers(bot)
    print("تم ربط الأوامر والردود بنجاح ✅")
    
    # 3. استراحة قصيرة لضمان إغلاق أي اتصال قديم بالكامل
    print("انتظار 3 ثوانٍ لتنظيف الاتصالات السابقة...")
    time.sleep(3)
    
    try:
        bot.remove_webhook()
        print("تم إزالة أي Webhook قديم بنجاح ✅")
    except Exception as e:
        print(f"ملاحظة: {e}")
        
    print("البوت يعمل الآن بشكل دائم وآمن!")
    
    # 4. تشغيل حلقة آمنة لا تتوقف أبداً حتى لو حدث خطأ مؤقت
    while True:
        try:
            bot.infinity_polling(timeout=20, long_polling_timeout=10, skip_pending=True)
        except Exception as e:
            print(f"حدث خطأ في الاتصال: {e}")
            print("إعادة محاولة التشغيل خلال 5 ثوانٍ...")
            time.sleep(5)

if __name__ == "__main__":
    main()

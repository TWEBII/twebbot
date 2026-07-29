import time
import telebot
import config
import database
import handlers

# تهيئة البوت باستخدام التوكن الجديد
bot = telebot.TeleBot(config.BOT_TOKEN)

def main():
    print(f"جاري تهيئة بوت {config.BOT_NAME}...")
    
    # 1. تهيئة قاعدة البيانات
    database.initialize_db()
    print("تم تهيئة قاعدة البيانات بنجاح ✅")
    
    # 2. تفعيل الأوامر
    handlers.register_handlers(bot)
    print("تم ربط الأوامر والردود بنجاح ✅")
    
    # 3. إيقاف مؤقت لمدة 10 ثوانٍ (الحل الحاسم لخطأ 409)
    print("انتظار 10 ثوانٍ لضمان إغلاق أي اتصال معلق من تيليجرام...")
    time.sleep(10)
    
    try:
        bot.remove_webhook()
        print("تم تنظيف الـ Webhook بنجاح ✅")
    except Exception as e:
        print(f"ملاحظة: {e}")
        
    print("البوت يعمل الآن بثبات تام!")
    
    # 4. تشغيل البوت مع تخطي الرسائل القديمة المعلقة
    while True:
        try:
            bot.infinity_polling(timeout=30, long_polling_timeout=20, skip_pending=True)
        except Exception as e:
            print(f"خطأ في الاتصال: {e}")
            print("إعادة المحاولة خلال 10 ثوانٍ...")
            time.sleep(10)

if __name__ == "__main__":
    main()

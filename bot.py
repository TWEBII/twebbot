import time
import os
import sys
import telebot
import config
import database
import handlers

# ملف قفل لمنع تشغيل نسختين في نفس الوقت
LOCK_FILE = "bot.lock"

def check_single_instance():
    if os.path.exists(LOCK_FILE):
        print("تحذير: نسخة أخرى تعمل مسبقاً، سيتم إيقاف هذه النسخة لمنع التعارض.")
        sys.exit(0)
    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

def remove_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)

# التأكد من عدم تكرار التشغيل
check_single_instance()

bot = telebot.TeleBot(config.BOT_TOKEN)

def main():
    try:
        print(f"جاري تشغيل بوت {config.BOT_NAME}...")
        
        database.initialize_db()
        print("تم تهيئة قاعدة البيانات بنجاح ✅")
        
        handlers.register_handlers(bot)
        print("تم ربط الأوامر والردود بنجاح ✅")
        
        time.sleep(3)
        
        try:
            bot.remove_webhook()
        except:
            pass
            
        print("البوت يعمل الآن بثبات تام وبدون تعارض!")
        bot.infinity_polling(timeout=30, long_polling_timeout=20, skip_pending=True)
        
    except Exception as e:
        print(f"حدث خطأ: {e}")
    finally:
        remove_lock()

if __name__ == "__main__":
    main()

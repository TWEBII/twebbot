import sqlite3
import time
import schedule
from datetime import datetime
import telebot

# استيراد كود البوت أو التوكن المشترك بدون فتح اتصال بولينج جديد
BOT_TOKEN = "8898698558:AAFjuVht_Qq1DD_-1nRIB1YT6U-VWPnwtFM"
bot = telebot.TeleBot(BOT_TOKEN)

DB_FILE = "users.db"

def init_adhkar_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (chat_id INTEGER PRIMARY KEY)''')
    conn.commit()
    conn.close()

# توليد 500 ذكر من حصن المسلم والسنة
def generate_500_adhkar():
    base_adhkar = [
        "«لَا إِلَهَ إِلَّا اللَّهَ وَحْدَهُ لَا شَرِيكَ لَهُ، لَهُ الْمُلْكُ وَلَهُ الْحَمْدُ، وَهُوَ عَلَى كُلِّ شَيْءٍ قَدِيرٌ»",
        "«سُبْحَانَ اللَّهِ وَبِحَمْدِهِ، سُبْحَانَ اللَّهِ الْعَظِيمِ»",
        "«لَا حَوْلَ وَلَا قُوَّةَ إِلَّا بِاللَّهِ الْعَلِيِّ الْعَظِيمِ»",
        "«سُبْحَانَ اللَّهِ، وَالْحَمْدُ لِلَّهِ، وَلَا إِلَهَ إِلَّا اللَّهُ، وَاللَّهُ أَكْبَرُ»",
        "«أستغفر الله العظيم الذي لا إله إلا هو الحي القيوم وأتوب إليه»",
        "«اللَّهُمَّ صَلِّ وَسَلِّمْ عَلَى نَبِيِّنَا مُحَمَّدٍ»",
        "«رَبِّ اغْفِرْ لِي وَتُبْ عَلَيَّ إِنَّكَ أَنْتَ التَّوَّابُ الرَّحِيمُ»",
        "«لا إله إلا أنت سبحانك إني كنت من الظالمين»",
        "«اللَّهُمَّ إِنِّي أَسْأَلُكَ الْعَفْوَ وَالْعَافِيَةَ فِي الدُّنْيَا وَالْآخِرَةِ»",
        "«حسبنا الله ونعم الوكيل»"
    ]
    full_list = []
    categories = [
        "أذكار التوحيد والتعظيم", "التسبيح والتحميد والتهليل", 
        "الاستغفار والتوبة", "الصلاة على النبي ﷺ", 
        "أدعية الكرب والفرج", "أذكار الصباح والمساء المختارة", 
        "الحوقلة والكنوز الباقيات الصالحات"
    ]
    for i in range(1, 501):
        cat = categories[i % len(categories)]
        core_dhkr = base_adhkar[i % len(base_adhkar)]
        text = f"📖 **ذكر من حصن المسلم والسنة (الرقم {i}/500):**\n\n📌 *التصنيف: {cat}*\n\n{core_dhkr}\n\n💡 *داوم عليها لتنال بها الأجر العظيم والطمأنينة.*"
        full_list.append(text)
    return full_list

ADHKAR_LIST = generate_500_adhkar()
current_index = 0

FRIDAY_MESSAGES = [
    "🌿 **نفحات الجمعة المباركة:**\n\n«إن من أفضل أيامكم يوم الجمعة، فأكثروا عليّ من الصلاة فيه فإن صلاتكم معروضة عليّ»\n\nاللهم صلّ وسلّم على نبينا محمد وعلى آله وصحبه أجمعين 🤍",
    "🕊️ **ذكر ليلة/يوم الجمعة:**\n\n«من صلّى عليّ صلاة صلى الله عليه بها عشراً»\n\nعطروا ألسنتكم بالصلاة على الحبيب المصطفى ﷺ في هذا اليوم المبارك.",
    "✨ **فضائل يوم الجمعة:**\n\nأكثروا من الصلاة على النبي ﷺ، وقراءة سورة الكهف، وتحري ساعة الاستجابة قبيل غروب الشمس."
]
friday_index = 0

SPECIAL_OCCASIONS = {
    "01-10": "🌙 **تنبيه مبارك:** مبارك عليكم حلول شهر رمضان المبارك، تقبل الله منا ومنكم صالح الأعمال.",
    "09-12": "🕋 **يوم عرفة المبارك:** احتسبوا على الله أن يكفر سنة ماضية وسنة باقية، وأكثروا من الدعاء والاستغفار.",
    "10-12": "🎉 **عيد الأضحى المبارك:** تقبل الله طاعاتكم وأيامكم مباركة، كل عام وأنتم بخير.",
    "10-01": "🌙 **يوم عاشوراء:** صيام هذا اليوم يكفر السنة الماضية، لا تنسوا صيامه واحتساب الأجر."
}

def get_today_dhkar():
    global current_index, friday_index
    now = datetime.now()
    
    date_key = now.strftime("%m-%d")
    if date_key in SPECIAL_OCCASIONS:
        return f"🌟 **مناسبة مباركة اليوم:**\n\n{SPECIAL_OCCASIONS[date_key]}"

    if now.weekday() == 4:
        msg = FRIDAY_MESSAGES[friday_index]
        friday_index = (friday_index + 1) % len(FRIDAY_MESSAGES)
        return msg

    text = ADHKAR_LIST[current_index]
    current_index = (current_index + 1) % len(ADHKAR_LIST)
    return text

def send_daily_adhkar():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute("SELECT chat_id FROM users")
    users = cursor.fetchall()
    conn.close()

    if not users:
        return

    text = get_today_dhkar()

    for user in users:
        chat_id = user[0]
        try:
            bot.send_message(chat_id, text, parse_mode="Markdown")
            time.sleep(0.3)
        except Exception as e:
            print(f"Failed to send to {chat_id}: {e}")

def run_scheduler():
    init_adhkar_db()
    # جدولة الإرسال اليومي الساعة 9 صباحاً
    schedule.every().day.at("09:00").do(send_daily_adhkar)
    while True:
        schedule.run_pending()
        time.sleep(60)

import sqlite3

DB_NAME = "tweb_database.db"

def initialize_db():
    """إنشاء الجداول الافتراضية إذا ما كانت موجودة"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # جدول لحفظ الأيدي مال المستخدمين (للإحصائيات والإذاعة)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY
        )
    ''')
    
    # جدول لحفظ الإعدادات مثل رسالة الترحيب start
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # نخلي رسالة ترحيب افتراضية أول ما يشتغل البوت
    cursor.execute("INSERT OR IGNORE INTO settings (key, value) VALUES ('start_message', 'أهلاً بك في بوت TWEB للذكاء الاصطناعي! كيف يمكنني مساعدتك اليوم؟')")
    
    conn.commit()
    conn.close()

def add_user(user_id):
    """إضافة مستخدم جديد لقاعدة البيانات"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR IGNORE INTO users (user_id) VALUES (?)", (user_id,))
    conn.commit()
    conn.close()

def get_users_count():
    """حساب عدد المشتركين بالبوت (للإحصائيات)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users")
    count = cursor.fetchone()[0]
    conn.close()
    return count

def get_all_users():
    """جلب كل أيدي المستخدمين (للإذاعة)"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT user_id FROM users")
    users = [row[0] for row in cursor.fetchall()]
    conn.close()
    return users

def get_start_message():
    """جلب رسالة الترحيب الحالية"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = 'start_message'")
    row = cursor.fetchone()
    conn.close()
    if row:
        return row[0]
    return "أهلاً بك في بوت TWEB!"

def set_start_message(text):
    """تحديث رسالة الترحيب من لوحة التحكم"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('start_message', ?)", (text,))
    conn.commit()
    conn.close()

from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def developer_panel_markup():
    """توليد لوحة التحكم الخاصة بالمطور (أحمد)"""
    # نحدد أن الأزرار تترتب عمودياً (زر واحد في كل صف)
    markup = InlineKeyboardMarkup(row_width=1)
    
    # إنشاء الأزرار
    btn_stats = InlineKeyboardButton("📊 الإحصائيات", callback_data="panel_stats")
    btn_broadcast = InlineKeyboardButton("📢 إذاعة", callback_data="panel_broadcast")
    btn_start = InlineKeyboardButton("📝 تعديل رسالة start", callback_data="panel_edit_start")
    
    # إضافة الأزرار للوحة
    markup.add(btn_stats, btn_broadcast, btn_start)
    
    return markup

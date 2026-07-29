from telebot.types import ReplyKeyboardMarkup, KeyboardButton


def main_menu(is_admin=False):
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.row(
        KeyboardButton("🤖 الدردشة الذكية")
    )

    kb.row(
        KeyboardButton("⚙️ الإعدادات"),
        KeyboardButton("📜 سجل المحادثات")
    )

    kb.row(
        KeyboardButton("ℹ️ المساعدة"),
        KeyboardButton("👨‍💻 المطور")
    )

    if is_admin:
        kb.row(
            KeyboardButton("👑 لوحة التحكم")
        )

    return kb


def admin_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)

    kb.row(
        KeyboardButton("📢 إذاعة")
    )

    kb.row(
        KeyboardButton("📝 تغيير رسالة Start")
    )

    kb.row(
        KeyboardButton("📊 الإحصائيات"),
        KeyboardButton("👥 المستخدمون")
    )

    kb.row(
        KeyboardButton("🚫 حظر مستخدم"),
        KeyboardButton("✅ إلغاء الحظر")
    )

    kb.row(
        KeyboardButton("📨 إرسال رسالة")
    )

    kb.row(
        KeyboardButton("⬅️ رجوع")
    )

    return kb

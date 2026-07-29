import config
import database
import ai
import keyboards

def register_handlers(bot):
    
    # 1. التعامل مع أمر /start
    @bot.message_handler(commands=['start'])
    def handle_start(message):
        user_id = message.from_user.id
        # نحفظ المستخدم بقاعدة البيانات
        database.add_user(user_id) 
        
        # إذا كان المستخدم هو أنت (المطور)
        if user_id == config.DEVELOPER_ID:
            bot.reply_to(
                message,
                f"أهلاً بك يا مطوري 🫡\nأنا بوت {config.BOT_NAME} تحت خدمتك.\nهذه لوحة التحكم الخاصة بك:",
                reply_markup=keyboards.developer_panel_markup()
            )
        else:
            # إذا كان مستخدم عادي نجيب رسالة الترحيب من القاعدة
            start_msg = database.get_start_message()
            bot.reply_to(message, start_msg)

    # 2. التعامل مع أزرار لوحة التحكم
    @bot.callback_query_handler(func=lambda call: call.data.startswith('panel_'))
    def handle_developer_panel(call):
        # التأكد من أن اللي ضغط الزر هو المطور
        if call.from_user.id != config.DEVELOPER_ID:
            bot.answer_callback_query(call.id, "هذه الأزرار للمطور فقط ⛔", show_alert=True)
            return

        # إذا ضغط على زر الإحصائيات
        if call.data == "panel_stats":
            count = database.get_users_count()
            bot.answer_callback_query(call.id, f"📊 عدد المستخدمين الكلي: {count}", show_alert=True)
            
        # إذا ضغط على زر الإذاعة
        elif call.data == "panel_broadcast":
            msg = bot.send_message(call.message.chat.id, "📢 أرسل الرسالة التي تريد إذاعتها لجميع المستخدمين الآن:")
            # ننتظر الرسالة الجاية من المطور ونوديها لدالة الإذاعة
            bot.register_next_step_handler(msg, process_broadcast)
            
        # إذا ضغط على زر تغيير رسالة الترحيب
        elif call.data == "panel_edit_start":
            msg = bot.send_message(call.message.chat.id, "📝 أرسل رسالة الترحيب (Start) الجديدة:")
            # ننتظر الرسالة الجاية من المطور ونوديها لدالة التعديل
            bot.register_next_step_handler(msg, process_edit_start)

    # دالة تنفيذ الإذاعة
    def process_broadcast(message):
        text = message.text
        if not text:
            bot.reply_to(message, "الرجاء إرسال نص للإذاعة. تم الإلغاء.")
            return
            
        users = database.get_all_users()
        success = 0
        bot.send_message(message.chat.id, "جاري الإذاعة... ⏳")
        for user in users:
            try:
                bot.send_message(user, text)
                success += 1
            except:
                pass # نتجاهل المستخدم إذا كان حاظر البوت
        
        bot.reply_to(message, f"تمت الإذاعة بنجاح لـ {success} مستخدمين. ✅")

    # دالة تنفيذ تغيير رسالة الترحيب
    def process_edit_start(message):
        text = message.text
        if not text:
            bot.reply_to(message, "الرجاء إرسال نص. تم الإلغاء.")
            return
            
        database.set_start_message(text)
        bot.reply_to(message, "تم تحديث رسالة الـ start بنجاح. ✅")

    # 3. التعامل مع باقي الرسائل (الذكاء الاصطناعي)
    @bot.message_handler(func=lambda message: True)
    def handle_ai_chat(message):
        # نرسل حالة "يكتب..." للمستخدم
        bot.send_chat_action(message.chat.id, 'typing')
        
        # نجيب الجواب الدقيق والمؤكد من ملف ai.py
        reply_text = ai.generate_ai_response(message.text)
        
        # نرسل الجواب
        bot.reply_to(message, reply_text)

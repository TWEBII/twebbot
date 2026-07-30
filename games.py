from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup_game_handlers(bot):
    
    # دالة عرض الأزرار الرئيسية للألعاب (جنباً إلى جنب)
    def get_games_keyboard():
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("لعبة XO ❌⭕️", callback_data="game_xo_main"),
            InlineKeyboardButton("حجر ورقة مقص ✂️", callback_data="game_rps_main")
        )
        markup.row(InlineKeyboardButton("« رجوع للقائمة الرئيسية", callback_data="user_back_home"))
        return markup

    # فتح قسم الألعاب والترفيه
    @bot.callback_query_handler(func=lambda call: call.data == "user_menu_games")
    def games_menu_callback(call):
        bot.answer_callback_query(call.id)  # إيقاف الدوران فوراً
        text = (
            "🎮 **قسم الألعاب والترفيه**\n\n"
            "اختر إحدى الألعاب أدناه للبدء باللعب والاستمتاع:"
        )
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=get_games_keyboard(),
                parse_mode="Markdown"
            )
        except Exception:
            bot.send_message(
                chat_id=call.message.chat.id,
                text=text,
                reply_markup=get_games_keyboard(),
                parse_mode="Markdown"
            )

    # واجهة لعبة XO مع زر التحدي والمشاركة
    @bot.callback_query_handler(func=lambda call: call.data == "game_xo_main")
    def start_xo_game(call):
        bot.answer_callback_query(call.id)
        
        xo_markup = InlineKeyboardMarkup()
        xo_markup.row(InlineKeyboardButton("💜 تحدي اللعبة", switch_inline_query="XO_Challenge"))
        xo_markup.row(InlineKeyboardButton("« رجوع للألعاب", callback_data="user_menu_games"))
        
        text = "🎮 **أهلاً بك في قسم لعبة XO 🕹️**\n\nانقر على زر التحدي أدناه لمشاركة اللعبة مع أصدقائك في أي محادثة:"
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=xo_markup,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"XO Error: {e}")

    # واجهة لعبة حجر ورقة مقص
    @bot.callback_query_handler(func=lambda call: call.data == "game_rps_main")
    def start_rps_game(call):
        bot.answer_callback_query(call.id)
        
        rps_markup = InlineKeyboardMarkup()
        rps_markup.row(
            InlineKeyboardButton("🪨 حجر", callback_data="rps_rock"),
            InlineKeyboardButton("📄 ورقة", callback_data="rps_paper"),
            InlineKeyboardButton("✂️ مقص", callback_data="rps_scissors")
        )
        rps_markup.row(InlineKeyboardButton("« رجوع للألعاب", callback_data="user_menu_games"))
        
        text = "✂️ **لعبة حجر ورقة مقص**\n\nاختر ما تنافس به:"
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=rps_markup,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"RPS Error: {e}")

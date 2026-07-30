from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def setup_game_handlers(bot):
    
    # دالة عرض الأزرار (زرين الألعاب بجانب بعضهما)
    def get_games_keyboard():
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("لعبة XO ❌⭕️", callback_data="game_xo"),
            InlineKeyboardButton("حجر ورقة مقص ✂️", callback_data="game_rps")
        )
        markup.row(InlineKeyboardButton("« رجوع للقائمة الرئيسية", callback_data="user_back_home"))
        return markup

    # فتح قسم الألعاب
    @bot.callback_query_handler(func=lambda call: call.data == "user_menu_games")
    def games_menu_callback(call):
        bot.answer_callback_query(call.id)  # ضروري جداً لإيقاف الدوران
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

    # لعبة XO
    @bot.callback_query_handler(func=lambda call: call.data == "game_xo")
    def start_xo_game(call):
        bot.answer_callback_query(call.id, "تم فتح لعبة XO بنجاح! ❌")
        
        markup = InlineKeyboardMarkup()
        # هنا يمكنك ترتيب أزرار لوحة XO (3x3) أو أزرار التحكم
        markup.row(
            InlineKeyboardButton("⬜", callback_data="xo_0"),
            InlineKeyboardButton("⬜", callback_data="xo_1"),
            InlineKeyboardButton("⬜", callback_data="xo_2")
        )
        markup.row(
            InlineKeyboardButton("⬜", callback_data="xo_3"),
            InlineKeyboardButton("⬜", callback_data="xo_4"),
            InlineKeyboardButton("⬜", callback_data="xo_5")
        )
        markup.row(
            InlineKeyboardButton("⬜", callback_data="xo_6"),
            InlineKeyboardButton("⬜", callback_data="xo_7"),
            InlineKeyboardButton("⬜", callback_data="xo_8")
        )
        markup.row(InlineKeyboardButton("« رجوع للألعاب", callback_data="user_menu_games"))
        
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="❌ **لعبة XO**\n\nدور اللاعب الأول:",
                reply_markup=markup,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"XO Error: {e}")

    # لعبة حجر ورقة مقص
    @bot.callback_query_handler(func=lambda call: call.data == "game_rps")
    def start_rps_game(call):
        bot.answer_callback_query(call.id, "تم فتح لعبة حجر ورقة مقص! ✂️")
        
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("🪨 حجر", callback_data="rps_rock"),
            InlineKeyboardButton("📄 ورقة", callback_data="rps_paper"),
            InlineKeyboardButton("✂️ مقص", callback_data="rps_scissors")
        )
        markup.row(InlineKeyboardButton("« رجوع للألعاب", callback_data="user_menu_games"))
        
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text="✂️ **لعبة حجر ورقة مقص**\n\nاختر ما ينافس به:",
                reply_markup=markup,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"RPS Error: {e}")

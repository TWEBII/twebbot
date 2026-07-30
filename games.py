import random
from telebot.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    InlineQueryResultArticle, 
    InputTextMessageContent
)

def setup_game_handlers(bot):
    
    # القائمة الرئيسية للألعاب (جنب إلى جنب)
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
        bot.answer_callback_query(call.id)
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

    # واجهة لعبة XO
    @bot.callback_query_handler(func=lambda call: call.data == "game_xo_main")
    def start_xo_game(call):
        bot.answer_callback_query(call.id)
        
        xo_markup = InlineKeyboardMarkup()
        xo_markup.row(InlineKeyboardButton("💜 تحدي اللعبة", switch_inline_query="XO_Challenge"))
        xo_markup.row(InlineKeyboardButton("« رجوع للألعاب", callback_data="user_menu_games"))
        
        text = "🎮 **لعبة XO ❌⭕️**\n\nانقر على زر التحدي أدناه لمشاركة اللعبة مع أصدقائك في أي محادثة:"
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
        rps_markup.row(InlineKeyboardButton("💜 تحدي اللعبة", switch_inline_query="RPS_Challenge"))
        rps_markup.row(
            InlineKeyboardButton("🪨 حجر", callback_data="rps_rock"),
            InlineKeyboardButton("📄 ورقة", callback_data="rps_paper"),
            InlineKeyboardButton("✂️ مقص", callback_data="rps_scissors")
        )
        rps_markup.row(InlineKeyboardButton("« رجوع للألعاب", callback_data="user_menu_games"))
        
        text = "✂️ **لعبة حجر ورقة مقص**\n\nاختر تحدي أصدقائك أو نافس البوت مباشرة:"
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

    # معالجة اللعب ضد البوت
    @bot.callback_query_handler(func=lambda call: call.data in ["rps_rock", "rps_paper", "rps_scissors"])
    def play_rps_game(call):
        user_choice = call.data
        choices = {
            "rps_rock": ("حجر", "🪨"),
            "rps_paper": ("ورقة", "📄"),
            "rps_scissors": ("مقص", "✂️")
        }
        
        user_name, user_emoji = choices[user_choice]
        bot_key = random.choice(list(choices.keys()))
        bot_name, bot_emoji = choices[bot_key]
        
        if user_choice == bot_key:
            result_text = "🤝 **تعادل! نفس الاختيار تماماً.**"
        elif (
            (user_choice == "rps_rock" and bot_key == "rps_scissors") or
            (user_choice == "rps_paper" and bot_key == "rps_rock") or
            (user_choice == "rps_scissors" and bot_key == "rps_paper")
        ):
            result_text = "🎉 **تهانينا، لقد فزت على البوت!**"
        else:
            result_text = "😢 **حظاً أوفر، لقد فاز البوت عليك!**"
            
        text = (
            f"✂️ **نتائج لعبة حجر ورقة مقص**\n\n"
            f"👤 اختيارك: {user_emoji} {user_name}\n"
            f"🤖 اختيار البوت: {bot_emoji} {bot_name}\n\n"
            f"{result_text}"
        )
        
        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("💜 تحدي اللعبة", switch_inline_query="RPS_Challenge"))
        markup.row(InlineKeyboardButton("🔄 تلعب مرة أخرى", callback_data="game_rps_main"))
        markup.row(InlineKeyboardButton("« رجوع للألعاب", callback_data="user_menu_games"))
        
        bot.answer_callback_query(call.id, f"اخترت {user_name}!")
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=markup,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"RPS Play Error: {e}")

    # معالج استعلامات الـ Inline لإرسال الألعاب
    @bot.inline_handler(func=lambda query: True)
    def send_inline_games(inline_query):
        query_text = inline_query.query
        results = []
        
        if "XO" in query_text:
            xo_board = InlineKeyboardMarkup()
            xo_board.row(
                InlineKeyboardButton("⬜", callback_data="xo_0"),
                InlineKeyboardButton("⬜", callback_data="xo_1"),
                InlineKeyboardButton("⬜", callback_data="xo_2")
            )
            xo_board.row(
                InlineKeyboardButton("⬜", callback_data="xo_3"),
                InlineKeyboardButton("⬜", callback_data="xo_4"),
                InlineKeyboardButton("⬜", callback_data="xo_5")
            )
            xo_board.row(
                InlineKeyboardButton("⬜", callback_data="xo_6"),
                InlineKeyboardButton("⬜", callback_data="xo_7"),
                InlineKeyboardButton("⬜", callback_data="xo_8")
            )
            
            results.append(
                InlineQueryResultArticle(
                    id='xo_game_res',
                    title='🎮 إرسال تحدي لعبة XO',
                    description='انقر لإرسال لوحة XO إلى أي دردشة ومبدأ التحدي!',
                    input_message_content=InputTextMessageContent(
                        message_text="🎮 **بدأت لعبة XO التحدي!**\n\nاختر خانتك للبدء:",
                        parse_mode='Markdown'
                    ),
                    reply_markup=xo_board
                )
            )
            
        elif "RPS" in query_text:
            rps_board = InlineKeyboardMarkup()
            rps_board.row(
                InlineKeyboardButton("🪨 حجر", callback_data="rps_inline_rock"),
                InlineKeyboardButton("📄 ورقة", callback_data="rps_inline_paper"),
                InlineKeyboardButton("✂️ مقص", callback_data="rps_inline_scissors")
            )
            
            results.append(
                InlineQueryResultArticle(
                    id='rps_game_res',
                    title='✂️ إرسال تحدي حجر ورقة مقص',
                    description='انقر لإرسال لعبة حجر ورقة مقص إلى أي دردشة!',
                    input_message_content=InputTextMessageContent(
                        message_text="✂️ **تحدي حجر ورقة مقص جديد!**\n\nاختر ما تنافس به:",
                        parse_mode='Markdown'
                    ),
                    reply_markup=rps_board
                )
            )
            
        try:
            bot.answer_inline_query(inline_query.id, results, cache_time=1)
        except Exception as e:
            print(f"Inline Error: {e}")

    # معالجة ضغطات الأزرار داخل رسائل الانلاين (لإيقاف الدوران والتفاعل)
    @bot.callback_query_handler(func=lambda call: call.data and (call.data.startswith("xo_") or call.data.startswith("rps_inline_")))
    def handle_inline_game_clicks(call):
        data = call.data
        
        # إيقاف الدوران فوراً وإرسال تنبيه للمستخدم الضاغط
        bot.answer_callback_query(call.id, "تم تسجيل اختيارك بنجاح! ✅")
        
        try:
            if data.startswith("xo_"):
                bot.edit_message_text(
                    inline_message_id=call.inline_message_id,
                    text="🎮 **لعبة XO جارية...**\nتم النقر على الخانة بنجاح.",
                    parse_mode="Markdown"
                )
            elif data.startswith("rps_inline_"):
                choice_name = "حجر 🪨" if "rock" in data else ("ورقة 📄" if "paper" in data else "مقص ✂️")
                bot.edit_message_text(
                    inline_message_id=call.inline_message_id,
                    text=f"✂️ **تم اختيار ({choice_name}) في التحدي!**",
                    parse_mode="Markdown"
                )
        except Exception as e:
            print(f"Inline Click Handling Error: {e}")

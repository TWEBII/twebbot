import random
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

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

    # واجهة لعبة XO مع زر التحدي والمشاركة
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

    # واجهة لعبة حجر ورقة مقص (مع زر التحدي وأزرار اللعب ضد البوت)
    @bot.callback_query_handler(func=lambda call: call.data == "game_rps_main")
    def start_rps_game(call):
        bot.answer_callback_query(call.id)
        
        rps_markup = InlineKeyboardMarkup()
        # زر تحدي صديق عبر الانلاين
        rps_markup.row(InlineKeyboardButton("💜 تحدي اللعبة", switch_inline_query="RPS_Challenge"))
        # أزرار اللعب السريع ضد البوت
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

    # معالجة نتيجة لعبة حجر ورقة مقص ضد البوت
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

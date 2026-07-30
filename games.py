import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
import random

def setup_game_handlers(bot):
    
    # عرض الزرين الرئيسيين (XO وحجرة ورقة مقص) عند الدخول لقسم الألعاب
    @bot.callback_query_handler(func=lambda call: call.data == "user_menu_games")
    def user_menu_games_handler(call):
        bot.answer_callback_query(call.id)
        games_markup = InlineKeyboardMarkup()
        # الزران الشفافان الرئيسيان في نفس الصف أو تحت بعض حسب رغبتك (هنا بجانب بعض)
        games_markup.row(
            InlineKeyboardButton("🎮 لعبة XO", callback_data="game_xo_main"),
            InlineKeyboardButton("✂️ حجرة ورقة مقص", callback_data="game_rps_main")
        )
        games_markup.row(InlineKeyboardButton("« رجوع للقائمة الرئيسية", callback_data="user_back_home"))
        edit_game_interface(bot, call, "🎮 **قسم الألعاب والترفيه**\n\nاختر اللعبة التي تود لعبها من الأزرار أدناه:", games_markup)

    # معالجة النقر على أزرار اللعبتين الرئيسية لعرض خيارات التحدي
    @bot.callback_query_handler(func=lambda call: call.data in ["game_xo_main", "game_rps_main"])
    def games_menu_handler(call):
        if call.data == "game_xo_main":
            bot.answer_callback_query(call.id)
            xo_markup = InlineKeyboardMarkup()
            xo_markup.row(InlineKeyboardButton("💜 تحدي اللعبة", switch_inline_query="XO_Challenge"))
            xo_markup.row(InlineKeyboardButton("« رجوع للألعاب", callback_data="user_menu_games"))
            edit_game_interface(bot, call, "🎮 **أهلاً بك في قسم لعبة XO 🕹️**\n\nانقر على زر التحدي أدناه لمشاركة اللعبة مع أصدقائك في أي محادثة:", xo_markup)
            
        elif call.data == "game_rps_main":
            bot.answer_callback_query(call.id)
            rps_markup = InlineKeyboardMarkup()
            rps_markup.row(InlineKeyboardButton("💜 تحدي اللعبة", switch_inline_query="Rps_Challenge"))
            rps_markup.row(InlineKeyboardButton("« رجوع للألعاب", callback_data="user_menu_games"))
            edit_game_interface(bot, call, "✂️ **أهلاً بك في قسم لعبة حجرة ورقة مقص 🗿**\n\nانقر على زر التحدي أدناه لمشاركة اللعبة مع أصدقائك في أي محادثة:", rps_markup)

    # منطق لعبة حجرة ورقة مقص ضد البوت
    @bot.callback_query_handler(func=lambda call: call.data in ["rps_rock", "rps_paper", "rps_scissors"])
    def rps_game_logic(call):
        choices = {
            "rps_rock": ("🪨 الحجرة", "rock"), 
            "rps_paper": ("📄 الورقة", "paper"), 
            "rps_scissors": ("✂️ المقص", "scissors")
        }
        user_choice_text, user_key_choice = choices[call.data]
        
        bot_choice_key = random.choice(["rock", "paper", "scissors"])
        bot_choices_map = {"rock": "🪨 الحجرة", "paper": "📄 الورقة", "scissors": "✂️ المقص"}
        bot_choice_text = bot_choices_map[bot_choice_key]
        
        if user_key_choice == bot_choice_key:
            result_msg = "🤝 تعادل!"
        elif (user_key_choice == "rock" and bot_choice_key == "scissors") or \
             (user_key_choice == "paper" and bot_choice_key == "rock") or \
             (user_key_choice == "scissors" and bot_choice_key == "paper"):
            result_msg = "🎉 مبروك، لقد فزت!"
        else:
            result_msg = "😢 لقد خسرت، حظاً أوفر في المرة القادمة!"
            
        final_text = (
            f"✂️ **نتيجة لعبة حجرة ورقة مقص**\n\n"
            f"👤 اختيارك: {user_choice_text}\n"
            f"🤖 اختيار البوت: {bot_choice_text}\n\n"
            f"**النتيجة:** {result_msg}"
        )
        try:
            bot.answer_callback_query(call.id, result_msg)
            bot.edit_message_text(text=final_text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=None, parse_mode="Markdown")
        except Exception as e:
            pass

def edit_game_interface(bot, call, text, markup):
    try:
        if call.message.photo or call.message.video:
            bot.edit_message_caption(caption=text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")
        else:
            bot.edit_message_text(text=text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup, parse_mode="Markdown")
    except Exception as e:
        try:
            if call.message.photo or call.message.video:
                bot.edit_message_caption(caption=text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
            else:
                bot.edit_message_text(text=text, chat_id=call.message.chat.id, message_id=call.message.message_id, reply_markup=markup)
        except Exception as ex:
            print(f"Game Interface Edit Error: {ex}")

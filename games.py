import random
from telebot.types import (
    InlineKeyboardMarkup, 
    InlineKeyboardButton, 
    InlineQueryResultArticle, 
    InputTextMessageContent
)

# ذاكرة مؤقتة لتخزين حالات ألعاب XO النشطة
ACTIVE_XO_GAMES = {}

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

    # واجهة لعبة حجر ورقة مقص (الخطوة 1: اختيار اللاعب الأول لحركته)
    @bot.callback_query_handler(func=lambda call: call.data == "game_rps_main")
    def start_rps_game(call):
        bot.answer_callback_query(call.id)
        
        rps_markup = InlineKeyboardMarkup()
        rps_markup.row(
            InlineKeyboardButton("🪨 حجر", callback_data="rps_p1_rock"),
            InlineKeyboardButton("📄 ورقة", callback_data="rps_p1_paper"),
            InlineKeyboardButton("✂️ مقص", callback_data="rps_p1_scissors")
        )
        rps_markup.row(InlineKeyboardButton("« رجوع للألعاب", callback_data="user_menu_games"))
        
        text = (
            "✂️ **لعبة حجر ورقة مقص**\n\n"
            "الخطوة الأولى: اختر حركتك أولاً من الأزرار أدناه قبل إرسال التحدي:"
        )
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

    # معالجة اختيار اللاعب الأول لحركته في حجر ورقة مقص
    @bot.callback_query_handler(func=lambda call: call.data in ["rps_p1_rock", "rps_p1_paper", "rps_p1_scissors"])
    def rps_p1_chosen(call):
        choice_map = {
            "rps_p1_rock": ("حجر", "🪨", "rock"),
            "rps_p1_paper": ("ورقة", "📄", "paper"),
            "rps_p1_scissors": ("مقص", "✂️", "scissors")
        }
        name, emoji, key = choice_map[call.data]
        bot.answer_callback_query(call.id, f"تم اختيار ({name}) بنجاح! ✅")
        
        share_markup = InlineKeyboardMarkup()
        share_markup.row(InlineKeyboardButton("🚀 إرسال التحدي إلى صديق", switch_inline_query=f"RPS_PLAY_{key}"))
        share_markup.row(InlineKeyboardButton("🔄 تغيير الحركة", callback_data="game_rps_main"))
        share_markup.row(InlineKeyboardButton("« رجوع للألعاب", callback_data="user_menu_games"))
        
        text = (
            f"✂️ **لعبة حجر ورقة مقص**\n\n"
            f"لقد اخترت: {emoji} **{name}**\n\n"
            f"الآن انقر على الزر أدناه لمشاركة التحدي وإرساله إلى صديقك في أي دردشة:"
        )
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=share_markup,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"RPS P1 Choice Error: {e}")

    # معالج استعلامات الـ Inline لإرسال الألعاب
    @bot.inline_handler(func=lambda query: True)
    def send_inline_games(inline_query):
        query_text = inline_query.query
        results = []
        user_id = inline_query.from_user.id
        
        if "XO" in query_text:
            initial_board = ["⬜"] * 9
            xo_board = InlineKeyboardMarkup()
            for i in range(0, 9, 3):
                xo_board.row(
                    InlineKeyboardButton(initial_board[i], callback_data=f"xo_{i}"),
                    InlineKeyboardButton(initial_board[i+1], callback_data=f"xo_{i+1}"),
                    InlineKeyboardButton(initial_board[i+2], callback_data=f"xo_{i+2}")
                )
            
            results.append(
                InlineQueryResultArticle(
                    id='xo_game_res',
                    title='🎮 إرسال تحدي لعبة XO',
                    description='انقر لإرسال لوحة XO للعب والتنافس مع صديق!',
                    input_message_content=InputTextMessageContent(
                        message_text="🎮 **بدأت تحدي لعبة XO!**\nدور اللاعب الأول (❌)\nانقر على أي مربع للبدء:",
                        parse_mode='Markdown'
                    ),
                    reply_markup=xo_board
                )
            )
            
        elif "RPS_PLAY_" in query_text:
            p1_choice = query_text.replace("RPS_PLAY_", "").strip()
            if p1_choice not in ["rock", "paper", "scissors"]:
                p1_choice = "rock"
                
            choices_info = {
                "rock": ("حجر", "🪨"),
                "paper": ("ورقة", "📄"),
                "scissors": ("مقص", "✂️")
            }
            c_name, c_emoji = choices_info[p1_choice]
            
            # أزرار اللاعب الثاني للاختيار
            rps_board = InlineKeyboardMarkup()
            rps_board.row(
                InlineKeyboardButton("🪨 حجر", callback_data=f"rps_play_{user_id}_{p1_choice}_rock"),
                InlineKeyboardButton("📄 ورقة", callback_data=f"rps_play_{user_id}_{p1_choice}_paper"),
                InlineKeyboardButton("✂️ مقص", callback_data=f"rps_play_{user_id}_{p1_choice}_scissors")
            )
            
            results.append(
                InlineQueryResultArticle(
                    id='rps_game_res',
                    title='✂️ إرسال تحدي حجر ورقة مقص جاهز',
                    description=f'انقر لإرسال التحدي (لقد اخترت {c_name}) ودع صديقك ينافسك!',
                    input_message_content=InputTextMessageContent(
                        message_text=(
                            f"✂️ **تحدي حجر ورقة مقص جديد!**\n\n"
                            f"👤 قام اللاعب الأول باختيار حركته (سرا 🔒).\n"
                            f"الآن دور اللاعب الثاني للاختيار ومنافسة الأول:"
                        ),
                        parse_mode='Markdown'
                    ),
                    reply_markup=rps_board
                )
            )
            
        try:
            bot.answer_inline_query(inline_query.id, results, cache_time=1)
        except Exception as e:
            print(f"Inline Error: {e}")

    # معالجة تفاعلات لعبة XO التفاعلية
    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("xo_"))
    def handle_xo_click(call):
        inline_id = call.inline_message_id
        if not inline_id:
            bot.answer_callback_query(call.id, "خطأ في معالجة اللعبة.")
            return

        if inline_id not in ACTIVE_XO_GAMES:
            ACTIVE_XO_GAMES[inline_id] = {
                "board": ["⬜"] * 9,
                "turn": "❌",
                "status": "playing"
            }
        
        game = ACTIVE_XO_GAMES[inline_id]
        if game["status"] != "playing":
            bot.answer_callback_query(call.id, "انتهت هذه الجولة بالفعل!")
            return

        try:
            idx = int(call.data.split("_")[1])
        except ValueError:
            return

        if game["board"][idx] != "⬜":
            bot.answer_callback_query(call.id, "هذه الخانة محجوزة بالفعل! اختر غيرها.")
            return

        symbol = game["turn"]
        game["board"][idx] = symbol

        board = game["board"]
        winning_combos = [
            (0,1,2), (3,4,5), (6,7,8),
            (0,3,6), (1,4,7), (2,5,8),
            (0,4,8), (2,4,6)
        ]
        
        winner = None
        for combo in winning_combos:
            if board[combo[0]] == board[combo[1]] == board[combo[2]] != "⬜":
                winner = symbol
                break

        is_draw = "⬜" not in board and not winner

        new_markup = InlineKeyboardMarkup()
        for i in range(0, 9, 3):
            new_markup.row(
                InlineKeyboardButton(board[i], callback_data=f"xo_{i}"),
                InlineKeyboardButton(board[i+1], callback_data=f"xo_{i+1}"),
                InlineKeyboardButton(board[i+2], callback_data=f"xo_{i+2}")
            )

        if winner:
            game["status"] = "finished"
            text = f"🎮 **انتهت لعبة XO!**\n\n🎉 الف مبروك للفائز بالرمز ({winner})!"
            new_markup = None
        elif is_draw:
            game["status"] = "finished"
            text = "🎮 **انتهت لعبة XO!**\n\n🤝 تعادل تام بين اللاعبين."
            new_markup = None
        else:
            game["turn"] = "⭕️" if symbol == "❌" else "❌"
            text = f"🎮 **لعبة XO جارية...**\nدور اللاعب ({game['turn']}):"

        bot.answer_callback_query(call.id, "تم تسجيل نقرتك بنجاح!")
        try:
            bot.edit_message_text(
                inline_message_id=inline_id,
                text=text,
                reply_markup=new_markup,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"XO Edit Error: {e}")

    # معالجة تفاعلات لعبة حجر ورقة مقص عندما يختار اللاعب الثاني
    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("rps_play_"))
    def handle_rps_play(call):
        parts = call.data.split("_")
        if len(parts) < 5:
            return
            
        p1_id = int(parts[2])
        c1 = parts[3] # rock, paper, scissors
        c2 = parts[4] # rock, paper, scissors
        
        user_id = call.from_user.id
        user_name = call.from_user.first_name
        
        if user_id == p1_id:
            bot.answer_callback_query(call.id, "لا يمكنك اللعب ضد نفسك! انتظر صديقاً ليختار.", show_alert=True)
            return

        choices_map = {
            "rock": ("حجر", "🪨"),
            "paper": ("ورقة", "📄"),
            "scissors": ("مقص", "✂️")
        }
        
        c1_name, c1_emoji = choices_map[c1]
        c2_name, c2_emoji = choices_map[c2]

        # تطبيق قوانين الفوز
        if c1 == c2:
            result_msg = "🤝 **النتيجة: تعادل تام!**"
        elif (
            (c1 == "rock" and c2 == "scissors") or
            (c1 == "paper" and c2 == "rock") or
            (c1 == "scissors" and c2 == "paper")
        ):
            result_msg = "🎉 **الف مبروك! فاز اللاعب الأول (صاحب التحدي)!**"
        else:
            result_msg = f"🎉 **الف مبروك! فاز اللاعب {user_name} (المنافس)!**"

        final_text = (
            f"✂️ **نتائج تحدي حجر ورقة مقص**\n\n"
            f"👤 اللاعب الأول: {c1_emoji} {c1_name}\n"
            f"👤 {user_name}: {c2_emoji} {c2_name}\n\n"
            f"{result_msg}"
        )

        bot.answer_callback_query(call.id, f"اخترت {c2_name} - انتهت اللعبة!")
        try:
            bot.edit_message_text(
                inline_message_id=call.inline_message_id,
                text=final_text,
                reply_markup=None,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"RPS Play Finish Error: {e}")

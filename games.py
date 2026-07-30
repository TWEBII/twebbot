import random
import string
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, InlineQueryResultArticle, InputTextMessageContent

# قاعدة بيانات مؤقتة للأنشطة والألعاب الشغالة
games_db = {}

def generate_game_id():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=8))

def check_winner(board):
    win_conditions = [
        [0, 1, 2], [3, 4, 5], [6, 7, 8], # أفقي
        [0, 3, 6], [1, 4, 7], [2, 5, 8], # عمودي
        [0, 4, 8], [2, 4, 6]             # قطري
    ]
    for cond in win_conditions:
        if board[cond[0]] == board[cond[1]] == board[cond[2]] and board[cond[0]] != "⬜":
            return board[cond[0]]
    if "⬜" not in board:
        return "DRAW"
    return None

def build_board_markup(game_id, board, is_over=False):
    markup = InlineKeyboardMarkup()
    rows = []
    for i in range(0, 9, 3):
        row = []
        for j in range(3):
            idx = i + j
            cell_text = board[idx]
            cb_data = "xo_noop" if is_over else f"xo_click:{game_id}:{idx}"
            row.append(InlineKeyboardButton(cell_text, callback_data=cb_data))
        rows.append(row)
    for r in rows:
        markup.row(*r)
    
    markup.row(InlineKeyboardButton("العب مرا اخرا 🕹️", callback_data=f"xo_restart:{game_id}"))
    return markup

def setup_game_handlers(bot):

    # 1. التفاعل مع البحث الشفاف (Inline Query) لإرسال التحدي
    @bot.inline_handler(func=lambda query: True)
    def inline_xo_handler(query):
        game_id = generate_game_id()
        user_name = query.from_user.first_name or "Ahmed"
        
        games_db[game_id] = {
            "p1_id": query.from_user.id,
            "p1_name": user_name,
            "p2_id": None,
            "p2_name": "(⭕)",
            "turn": query.from_user.id,
            "board": ["⬜"] * 9,
            "status": "waiting"
        }

        share_text = (
            "لعبة 🤖 XO\n"
            "انقر على الزر أدناه لبدء 🕹️ 👇"
        )
        markup = InlineKeyboardMarkup()
        markup.add(InlineKeyboardButton("بدأ اللعب ! 🎮", callback_data=f"xo_start:{game_id}"))

        result = InlineQueryResultArticle(
            id=f"xo_{game_id}",
            title="لعبة XO - تحدي إكس أو",
            description="اضغط هنا لإرسال التحدي إلى الدردشة",
            input_message_content=InputTextMessageContent(share_text, parse_mode="Markdown"),
            reply_markup=markup
        )
        bot.answer_inline_query(query.id, [result], cache_time=1)

    # 2. إدارة نقرات الأزرار داخل اللعبة
    @bot.callback_query_handler(func=lambda call: call.data.startswith("xo_"))
    def callback_xo_handler(call):
        data = call.data.split(":")
        action = data[0]

        if action == "xo_noop":
            bot.answer_callback_query(call.id, "انتهت اللعبة بالفعل!")
            return

        # بدء اللعب عند انضمام المنافس
        if action == "xo_start":
            game_id = data[1]
            game = games_db.get(game_id)
            
            if not game:
                game = {
                    "p1_id": call.from_user.id,
                    "p1_name": call.from_user.first_name or "Ahmed",
                    "p2_id": None,
                    "p2_name": "(⭕)",
                    "turn": call.from_user.id,
                    "board": ["⬜"] * 9,
                    "status": "waiting"
                }
                games_db[game_id] = game

            if game["p2_id"] is None:
                if call.from_user.id != game["p1_id"]:
                    game["p2_id"] = call.from_user.id
                    game["p2_name"] = call.from_user.first_name or "المنافس"
                    game["status"] = "playing"
                    bot.answer_callback_query(call.id, "انضممت إلى اللعبة! بالتوفيق.")
                else:
                    bot.answer_callback_query(call.id, "بانتظار انضمام صديقك للعب معاً...")
                    return

            game_text = (
                f"عبّر @xosBBot\n"
                f"اللاعب الاول ❌ : {game['p1_name']}\n"
                f"اللاعب الثاني 🌳 : {game['p2_name']}"
            )
            markup = build_board_markup(game_id, game["board"])
            try:
                bot.edit_message_text(game_text, inline_message_id=call.inline_message_id, reply_markup=markup)
            except:
                pass

        # الضغط على أحد المربعات
        elif action == "xo_click":
            game_id = data[1]
            idx = int(data[2])
            game = games_db.get(game_id)

            if not game:
                bot.answer_callback_query(call.id, "هذه اللعبة قديمة، ابدأ لعبة جديدة!")
                return

            if game["p2_id"] is None:
                bot.answer_callback_query(call.id, "ينبغي انضمام اللاعب الثاني أولاً!")
                return

            if call.from_user.id != game["turn"]:
                bot.answer_callback_query(call.id, "ليس دورك الآن! انتظر المنافس.")
                return

            if game["board"][idx] != "⬜":
                bot.answer_callback_query(call.id, "هذا المربع ممتلئ!")
                return

            # تسجيل الحركة
            if call.from_user.id == game["p1_id"]:
                game["board"][idx] = "❌"
                game["turn"] = game["p2_id"]
            else:
                game["board"][idx] = "⭕"
                game["turn"] = game["p1_id"]

            winner = check_winner(game["board"])

            if winner:
                game["status"] = "over"
                if winner == "❌":
                    win_text = (
                        f"عبّر @xosBBot\n"
                        f"اللاعب الاول ❌ : {game['p1_name']}\n"
                        f"اللاعب الثاني 🌳 : {game['p2_name']}\n"
                        f"الفائز ❌ {game['p1_name']} : 🏆"
                    )
                elif winner == "⭕":
                    win_text = (
                        f"عبّر @xosBBot\n"
                        f"اللاعب الاول ❌ : {game['p1_name']}\n"
                        f"اللاعب الثاني 🌳 : {game['p2_name']}\n"
                        f"الفائز ⭕ {game['p2_name']} : 🏆"
                    )
                else:
                    win_text = (
                        f"عبّر @xosBBot\n"
                        f"اللاعب الاول ❌ : {game['p1_name']}\n"
                        f"اللاعب الثاني 🌳 : {game['p2_name']}\n"
                        f"تعادل بين اللاعبين! 🤝"
                    )

                markup = build_board_markup(game_id, game["board"], is_over=True)
                bot.edit_message_text(win_text, inline_message_id=call.inline_message_id, reply_markup=markup)
                bot.answer_callback_query(call.id, "انتهت اللعبة!")
            else:
                game_text = (
                    f"عبّر @xosBBot\n"
                    f"اللاعب الاول ❌ : {game['p1_name']}\n"
                    f"اللاعب الثاني 🌳 : {game['p2_name']}"
                )
                markup = build_board_markup(game_id, game["board"])
                bot.edit_message_text(game_text, inline_message_id=call.inline_message_id, reply_markup=markup)
                bot.answer_callback_query(call.id)

        # زر "العب مرا اخرا"
        elif action == "xo_restart":
            game_id = data[1]
            old_game = games_db.get(game_id)
            new_game_id = generate_game_id()
            
            p1_id = call.from_user.id
            p1_name = call.from_user.first_name or "Ahmed"
            p2_id = old_game["p2_id"] if old_game and old_game["p2_id"] != p1_id else (old_game["p1_id"] if old_game else None)
            p2_name = old_game["p2_name"] if old_game and old_game["p2_id"] != p1_id else (old_game["p1_name"] if old_game else "(⭕)")

            games_db[new_game_id] = {
                "p1_id": p1_id,
                "p1_name": p1_name,
                "p2_id": p2_id,
                "p2_name": p2_name,
                "turn": p1_id,
                "board": ["⬜"] * 9,
                "status": "playing" if p2_id else "waiting"
            }

            game_text = (
                f"عبّر @xosBBot\n"
                f"اللاعب الاول ❌ : {p1_name}\n"
                f"اللاعب الثاني 🌳 : {p2_name}"
            )
            markup = build_board_markup(new_game_id, games_db[new_game_id]["board"])
            bot.edit_message_text(game_text, inline_message_id=call.inline_message_id, reply_markup=markup)
            bot.answer_callback_query(call.id, "بدأت لعبة جديدة!")

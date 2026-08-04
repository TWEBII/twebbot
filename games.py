# -*- coding: utf-8 -*-
import random
import os
from telebot.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    InlineQueryResultArticle,
    InputTextMessageContent
)
from pymongo import MongoClient

# ==================== إعدادات قاعدة بيانات MongoDB = ====================
# استبدل الرابط أدناه برابط الاتصال الخاص بقاعدة بياناتك على MongoDB
MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017/")
client = MongoClient(MONGO_URI)
db = client["telegram_games_bot"]

# المجموعات (Collections) في MongoDB
riddles_collection = db["riddles"]
kut_collection = db["kut_questions"]
users_stats_collection = db["users_stats"]
users_collection = db["users"]  # مجموعة حفظ بيانات المستخدمين والمحافظات

# ذاكرة مؤقتة للحالات الحية للعبة ولعملية التسجيل
ACTIVE_XO_GAMES = {}
ACTIVE_XO_BOT_GAMES = {}
USER_REGISTRATION_STATE = {}  # لتتبع خطوات تسجيل المستخدم (الاسم ثم المحافظة)

# دالة لتحديث إحصائيات اللاعب في MongoDB
def update_user_stats(user_id, game_type, result):
    """
    result: 'wins', 'losses', 'draws'
    """
    try:
        users_stats_collection.update_one(
            {"user_id": user_id},
            {"$inc": {f"{game_type}.{result}": 1, f"{game_type}.total": 1}},
            upsert=True
        )
    except Exception as e:
        print(f"DB Stats Error: {e}")

def setup_game_handlers(bot):

    # القائمة الرئيسية للألعاب مع زر تسجيل الحساب
    def get_games_keyboard():
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("👤 تسجيل حساب جديد", callback_data="start_registration")
        )
        markup.row(
            InlineKeyboardButton("لعبة XO ❌⭕️", callback_data="game_xo_main"),
            InlineKeyboardButton("حجر ورقة مقص ✂️", callback_data="game_rps_main")
        )
        markup.row(
            InlineKeyboardButton("لعبة حوازير 🧩", callback_data="game_riddles_main"),
            InlineKeyboardButton("لعبة كت 🎯", callback_data="game_kut_main")
        )
        markup.row(InlineKeyboardButton("« رجوع للقائمة الرئيسية", callback_data="user_back_home"))
        return markup

    # بدء عملية التسجيل (طلب الاسم)
    @bot.callback_query_handler(func=lambda call: call.data == "start_registration")
    def start_registration_callback(call):
        bot.answer_callback_query(call.id)
        user_id = call.from_user.id
        USER_REGISTRATION_STATE[user_id] = {"step": "waiting_name"}
        
        text = (
            "👤 **تسجيل حساب جديد**\n\n"
            "الخطوة 1 من 2:\n"
            "يرجى إرسال **اسمك** أو اسم المستخدم الخاص بك في رسالة الآن:"
        )
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                parse_mode="Markdown"
            )
        except Exception:
            bot.send_message(
                chat_id=call.message.chat.id,
                text=text,
                parse_mode="Markdown"
            )

    # معالجة الرسائل النصية لخطوات التسجيل (الاسم ثم المحافظة تلقائياً)
    @bot.message_handler(func=lambda message: message.from_user.id in USER_REGISTRATION_STATE)
    def handle_registration_steps(message):
        user_id = message.from_user.id
        state_data = USER_REGISTRATION_STATE.get(user_id, {})
        step = state_data.get("step")

        if step == "waiting_name":
            name = message.text.strip()
            if not name:
                bot.reply_to(message, "⚠️ يرجى إرسال اسم صالح.")
                return
            
            # حفظ الاسم مؤقتاً في الحالة والانتقال لطلب المحافظة
            USER_REGISTRATION_STATE[user_id] = {
                "step": "waiting_governorate",
                "name": name
            }
            bot.reply_to(
                message,
                f"✅ تم حفظ الاسم: **{name}**\n\n"
                "الخطوة 2 من 2:\n"
                "الآن يرجى إرسال اسم **المحافظة** الخاصة بك:",
                parse_mode="Markdown"
            )

        elif step == "waiting_governorate":
            governorate = message.text.strip()
            if not governorate:
                bot.reply_to(message, "⚠️ يرجى إرسال اسم محافظة صالح.")
                return

            name = state_data.get("name")
            
            # حفظ البيانات نهائياً في مجموعة MongoDB (users_collection)
            try:
                users_collection.update_one(
                    {"user_id": user_id},
                    {
                        "$set": {
                            "user_id": user_id,
                            "username": message.from_user.username,
                            "name": name,
                            "governorate": governorate
                        }
                    },
                    upsert=True
                )
            except Exception as e:
                print(f"DB Registration Error: {e}")
                bot.reply_to(message, "❌ حدث خطأ أثناء حفظ البيانات في قاعدة البيانات. حاول مرة أخرى.")
                USER_REGISTRATION_STATE.pop(user_id, None)
                return

            # مسح حالة التسجيل بعد الإنجاز
            USER_REGISTRATION_STATE.pop(user_id, None)

            # إرسال رسالة نجاح إنشاء الحساب
            success_text = (
                f"🎉 **تم إنشاء الحساب بنجاح!**\n\n"
                f"👤 الاسم: **{name}**\n"
                f"📍 المحافظة: **{governorate}**\n\n"
                f"يمكنك الآن التوجه للألعاب والاستمتاع بالتحديات!"
            )
            bot.reply_to(message, success_text, parse_mode="Markdown")

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

    # ==================== قسم لعبة XO ====================
    @bot.callback_query_handler(func=lambda call: call.data == "game_xo_main")
    def start_xo_game(call):
        bot.answer_callback_query(call.id)

        xo_markup = InlineKeyboardMarkup()
        xo_markup.row(
            InlineKeyboardButton("👥 تحدي صديق", switch_inline_query="XO_Challenge"),
            InlineKeyboardButton("🤖 تحدي البوت", callback_data="xo_vs_bot_start")
        )
        xo_markup.row(InlineKeyboardButton("« رجوع للألعاب", callback_data="user_menu_games"))

        text = (
            "🎮 **لعبة XO ❌⭕️**\n\n"
            "اختر طريقة اللعب التي تفضلها:"
        )
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

    # بدء لعبة XO ضد البوت
    @bot.callback_query_handler(func=lambda call: call.data == "xo_vs_bot_start")
    def xo_vs_bot_start(call):
        bot.answer_callback_query(call.id, "بدأت لعبة XO ضد البوت!")
        chat_id = call.message.chat.id
        msg_id = call.message.message_id

        ACTIVE_XO_BOT_GAMES[(chat_id, msg_id)] = {
            "board": ["⬜"] * 9,
            "status": "playing"
        }

        markup = InlineKeyboardMarkup()
        for i in range(0, 9, 3):
            markup.row(
                InlineKeyboardButton("⬜", callback_data=f"xobot_{i}"),
                InlineKeyboardButton("⬜", callback_data=f"xobot_{i+1}"),
                InlineKeyboardButton("⬜", callback_data=f"xobot_{i+2}")
            )
        markup.row(InlineKeyboardButton("🔄 إعادة الجولة", callback_data="xo_vs_bot_start"))
        markup.row(InlineKeyboardButton("« رجوع للألعاب", callback_data="game_xo_main"))

        text = "🤖 **لعبة XO ضد البوت**\n\nأنت تلعب بـ (❌) والبوت بـ (⭕️).\nدورك الآن، اختر خانة:"
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=text,
                reply_markup=markup,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"XO Bot Start Error: {e}")

    # تفاعل لوحة XO ضد البوت
    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("xobot_"))
    def handle_xo_bot_click(call):
        chat_id = call.message.chat.id
        msg_id = call.message.message_id
        user_id = call.from_user.id
        key = (chat_id, msg_id)

        if key not in ACTIVE_XO_BOT_GAMES:
            ACTIVE_XO_BOT_GAMES[key] = {"board": ["⬜"] * 9, "status": "playing"}

        game = ACTIVE_XO_BOT_GAMES[key]
        if game["status"] != "playing":
            bot.answer_callback_query(call.id, "انتهت هذه الجولة!", show_alert=True)
            return

        try:
            idx = int(call.data.split("_")[1])
        except ValueError:
            return

        board = game["board"]
        if board[idx] != "⬜":
            bot.answer_callback_query(call.id, "هذه الخانة محجوزة!", show_alert=True)
            return

        board[idx] = "❌"

        winning_combos = [(0,1,2), (3,4,5), (6,7,8), (0,3,6), (1,4,7), (2,5,8), (0,4,8), (2,4,6)]
        winner = None
        for c in winning_combos:
            if board[c[0]] == board[c[1]] == board[c[2]] != "⬜":
                winner = board[c[0]]
                break

        is_draw = "⬜" not in board and not winner

        if not winner and not is_draw:
            empty_spots = [i for i, val in enumerate(board) if val == "⬜"]
            if empty_spots:
                bot_idx = random.choice(empty_spots)
                board[bot_idx] = "⭕️"

                for c in winning_combos:
                    if board[c[0]] == board[c[1]] == board[c[2]] != "⬜":
                        winner = board[c[0]]
                        break
                is_draw = "⬜" not in board and not winner

        markup = InlineKeyboardMarkup()
        if not winner and not is_draw:
            for i in range(0, 9, 3):
                markup.row(
                    InlineKeyboardButton(board[i], callback_data=f"xobot_{i}"),
                    InlineKeyboardButton(board[i+1], callback_data=f"xobot_{i+1}"),
                    InlineKeyboardButton(board[i+2], callback_data=f"xobot_{i+2}")
                )
            text = "🤖 **لعبة XO ضد البوت**\n\nدورك الآن (❌):"
        else:
            game["status"] = "finished"
            if winner == "❌":
                text = "🤖 **لعبة XO ضد البوت**\n\n🎉 تهانينا! لقد هزمت البوت ببراعة!"
                update_user_stats(user_id, "xo_bot", "wins")
            elif winner == "⭕️":
                text = "🤖 **لعبة XO ضد البوت**\n\n😢 حظاً أوفر، لقد فاز البوت عليك!"
                update_user_stats(user_id, "xo_bot", "losses")
            else:
                text = "🤖 **لعبة XO ضد البوت**\n\n🤝 تعادل تام بينك وبين البوت."
                update_user_stats(user_id, "xo_bot", "draws")

            markup.row(InlineKeyboardButton("🔄 تلعب مرة أخرى", callback_data="xo_vs_bot_start"))
            markup.row(InlineKeyboardButton("« رجوع للألعاب", callback_data="game_xo_main"))

        bot.answer_callback_query(call.id)
        try:
            bot.edit_message_text(
                chat_id=chat_id,
                message_id=msg_id,
                text=text,
                reply_markup=markup,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"XO Bot Click Error: {e}")

    # ==================== قسم لعبة حجر ورقة مقص ====================
    @bot.callback_query_handler(func=lambda call: call.data == "game_rps_main")
    def start_rps_game(call):
        bot.answer_callback_query(call.id)

        rps_markup = InlineKeyboardMarkup()
        rps_markup.row(
            InlineKeyboardButton("👥 تحدي صديق", callback_data="rps_friend_mode"),
            InlineKeyboardButton("🤖 تحدي البوت", callback_data="rps_bot_mode")
        )
        rps_markup.row(InlineKeyboardButton("« رجوع للألعاب", callback_data="user_menu_games"))

        text = (
            "✂️ **لعبة حجر ورقة مقص**\n\n"
            "اختر وضع التحدي المناسب لك:"
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

    @bot.callback_query_handler(func=lambda call: call.data == "rps_friend_mode")
    def rps_friend_mode(call):
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("🪨 حجر", callback_data="rps_p1_rock"),
            InlineKeyboardButton("📄 ورقة", callback_data="rps_p1_paper"),
            InlineKeyboardButton("✂️ مقص", callback_data="rps_p1_scissors")
        )
        markup.row(InlineKeyboardButton("« رجوع", callback_data="game_rps_main"))

        text = "✂️ **تحدي صديق**\n\nالخطوة الأولى: اختر حركتك سرا أولاً:"
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=markup,
                parse_mode="Markdown"
            )
        except Exception:
            pass

    @bot.callback_query_handler(func=lambda call: call.data == "rps_bot_mode")
    def rps_bot_mode(call):
        bot.answer_callback_query(call.id)
        markup = InlineKeyboardMarkup()
        markup.row(
            InlineKeyboardButton("🪨 حجر", callback_data="rps_vs_bot_rock"),
            InlineKeyboardButton("📄 ورقة", callback_data="rps_vs_bot_paper"),
            InlineKeyboardButton("✂️ مقص", callback_data="rps_vs_bot_scissors")
        )
        markup.row(InlineKeyboardButton("« رجوع", callback_data="game_rps_main"))

        text = "🤖 **تحدي البوت في حجر ورقة مقص**\n\nاختر ما تنافس به البوت الآن:"
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=markup,
                parse_mode="Markdown"
            )
        except Exception:
            pass

    @bot.callback_query_handler(func=lambda call: call.data in ["rps_vs_bot_rock", "rps_vs_bot_paper", "rps_vs_bot_scissors"])
    def play_rps_vs_bot(call):
        user_id = call.from_user.id
        user_choice_key = call.data.replace("rps_vs_bot_", "")
        choices = {
            "rock": ("حجر", "🪨"),
            "paper": ("ورقة", "📄"),
            "scissors": ("مقص", "✂️")
        }

        user_name, user_emoji = choices[user_choice_key]
        bot_key = random.choice(list(choices.keys()))
        bot_name, bot_emoji = choices[bot_key]

        if user_choice_key == bot_key:
            result_text = "🤝 **تعادل تام مع البوت!**"
            update_user_stats(user_id, "rps_bot", "draws")
        elif (
            (user_choice_key == "rock" and bot_key == "scissors") or
            (user_choice_key == "paper" and bot_key == "rock") or
            (user_choice_key == "scissors" and bot_key == "paper")
        ):
            result_text = "🎉 **تهانينا، لقد فزت على البوت!**"
            update_user_stats(user_id, "rps_bot", "wins")
        else:
            result_text = "😢 **حظاً أوفر، لقد فاز البوت عليك!**"
            update_user_stats(user_id, "rps_bot", "losses")

        text = (
            f"🤖 **نتيجة تحدي البوت**\n\n"
            f"👤 اختيارك: {user_emoji} {user_name}\n"
            f"🤖 اختيار البوت: {bot_emoji} {bot_name}\n\n"
            f"{result_text}"
        )

        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("🔄 تلعب مرة أخرى", callback_data="rps_bot_mode"))
        markup.row(InlineKeyboardButton("« رجوع للألعاب", callback_data="game_rps_main"))

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
            print(f"RPS Bot Play Error: {e}")

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
        share_markup.row(InlineKeyboardButton("🔄 تغيير الحركة", callback_data="rps_friend_mode"))
        share_markup.row(InlineKeyboardButton("« رجوع", callback_data="game_rps_main"))

        text = (
            f"✂️ **تحدي صديق**\n\n"
            f"لقد اخترت: {emoji} **{name}**\n\n"
            f"انقر على الزر أدناه لمشاركة التحدي مع صديقك في أي دردشة:"
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

    # ==================== قسم لعبة كت (من MongoDB) ====================
    @bot.callback_query_handler(func=lambda call: call.data == "game_kut_main")
    def start_kut_game(call):
        bot.answer_callback_query(call.id)
        
        question = "ما هو أكثر شيء تندم عليه؟"
        try:
            pipeline = [{"$sample": {"size": 1}}]
            kut_docs = list(kut_collection.aggregate(pipeline))
            if kut_docs:
                question = kut_docs[0].get("question", question)
        except Exception as e:
            print(f"MongoDB Kut Error: {e}")

        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("🔄 سؤال آخر", callback_data="game_kut_main"))
        markup.row(InlineKeyboardButton("« رجوع للألعاب", callback_data="user_menu_games"))

        text = (
            "🎯 **لعبة كت (صراحة وتحدي)**\n\n"
            f"📌 **السؤال:**\n{question}"
        )
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=markup,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Kut Game Error: {e}")

    # ==================== قسم لعبة حوازير (من MongoDB) ====================
    @bot.callback_query_handler(func=lambda call: call.data == "game_riddles_main")
    def start_riddles_game(call):
        bot.answer_callback_query(call.id)
        
        riddle_text = "ما هو الشيء الذي إذا أخذت منه كبر وصغر؟"
        try:
            pipeline = [{"$sample": {"size": 1}}]
            riddle_docs = list(riddles_collection.aggregate(pipeline))
            if riddle_docs:
                riddle_text = riddle_docs[0].get("riddle", riddle_text)
        except Exception as e:
            print(f"MongoDB Riddles Error: {e}")

        markup = InlineKeyboardMarkup()
        markup.row(InlineKeyboardButton("🔄 حزورة أخرى", callback_data="game_riddles_main"))
        markup.row(InlineKeyboardButton("« رجوع للألعاب", callback_data="user_menu_games"))

        text = (
            "🧩 **لعبة الحوازير والذكاء**\n\n"
            f"❓ **الحزورة:**\n{riddle_text}"
        )
        try:
            bot.edit_message_text(
                chat_id=call.message.chat.id,
                message_id=call.message.message_id,
                text=text,
                reply_markup=markup,
                parse_mode="Markdown"
            )
        except Exception as e:
            print(f"Riddles Game Error: {e}")

    # ==================== معالج استعلامات الـ Inline ====================
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
                    InlineKeyboardButton(initial_board[i], callback_data=f"xo_{user_id}_{i}"),
                    InlineKeyboardButton(initial_board[i+1], callback_data=f"xo_{user_id}_{i+1}"),
                    InlineKeyboardButton(initial_board[i+2], callback_data=f"xo_{user_id}_{i+2}")
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

    # معالجة تفاعلات لعبة XO بين شخصين
    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("xo_") and not call.data.startswith("xobot_"))
    def handle_xo_click(call):
        parts = call.data.split("_")
        if len(parts) < 3:
            return

        p1_id = int(parts[1])
        try:
            idx = int(parts[2])
        except ValueError:
            return

        inline_id = call.inline_message_id
        if not inline_id:
            bot.answer_callback_query(call.id, "خطأ في معالجة اللعبة.")
            return

        if inline_id not in ACTIVE_XO_GAMES:
            ACTIVE_XO_GAMES[inline_id] = {
                "board": ["⬜"] * 9,
                "turn": "❌",
                "p1_id": p1_id,
                "p2_id": None,
                "status": "playing"
            }

        game = ACTIVE_XO_GAMES[inline_id]
        if game["status"] != "playing":
            bot.answer_callback_query(call.id, "انتهت هذه الجولة بالفعل!", show_alert=True)
            return

        user_id = call.from_user.id
        turn = game["turn"]

        if turn == "❌":
            if user_id != game["p1_id"]:
                bot.answer_callback_query(call.id, "ليس دورك! هذا دور اللاعب الأول (❌).", show_alert=True)
                return
        else:
            if game["p2_id"] is None:
                if user_id == game["p1_id"]:
                    bot.answer_callback_query(call.id, "لا يمكنك اللعب ضد نفسك! انتظر صديقاً ليشارك.", show_alert=True)
                    return
                game["p2_id"] = user_id
            else:
                if user_id != game["p2_id"]:
                    bot.answer_callback_query(call.id, "ليس دورك! هذا دور اللاعب الثاني (⭕️).", show_alert=True)
                    return

        if game["board"][idx] != "⬜":
            bot.answer_callback_query(call.id, "هذه الخانة محجوزة بالفعل! اختر غيرها.")
            return

        symbol = turn
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
                InlineKeyboardButton(board[i], callback_data=f"xo_{p1_id}_{i}"),
                InlineKeyboardButton(board[i+1], callback_data=f"xo_{p1_id}_{i+1}"),
                InlineKeyboardButton(board[i+2], callback_data=f"xo_{p1_id}_{i+2}")
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
            next_turn_symbol = game["turn"]
            text = f"🎮 **لعبة XO جارية...**\nدور اللاعب ({next_turn_symbol}):"

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

    # معالجة تفاعلات لعبة حجر ورقة مقص بين شخصين عبر الانلاين
    @bot.callback_query_handler(func=lambda call: call.data and call.data.startswith("rps_play_"))
    def handle_rps_play(call):
        parts = call.data.split("_")
        if len(parts) < 5:
            return

        p1_id = int(parts[2])
        c1 = parts[3]
        c2 = parts[4]

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

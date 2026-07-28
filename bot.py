import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

API_ID = 20503432
API_HASH = "26227bf46cdb65744fb4c6572b82bc01"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

app_bot = Client(
    "tweb_stream_bot", 
    api_id=API_ID, 
    api_hash=API_HASH, 
    bot_token=TELEGRAM_TOKEN, 
    in_memory=True
)

routes = web.RouteTableDef()

@routes.get('/')
async def index(request):
    return web.Response(text="TWEB Cloud Stream Bot is Active!", content_type='text/plain')

@app_bot.on_message(filters.video | filters.document)
async def handle_media(client, message):
    try:
        # إرسال زر يفتح المحاضرة مباشرة من رسالة البوت الداخلية بسرعة صاروخية وبدون استهلاك سيرفر الويب
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 اضغط هنا للمشاهدة والتحميل الفوري", callback_data=f"watch_{message.id}")]])
        await message.reply_text("✅ تم تجهيز رابط المحاضرة السريع:", reply_markup=markup)
    except Exception as e:
        print(f"Error: {e}")

@app_bot.on_callback_query(filters.regex("^watch_"))
async def callback_watch(client, callback_query):
    msg_id = int(callback_query.data.split("_")[1])
    await callback_query.answer("جاري فتح المحاضرة...", show_alert=False)
    try:
        await client.copy_message(chat_id=callback_query.message.chat.id, from_chat_id=callback_query.message.chat.id, message_id=msg_id)
    except Exception:
        await callback_query.message.reply_text("عذراً، حدث خطأ أو أن رسالة المحاضرة قديمة.")

@app_bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text("أهلاً بك يا أحمد في بوت TWEB السحابي المطور! 👋\n\nأرسل أي محاضرة وسأقوم بتجهيز رابط التشغيل الفوري لها.")

async def web_server():
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()

async def main():
    await app_bot.start()
    await web_server()
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())

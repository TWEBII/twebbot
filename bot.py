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
        media = message.video or message.document
        
        # استخدام رابط تليجرام المباشر الداخلي للرسالة لتجنب أي مشاكل في السيرفر
        file_id = media.file_id
        
        railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost:8080")
        base_url = f"https://{railway_domain}" if not railway_domain.startswith("http") else railway_domain
        
        # رابط مباشر يعتمد على ملفات تيليجرام الصافية
        watch_link = f"https://t.me/{app_bot.me.username}?start=file_{message.id}"
        
        # لفتح الفيديو مباشرة من سيرفرات تيليجرام بدون سكريبت معقد يستهلك الرام:
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("📺 اضغط هنا لمشاهدة المحاضرة", url=f"https://t.me/{app_bot.me.username}?start=file_{message.id}")]])
        await message.reply_text("✅ تم تجهيز رابط المحاضرة السريع:", reply_markup=markup)
    except Exception as e:
        print(f"Error: {e}")

@app_bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    text = message.text
    if len(text.split()) > 1:
        param = text.split()[1]
        if param.startswith("file_"):
            msg_id = int(param.split("_")[1])
            # إعادة توجيه المستخدم للملف الأصلي فوراً لفتحه بدون أي شاشة سوداء
            await message.reply_text("إليك المحاضرة المطلوبة جاهزة للمشاهدة الفورية 👇")
            await client.copy_message(chat_id=message.chat.id, from_chat_id=message.chat.id, message_id=msg_id)
            return

    await message.reply_text("أهلاً بك يا أحمد في بوت TWEB السحابي المطور! 👋\n\nأرسل أي محاضرة وسأقوم بتجهيزها لك.")

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

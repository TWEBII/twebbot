import os
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

API_ID = 20503432
API_HASH = "26227bf46cdb65744fb4c6572b82bc01"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

FILE_CACHE = {}

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

@routes.get('/direct/{file_id}')
async def direct_stream(request):
    file_id = request.match_info['file_id']
    meta = FILE_CACHE.get(file_id)
    
    if not meta:
        return web.Response(status=404, text="الملف غير موجود أو انتهت صلاحيته.")

    try:
        message = await app_bot.get_messages(meta['chat_id'], meta['message_id'])
        media = message.video or message.document
        
        # فتح اتصال تدريجي مباشر وسريع جداً بدون تعقيد ليعمل المشغل الخارجي فوراً
        response = web.StreamResponse()
        response.content_type = 'video/mp4'
        response.headers['Accept-Ranges'] = 'bytes'
        await response.prepare(request)
        
        async for chunk in app_bot.stream_media(message):
            await response.write(chunk)
            await response.drain()
            
        return response
    except Exception as e:
        return web.Response(status=500, text=f"خطأ في البث: {e}")

@app_bot.on_message(filters.video | filters.document)
async def handle_media(client, message):
    try:
        media = message.video or message.document
        file_id = media.file_unique_id
        
        FILE_CACHE[file_id] = {
            'chat_id': message.chat.id,
            'message_id': message.id
        }
        
        railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost:8080")
        base_url = f"https://{railway_domain}" if not railway_domain.startswith("http") else railway_domain
        
        direct_link = f"{base_url}/direct/{file_id}"
        
        # زر يفتح الرابط المباشر للخارج (ليفتحه مشغل الهاتف أو المتصفح الخارجي فوراً)
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("🚀 تشغيل مباشر في المشغل", url=direct_link)]])
        await message.reply_text("✅ تم تجهيز الرابط المباشر السريع:", reply_markup=markup)
    except Exception as e:
        print(f"Error: {e}")

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
    asyncio.get_event_loop().run_forever()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
 

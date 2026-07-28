import os
import re
import asyncio
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import web

# بيانات تطبيق تيليجرام الخاص بك
API_ID = 20503432
API_HASH = "26227bf46cdb65744fb4c6572b82bc01"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

FILE_CACHE = {}

# إعداد عميل بايروجرام
app_bot = Client(
    "tweb_stream_bot", 
    api_id=API_ID, 
    api_hash=API_HASH, 
    bot_token=TELEGRAM_TOKEN, 
    in_memory=True
)

routes = web.RouteTableDef()

HTML_PAGE = """<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TWEB Cloud Stream</title>
    <style>
        body { background: #0f172a; color: #fff; font-family: Tahoma, sans-serif; text-align: center; padding: 30px; margin: 0; }
        h2 { color: #38bdf8; margin-bottom: 20px; font-size: 28px; font-weight: bold; }
        .video-container { max-width: 800px; margin: 0 auto; background: #1e293b; padding: 15px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.5); }
        video { width: 100%; border-radius: 8px; outline: none; }
        .btn { display: inline-block; margin-top: 25px; padding: 12px 25px; background: #38bdf8; color: #0f172a; text-decoration: none; font-weight: bold; border-radius: 8px; }
        .btn:hover { background: #0ea5e9; }
        .footer-tag { margin-top: 20px; color: #94a3b8; font-size: 16px; font-weight: bold; }
    </style>
</head>
<body>
    <h2>TWEB Cloud Stream</h2>
    <div class="video-container">
        <video controls autoplay playsinline preload="auto">
            <source src="{stream_url}" type="video/mp4">
            متصفحك لا يدعم تشغيل الفيديو.
        </video>
    </div>
    <div>
        <a class="btn" href="{stream_url}" download>تحميل المحاضرة برابط مباشر 📥</a>
    </div>
    <div class="footer-tag">@TWEBiii</div>
</body>
</html>"""

@routes.get('/')
async def index(request):
    return web.Response(text="TWEB Cloud Stream Bot is Active!", content_type='text/plain')

@routes.get('/watch/{file_id}')
async def watch(request):
    file_id = request.match_info['file_id']
    railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", request.host)
    base_url = f"https://{railway_domain}" if not railway_domain.startswith("http") else railway_domain
    stream_url = f"{base_url}/stream/{file_id}"
    return web.Response(text=HTML_PAGE.replace("{stream_url}", stream_url), content_type='text/html')

@routes.get('/stream/{file_id}')
async def stream(request):
    file_id = request.match_info['file_id']
    message = FILE_CACHE.get(file_id)
    
    if not message:
        return web.Response(status=404, text="عذراً، الملف غير موجود. أرسل الفيديو للبوت مجدداً.")

    media = message.video or message.document
    file_size = media.file_size

    offset = 0
    limit = file_size
    range_header = request.headers.get('Range', '')

    if range_header:
        match = re.search(r'bytes=(\d+)-(\d*)', range_header)
        if match:
            offset = int(match.group(1))
            if match.group(2):
                limit = int(match.group(2)) + 1 - offset
            else:
                limit = file_size - offset

    headers = {
        'Content-Type': 'video/mp4',
        'Accept-Ranges': 'bytes',
        'Content-Range': f'bytes {offset}-{offset + limit - 1}/{file_size}',
        'Content-Length': str(limit),
        'Connection': 'keep-alive',
    }

    response = web.StreamResponse(status=206 if range_header else 200, headers=headers)
    await response.prepare(request)

    try:
        # تدفق البيانات بسرعة عالية للمتصفح دون تأخير
        async for chunk in app_bot.stream_media(message, offset=offset, limit=limit):
            await response.write(chunk)
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"Stream Error: {e}")

    return response

@app_bot.on_message(filters.video | filters.document)
async def handle_media(client, message):
    msg = await message.reply_text("⏳ جاري توليد رابط البث السحابي السريع للمحاضرة...")
    try:
        media = message.video or message.document
        file_id = media.file_unique_id
        
        FILE_CACHE[file_id] = message
        
        railway_domain = os.getenv("RAILWAY_PUBLIC_DOMAIN", "localhost:8080")
        base_url = f"https://{railway_domain}" if not railway_domain.startswith("http") else railway_domain
        
        watch_link = f"{base_url}/watch/{file_id}"
        
        markup = InlineKeyboardMarkup([[InlineKeyboardButton("📺 مشاهدة وتحميل المحاضرة", url=watch_link)]])
        await msg.edit_text("✅ تم تجهيز رابط البث بنجاح!\n\nيمكنك الآن المشاهدة والتحميل بدون أي توقف:", reply_markup=markup)
    except Exception as e:
        await msg.edit_text(f"⚠️ حدث خطأ: {e}")

@app_bot.on_message(filters.command("start"))
async def start_cmd(client, message):
    await message.reply_text("أهلاً بك يا أحمد في بوت TWEB السحابي المطور! 👋\n\nأرسل أي محاضرة وسأقوم ببثها فوراً وبدون أي أخطاء.")

async def web_server():
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, '0.0.0.0', port)
    await site.start()
    print(f"Web server started on port {port}")

async def main():
    await app_bot.start()
    print("Telegram Bot started successfully!")
    await web_server()
    await asyncio.Event().wait()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
 

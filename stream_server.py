import os
from flask import Flask, Response, request, render_template_string
import aiohttp
import asyncio

app = Flask(__name__)

# ضع توكن البوت الخاص بك هنا
BOT_TOKEN = "8898698558:AAFjuVht_Qq1DD_-1nRIB1YT6U-VWPnwtFM"
# ضع رابط استضافتك هنا (مثلاً رابط مشروعك على Railway)
BASE_URL = "https://your-app-name.up.railway.app"

# =========================================================
# قالب صفحة الويب للمشغل مع بصمة وتصميم TWEB
# =========================================================
PLAYER_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TWEB Stream | مشغل الفيديوهات المباشر</title>
    <style>
        body {
            background-color: #0b0f19;
            color: #ffffff;
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 100vh;
        }
        .container {
            width: 100%;
            max-width: 900px;
            padding: 20px;
            box-sizing: border-box;
            text-align: center;
        }
        .brand-header {
            background: linear-gradient(135deg, #2563eb, #7c3aed);
            padding: 15px 20px;
            border-radius: 14px 14px 0 0;
            font-size: 20px;
            font-weight: bold;
            letter-spacing: 1px;
            box-shadow: 0 4px 20px rgba(37, 99, 235, 0.4);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .brand-header span {
            font-size: 13px;
            background: rgba(0, 0, 0, 0.35);
            padding: 5px 12px;
            border-radius: 20px;
            letter-spacing: 0.5px;
        }
        .video-wrapper {
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 0 0 14px 14px;
            overflow: hidden;
            box-shadow: 0 10px 30px rgba(0,0,0,0.6);
        }
        video {
            width: 100%;
            max-height: 72vh;
            display: block;
            background: #000;
        }
        .file-info {
            margin-top: 15px;
            padding: 15px;
            background: #111827;
            border: 1px solid #1f2937;
            border-radius: 10px;
            text-align: right;
            font-size: 14px;
            color: #9ca3af;
        }
        .file-info b {
            color: #60a5fa;
        }
        .footer {
            margin-top: 25px;
            font-size: 13px;
            color: #6b7280;
        }
        .footer b {
            color: #3b82f6;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="brand-header">
            🎬 TWEB Media Stream
            <span>Server Active</span>
        </div>
        <div class="video-wrapper">
            <video controls autoplay playsinline preload="metadata">
                <source src="{{ stream_url }}" type="video/mp4">
                متصفحك لا يدعم تشغيل الفيديو.
            </video>
        </div>
        
        <div class="file-info">
            <p>📂 اسم الملف: <b>{{ file_name }}</b></p>
            <p>⚡ حالة البث: <b>سريع، مباشر، وبدون تقطيع (Streaming Ready)</b></p>
        </div>

        <div class="footer">
            تم التطوير والإشراف بواسطة منصة وتطبيقات <b>TWEB</b>
        </div>
    </div>
</body>
</html>
"""

@app.route('/watch/<file_id>')
def watch_video(file_id):
    file_name = request.args.get('name', 'TWEB_Video.mp4')
    stream_link = f"{BASE_URL}/stream/{file_id}"
    return render_template_string(PLAYER_TEMPLATE, stream_url=stream_link, file_name=file_name)

@app.route('/stream/<file_id>')
def proxy_stream(file_id):
    # جلب مسار الفيديو من تليجرام وبثه للمتصفح تدريجياً لضمان عدم التقطيع
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    async def fetch_telegram_file():
        url = f"https://api.telegram.org/bot{BOT_TOKEN}/getFile?file_id={file_id}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                res_json = await resp.json()
                if res_json.get("ok"):
                    return res_json["result"]["file_path"]
        return None

    file_path = loop.run_until_complete(fetch_telegram_file())
    if not file_path:
        return "لم يتم العثور على الملف المطلوب", 404

    telegram_file_url = f"https://api.telegram.org/file/bot{BOT_TOKEN}/{file_path}"
    range_header = request.headers.get('Range', None)

    async def send_stream():
        async with aiohttp.ClientSession() as session:
            headers = {}
            if range_header:
                headers['Range'] = range_header
            async with session.get(telegram_file_url, headers=headers) as resp:
                async def generate():
                    async for chunk in resp.content.iter_chunked(1024 * 64):
                        yield chunk
                
                response = Response(generate(), status=resp.status, mimetype=resp.headers.get('Content-Type', 'video/mp4'))
                if 'Content-Length' in resp.headers:
                    response.headers['Content-Length'] = resp.headers['Content-Length']
                if 'Content-Range' in resp.headers:
                    response.headers['Content-Range'] = resp.headers['Content-Range']
                response.headers['Accept-Ranges'] = 'bytes'
                return response

    # تشغيل البث المباشر المقطع
    return loop.run_until_complete(send_stream())

if __name__ == '__main__':
    # تشغيل السيرفر على البورت المطلوب للاستضافة
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)

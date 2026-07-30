import os
import yt_dlp

def download_video(query_or_url, output_filename="video.mp4"):
    if os.path.exists(output_filename):
        try:
            os.remove(output_filename)
        except:
            pass

    target_url = query_or_url
    if not (query_or_url.startswith('http://') or query_or_url.startswith('https://')):
        target_url = f"ytsearch:{query_or_url}"

    ydl_opts = {
        'format': 'best[ext=mp4]/best',
        'outtmpl': output_filename,
        'quiet': False,          # اظهار تفاصيل التحميل في السيرفر
        'no_warnings': False,
        'socket_timeout': 30,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([target_url])
        
        if os.path.exists(output_filename):
            return output_filename
    except Exception as e:
        print(f"❌ تفاصيل خطأ yt-dlp البحتة: {str(e)}")

    return None

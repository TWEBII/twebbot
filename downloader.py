import os
import yt_dlp

def download_video(query_or_url, output_filename="video.mp4"):
    # تنظيف أي ملف قديم متراكم بنفس الاسم
    if os.path.exists(output_filename):
        try:
            os.remove(output_filename)
        except:
            pass

    # إذا كان المدخل ليس رابطاً صريحاً، قم بالبحث عنه في اليوتيوب تلقائياً
    target_url = query_or_url
    if not (query_or_url.startswith('http://') or query_or_url.startswith('https://')):
        target_url = f"ytsearch:{query_or_url}"

    ydl_opts = {
        'format': 'best[ext=mp4]/best',  # اختيار أفضل جودة فيديو بصيغة MP4
        'outtmpl': output_filename,      # حفظ الملف بالاسم المحدد
        'quiet': True,
        'no_warnings': True,
        'socket_timeout': 30,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([target_url])
        
        # التحقق من نجاح التحميل ووجود الملف على السيرفر
        if os.path.exists(output_filename):
            return output_filename
    except Exception as e:
        print(f"Download Error: {e}")

    return None

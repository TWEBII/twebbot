import os
import yt_dlp

def get_video_info(url):
    ydl_opts = {
        'quiet': True, 
        'no_warnings': True,
        'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return {
                'title': info.get('title', 'فيديو بدون عنوان'),
                'duration': info.get('duration', 0),
                'views': info.get('view_count', 0)
            }
    except Exception as e:
        print(f"Info Error: {e}")
    return None

def download_video(url, output_filename="video.mp4", mode="video"):
    if mode == "audio":
        out_file = output_filename.replace('.mp4', '.m4a') # استخدام صيغة m4a الأخف والأسرع لتيليجرام
        if os.path.exists(out_file):
            try: os.remove(out_file)
            except: pass
            
        ydl_opts = {
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': out_file,
            'quiet': True,
            'no_warnings': True,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
        }
    else:
        out_file = output_filename
        if os.path.exists(out_file):
            try: os.remove(out_file)
            except: pass
            
        ydl_opts = {
            'format': 'best[height<=360][ext=mp4]/best[height<=360]/best',
            'outtmpl': out_file,
            'quiet': True,
            'no_warnings': True,
            'geo_bypass': True,
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}}
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        if os.path.exists(out_file):
            return out_file
    except Exception as e:
        print(f"❌ خطأ التحميل: {e}")

    return None

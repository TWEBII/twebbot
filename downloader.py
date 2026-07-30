import yt_dlp
import os

# إنشاء مجلد للتحميلات إذا لم يكن موجوداً لتجنب الأخطاء
if not os.path.exists('downloads'):
    os.makedirs('downloads')

def get_video_info(url):
    """
    دالة لاستخراج تفاصيل المقطع قبل التحميل لعرضها للمستخدم (مع دعم كامل لتجاوز حظر يوتيوب)
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'extract_flat': False,
        'socket_timeout': 30,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        }
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        print(f"Error fetching info: {e}")
        return None

def download_media(url, media_type='video', progress_callback=None):
    """
    دالة لتحميل الفيديو أو الصوت بشكل آمن، مع ربط العداد الفعلي (Progress Hook)
    """
    max_size_bytes = 45 * 1024 * 1024  # 45 ميجابايت

    # دالة داخلية لالتقاط النسبة المئوية من yt_dlp وإرسالها للبوت
    def hook(d):
        if d['status'] == 'downloading' and progress_callback:
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 1)
            downloaded = d.get('downloaded_bytes', 0)
            if total > 1:
                percent = (downloaded / total) * 100
                progress_callback(percent)

    # إعدادات عامة لتجاوز حظر يوتيوب ومواقع السوشيال ميديا
    common_opts = {
        'geo_bypass': True,
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': max_size_bytes,
        'socket_timeout': 30,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-us,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        }
    }

    if media_type == 'video':
        ydl_opts = {
            **common_opts,
            'format': 'bestvideo[ext=mp4][filesize<=45M]+bestaudio[ext=m4a]/best[ext=mp4][filesize<=45M]/best[filesize<=45M]/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
        }
    else: 
        ydl_opts = {
            **common_opts,
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

    # إضافة العداد إذا تم تمريره
    if progress_callback:
        ydl_opts['progress_hooks'] = [hook]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # تصحيح الامتداد النهائي بدقة عالية
            if media_type == 'audio':
                base_name = os.path.splitext(filename)[0]
                filename = base_name + '.mp3'
            elif media_type == 'video':
                base_name = os.path.splitext(filename)[0]
                if not os.path.exists(filename) and os.path.exists(base_name + '.mp4'):
                    filename = base_name + '.mp4'
                elif not filename.endswith('.mp4'):
                    filename = base_name + '.mp4'
                
            return filename
            
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e).lower()
        if 'file is larger than max-filesize' in error_msg or 'filesize' in error_msg:
            return "TOO_LARGE"
        elif 'not available' in error_msg or 'unavailable' in error_msg:
            return "UNAVAILABLE"
        print(f"yt_dlp Error: {e}")
        return None
    except Exception as e:
        print(f"General Error: {e}")
        return None

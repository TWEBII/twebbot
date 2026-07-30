import yt_dlp
import os

# إنشاء مجلد للتحميلات إذا لم يكن موجوداً لتجنب الأخطاء
if not os.path.exists('downloads'):
    os.makedirs('downloads')

def get_video_info(url):
    """
    دالة لاستخراج تفاصيل المقطع قبل التحميل لعرضها للمستخدم
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'extract_flat': False,
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

    if media_type == 'video':
        ydl_opts = {
            # إعدادات مرنة جداً لدعم تيك توك ويوتيوب معاً
            'format': 'bestvideo[ext=mp4][filesize<=45M]+bestaudio[ext=m4a]/best[ext=mp4][filesize<=45M]/best[filesize<=45M]/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'merge_output_format': 'mp4',
            'geo_bypass': True,
            'nocheckcertificate': True,
            'quiet': True,
            'no_warnings': True,
            'max_filesize': max_size_bytes,
        }
    else: 
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3', # MP3 أفضل وأكثر استقراراً من m4a
            }],
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'max_filesize': max_size_bytes,
        }

    # إضافة العداد إذا تم تمريره
    if progress_callback:
        ydl_opts['progress_hooks'] = [hook]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # تصحيح الامتداد النهائي
            if media_type == 'audio':
                filename = filename.rsplit('.', 1)[0] + '.mp3'
            elif media_type == 'video' and not filename.endswith('.mp4'):
                filename = filename.rsplit('.', 1)[0] + '.mp4'
                
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

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

def download_media(url, media_type='video'):
    """
    دالة لتحميل الفيديو أو الصوت بشكل آمن ومتوافق مع تيليجرام
    مع قيد أقصى للحجم (45 ميجابايت)
    """
    max_size_bytes = 45 * 1024 * 1024  # 45 ميجابايت

    if media_type == 'video':
        ydl_opts = {
            # إجبار المكتبة على البحث عن صيغ لا تتجاوز 45 ميجا
            'format': 'bestvideo[ext=mp4][filesize<=45M]+bestaudio[ext=m4a]/best[ext=mp4][filesize<=45M]/best[filesize<=45M]',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'merge_output_format': 'mp4',
            'geo_bypass': True,
            'nocheckcertificate': True,
            'quiet': True,
            'no_warnings': True,
            'max_filesize': max_size_bytes, # إيقاف فوري إذا تجاوز 45 ميجا
        }
    else: # في حالة اختيار الصوت
        ydl_opts = {
            'format': 'bestaudio[filesize<=45M]/best[filesize<=45M]',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
            }],
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
            'max_filesize': max_size_bytes,
        }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            # تصحيح الامتداد النهائي لضمان قبوله في تيليجرام
            if media_type == 'audio' and not filename.endswith('.m4a'):
                filename = filename.rsplit('.', 1)[0] + '.m4a'
            elif media_type == 'video' and not filename.endswith('.mp4'):
                filename = filename.rsplit('.', 1)[0] + '.mp4'
                
            return filename
            
    except yt_dlp.utils.DownloadError as e:
        if 'File is larger than max-filesize' in str(e) or 'filesize' in str(e).lower():
            print("حجم الملف يتجاوز 45 ميجابايت.")
            return "TOO_LARGE"
        print(f"Error downloading: {e}")
        return None
    except Exception as e:
        print(f"Error downloading: {e}")
        return None

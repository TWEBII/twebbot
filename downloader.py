import yt_dlp
import os

# إنشاء مجلد للتحميلات إذا لم يكن موجوداً لتجنب الأخطاء
if not os.path.exists('downloads'):
    os.makedirs('downloads')

def download_media(url, media_type='video'):
    """
    دالة لتحميل الفيديو أو الصوت بشكل آمن ومتوافق مع تيليجرام
    """
    if media_type == 'video':
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'merge_output_format': 'mp4', # إجبار الدمج بصيغة mp4 لحل مشكلة تيك توك
            'geo_bypass': True,
            'nocheckcertificate': True,
            'quiet': True,
            'no_warnings': True,
        }
    else: # في حالة اختيار الصوت
        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'm4a',
            }],
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
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
    except Exception as e:
        print(f"Error downloading: {e}")
        return None

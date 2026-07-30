import yt_dlp
import os

if not os.path.exists('downloads'):
    os.makedirs('downloads')

def get_video_info(url):
    """
    استخراج مبسط جداً لتفاصيل الفيديو لتجنب الحظر
    """
    # إذا كان الرابط يوتيوب، نتجاوز جلب التفاصيل المسبق لمنع حظر البوت ونترك التحميل المباشر يتولى الأمر
    if 'youtube.com' in url or 'youtu.be' in url:
        return {'title': 'YouTube Video', 'duration': 0, 'id': url.split('/')[-1].split('?')[0]}

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'socket_timeout': 10,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        print(f"Error fetching info: {e}")
        # إرجاع بيانات افتراضية حتى لا يتوقف البوت أبداً
        return {'title': 'Media', 'id': 'temp_id'}

def download_media(url, media_type='video', progress_callback=None):
    max_size_bytes = 45 * 1024 * 1024  # 45 ميجابايت

    def hook(d):
        if d['status'] == 'downloading' and progress_callback:
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 1)
            downloaded = d.get('downloaded_bytes', 0)
            if total > 1:
                percent = (downloaded / total) * 100
                progress_callback(percent)

    ydl_opts = {
        'geo_bypass': True,
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': max_size_bytes,
        'socket_timeout': 30,
        # استخدام مشغل الـ ios أو android لتجاوز قيود يوتيوب وتيك توك بدون أخطاء
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 16_6 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/16.6 Mobile/15E148 Safari/604.1',
        }
    }

    if media_type == 'video':
        ydl_opts.update({
            'format': 'best[filesize<=45M]/bestvideo+bestaudio/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
        })
    else: 
        ydl_opts.update({
            'format': 'best/bestaudio/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        })

    if progress_callback:
        ydl_opts['progress_hooks'] = [hook]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            
            if media_type == 'audio':
                base_name = os.path.splitext(filename)[0]
                mp3_file = base_name + '.mp3'
                if os.path.exists(mp3_file):
                    return mp3_file
                for f in os.listdir('downloads'):
                    if f.endswith('.mp3'):
                        return os.path.join('downloads', f)
                return filename.rsplit('.', 1)[0] + '.mp3'
            else:
                base_name = os.path.splitext(filename)[0]
                mp4_file = base_name + '.mp4'
                if os.path.exists(mp4_file):
                    return mp4_file
                return filename
            
    except Exception as e:
        print(f"Download Error: {e}")
        return None

import yt_dlp
import os

if not os.path.exists('downloads'):
    os.makedirs('downloads')

def get_video_info(url):
    """
    استخراج بيانات الفيديو مع تجاوز حظر يوتيوب وتيك توك
    """
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'extract_flat': False,
        'socket_timeout': 15,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
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
    تحميل الوسائط (يوتيوب وتيك توك) بفيديو أو صوت بدقة واستقرار كاملين
    """
    max_size_bytes = 45 * 1024 * 1024  # 45 ميجابايت

    def hook(d):
        if d['status'] == 'downloading' and progress_callback:
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 1)
            downloaded = d.get('downloaded_bytes', 0)
            if total > 1:
                percent = (downloaded / total) * 100
                progress_callback(percent)

    common_opts = {
        'geo_bypass': True,
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': max_size_bytes,
        'socket_timeout': 25,
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'web']
            }
        },
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        }
    }

    if media_type == 'video':
        ydl_opts = {
            **common_opts,
            'format': 'best[filesize<=45M]/bestvideo+bestaudio/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
        }
    else: 
        # إعدادات مخصصة لاستخراج الصوت من تيك توك ويوتيوب بأمان تام
        ydl_opts = {
            **common_opts,
            'format': 'best/bestaudio/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
        }

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
                # البحث الذكي عن أي ملف mp3 تم توليده بالمعرف الخاص بالفيديو
                video_id = info.get('id', '')
                for f in os.listdir('downloads'):
                    if f.startswith(str(video_id)) and f.endswith('.mp3'):
                        return os.path.join('downloads', f)
                return filename.rsplit('.', 1)[0] + '.mp3'
            else:
                base_name = os.path.splitext(filename)[0]
                mp4_file = base_name + '.mp4'
                if os.path.exists(mp4_file):
                    return mp4_file
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

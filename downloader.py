import os
import yt_dlp

if not os.path.exists('downloads'):
    os.makedirs('downloads')

def resolve_url(url):
    # ترك معالجة وتوجيه الروابط بالكامل لمكتبة yt-dlp مع الـ Headers المخصصة
    return url

def get_video_info(url):
    common_opts = {
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'socket_timeout': 15,
        'extractor_args': {'youtube': {'player_client': ['android', 'ios']}},
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.tiktok.com/',
        }
    }

    try:
        with yt_dlp.YoutubeDL(common_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        print(f"Error fetching info: {e}")
        return {'title': 'Media', 'id': 'temp_id'}

def download_media(url, media_type='video', progress_callback=None):
    max_size_bytes = 50 * 1024 * 1024  # 50 ميجابايت كحد أقصى لتليجرام

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
        'socket_timeout': 30,
        'extractor_args': {'youtube': {'player_client': ['android', 'ios', 'web']}},
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.tiktok.com/',
        }
    }

    if media_type == 'audio':
        ydl_opts = {
            **common_opts,
            'format': 'bestaudio[ext=m4a]/bestaudio/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
        }
    else:
        ydl_opts = {
            **common_opts,
            'format': 'best[ext=mp4]/best/worst',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
        }

    if progress_callback:
        ydl_opts['progress_hooks'] = [hook]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            final_path = filename
            
            if media_type != 'audio':
                base_name = os.path.splitext(filename)[0]
                mp4_file = base_name + '.mp4'
                if os.path.exists(mp4_file):
                    final_path = mp4_file
            
            if os.path.exists(final_path):
                file_size = os.path.getsize(final_path)
                if file_size > max_size_bytes:
                    os.remove(final_path)
                    print(f"File size exceeds 50MB limit.")
                    return None
                return final_path
                
            return None
    except Exception as e:
        print(f"Download Error: {e}")
        return None

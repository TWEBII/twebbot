import yt_dlp
import os
import urllib.request

if not os.path.exists('downloads'):
    os.makedirs('downloads')

def resolve_url(url):
    if 'vm.tiktok.com' in url or 'vt.tiktok.com' in url:
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36'}
            )
            with urllib.request.urlopen(req, timeout=10) as response:
                return response.url
        except Exception as e:
            print(f"Error resolving URL: {e}")
    return url

def get_video_info(url):
    resolved_url = resolve_url(url)
    if 'youtube.com' in resolved_url or 'youtu.be' in resolved_url:
        return {'title': 'YouTube Video', 'duration': 0, 'id': resolved_url.split('/')[-1].split('?')[0]}
    
    if 'tiktok.com' in resolved_url:
        return {'title': 'TikTok Video', 'duration': 0, 'id': 'tiktok_id'}

    if 'instagram.com' in resolved_url:
        return {'title': 'Instagram Media', 'duration': 0, 'id': 'insta_id'}

    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'geo_bypass': True,
        'nocheckcertificate': True,
        'socket_timeout': 10,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(resolved_url, download=False)
            return info
    except Exception as e:
        print(f"Error fetching info: {e}")
        return {'title': 'Media', 'id': 'temp_id'}

def download_media(url, media_type='video', progress_callback=None):
    max_size_bytes = 45 * 1024 * 1024  # 45 ميجابايت

    real_url = resolve_url(url)

    def hook(d):
        if d['status'] == 'downloading' and progress_callback:
            total = d.get('total_bytes') or d.get('total_bytes_estimate', 1)
            downloaded = d.get('downloaded_bytes', 0)
            if total > 1:
                percent = (downloaded / total) * 100
                progress_callback(percent)

    is_tiktok = 'tiktok.com' in real_url
    is_insta = 'instagram.com' in real_url
    is_youtube = 'youtube.com' in real_url or 'youtu.be' in real_url

    common_opts = {
        'geo_bypass': True,
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': max_size_bytes,
        'socket_timeout': 30,
    }

    if is_youtube:
        # استخدام مشغل الأندرويد لتجاوز حماية البوتات تماماً بدون كوكيز
        common_opts.update({
            'extractor_args': {
                'youtube': {
                    'player_client': ['android', 'web']
                }
            },
            'http_headers': {
                'User-Agent': 'com.google.android.youtube/19.29.35 (Linux; U; Android 14; 23117RK6CB) gzip',
            }
        })
    elif is_tiktok:
        common_opts.update({
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
                'Referer': 'https://www.tiktok.com/',
            }
        })
    elif is_insta:
        common_opts.update({
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Referer': 'https://www.instagram.com/',
            }
        })

    if is_tiktok or is_insta:
        ydl_opts = {
            **common_opts,
            'format': 'best[filesize<=45M]/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
        }
    else:
        if media_type == 'video':
            ydl_opts = {
                **common_opts,
                'format': 'best[filesize<=45M]/bestvideo+bestaudio/best',
                'outtmpl': 'downloads/%(id)s.%(ext)s',
                'merge_output_format': 'mp4',
            }
        else: 
            ydl_opts = {
                **common_opts,
                'format': 'bestaudio/best',
                'outtmpl': 'downloads/%(id)s.%(ext)s',
            }

    if progress_callback:
        ydl_opts['progress_hooks'] = [hook]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(real_url, download=True)
            filename = ydl.prepare_filename(info)
            
            if media_type == 'audio':
                base_name = os.path.splitext(filename)[0]
                for ext in ['.mp3', '.m4a', '.webm', '.aac', '.opus', '.mp4']:
                    candidate = base_name + ext
                    if os.path.exists(candidate):
                        return candidate
                
                video_id = info.get('id', '')
                for f in os.listdir('downloads'):
                    if str(video_id) in f:
                        return os.path.join('downloads', f)
                return filename
            else:
                base_name = os.path.splitext(filename)[0]
                mp4_file = base_name + '.mp4'
                if os.path.exists(mp4_file):
                    return mp4_file
                return filename
            
    except Exception as e:
        print(f"Download Error: {e}")
        return None

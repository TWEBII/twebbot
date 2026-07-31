import yt_dlp
import os
import urllib.request
import json

if not os.path.exists('downloads'):
    os.makedirs('downloads')

def resolve_url(url):
    if 'vm.tiktok.com' in url or 'vt.tiktok.com' in url:
        try:
            req = urllib.request.Request(
                url,
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
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
    max_size_bytes = 50 * 1024 * 1024  # 50 ميجابايت كحد أقصى لتليجرام
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

    # معالجة يوتيوب والـ Shorts عبر واجهة السحب المباشرة
    if is_youtube:
        try:
            api_url = f"https://co.wuk.sh/api/json"
            data = json.dumps({
                "url": real_url,
                "isAudioOnly": True if media_type == 'audio' else False
            }).encode('utf-8')
            
            req = urllib.request.Request(
                api_url,
                data=data,
                headers={
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'
                }
            )
            
            with urllib.request.urlopen(req, timeout=15) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                if 'url' in res_data:
                    download_url = res_data['url']
                    ext = 'mp3' if media_type == 'audio' else 'mp4'
                    file_path = f"downloads/youtube_media.{ext}"
                    
                    urllib.request.urlretrieve(download_url, file_path)
                    if os.path.exists(file_path):
                        # التحقق من أن حجم الملف لا يتجاوز 50 ميجابايت
                        if os.path.getsize(file_path) > max_size_bytes:
                            os.remove(file_path)
                            print("Error: File exceeds 50MB limit even at lowest quality.")
                            return None
                        return file_path
        except Exception as e:
            print(f"Alternative API Error: {e}")

    common_opts = {
        'geo_bypass': True,
        'nocheckcertificate': True,
        'quiet': True,
        'no_warnings': True,
        'max_filesize': max_size_bytes,
        'socket_timeout': 30,
    }

    if is_tiktok:
        common_opts.update({
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Referer': 'https://www.tiktok.com/',
            }
        })
    elif is_insta:
        common_opts.update({
            'http_headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                'Referer': 'https://www.instagram.com/',
            }
        })

    ydl_opts = {
        **common_opts,
        'format': 'best[filesize<=50M]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
    }

    if progress_callback:
        ydl_opts['progress_hooks'] = [hook]

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(real_url, download=True)
            filename = ydl.prepare_filename(info)
            base_name = os.path.splitext(filename)[0]
            mp4_file = base_name + '.mp4'
            final_path = mp4_file if os.path.exists(mp4_file) else filename
            
            if os.path.exists(final_path) and os.path.getsize(final_path) > max_size_bytes:
                os.remove(final_path)
                return None
                
            return final_path
    except Exception as e:
        print(f"Download Error: {e}")
        return None

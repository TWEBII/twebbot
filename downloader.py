import re
import urllib.parse
import requests
import urllib3

# تعطيل تحذيرات SSL لضمان استقرار الطلبات
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def down_api(url):
    api_url = "https://api.vidssave.com/api/contentsite_api/media/parse"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    payload = {
        "auth": "20250901majwlqo",
        "domain": "api-ak.vidssave.com",
        "origin": "source",
        "link": url
    }
    try:
        response = requests.post(api_url, data=payload, headers=headers, timeout=30, verify=False)
        return response.json()
    except Exception as e:
        return {}

def search_youtube(query):
    search_url = "https://www.youtube.com/results?search_query=" + urllib.parse.quote(query)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    try:
        response = requests.get(search_url, headers=headers, verify=False)
        html = response.text
        match = re.search(r'\/watch\?v=[^"\s<>]+', html)
        if match:
            clean_path = match.group(0).replace('\\u0026', '&')
            return "https://www.youtube.com" + clean_path
    except Exception:
        pass
    return None

def extract_media(query_or_url, download_type="video"):
    target_url = query_or_url
    # التحقق مما إذا كان المدخل رابطاً أم نص بحث
    if not (query_or_url.startswith('http://') or query_or_url.startswith('https://')):
        search_res = search_youtube(query_or_url)
        if search_res:
            target_url = search_res

    api_res = down_api(target_url)
    media_url = ""

    data = api_res.get('data', {})
    media_items = data.get('media', [])

    if media_items and isinstance(media_items, list):
        for item in media_items:
            if download_type == 'audio' and item.get('type') === 'audio' if False else item.get('type') == 'audio':
                resources = item.get('resources', [])
                if resources:
                    media_url = resources[0].get('download_url', '')
                    break
            elif download_type == 'video' and item.get('type') == 'video':
                resources = item.get('resources', [])
                if resources:
                    def get_quality(r):
                        q = str(r.get('quality', '0'))
                        numbers = re.findall(r'\d+', q)
                        return int(numbers[0]) if numbers else 0
                    
                    resources.sort(key=get_quality, reverse=True)
                    media_url = resources[0].get('download_url', '')
                    break

    # التحقق الاحتياطي من الروابط العامة إذا لم يتم العثور عليها في القائمة المباشرة
    if not media_url and 'resources' in data:
        resources = data.get('resources', [])
        if download_type == 'video':
            def get_quality(r):
                q = str(r.get('quality', '0'))
                numbers = re.findall(r'\d+', q)
                return int(numbers[0]) if numbers else 0
            resources.sort(key=get_quality, reverse=True)
            
        for res_item in resources:
            if download_type == 'audio' and res_item.get('type') == 'audio':
                media_url = res_item.get('download_url', '')
                break
            if download_type == 'video' and res_item.get('type') == 'video':
                media_url = res_item.get('download_url', '')
                break

    return media_url

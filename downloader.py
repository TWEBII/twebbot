import os
import re
import yt_dlp

def extract_clean_url(text):
    """استخراج الرابط النظيف حصراً من أي نص مرسل (مثل رسائل مشاركة تيك توك)"""
    url_match = re.search(r'https?://[^\s]+', text)
    if url_match:
        # إزالة أي رموز إضافية قد تكون ملتصقة بنهاية الرابط مثل علامة التعجب أو الفاصلة
        return url_match.group(0).rstrip('!#.,;')
    return text

def download_video(input_text):
    """
    دالة محدثة لتحميل الفيديو مع استخراج الرابط تلقائياً وضبط الجودة لتناسب حدود تلغرام
    """
    url = extract_clean_url(input_text)
    
    ydl_opts = {
        # تقييد الجودة إلى 720p كحد أقصى لضمان عدم تجاوز حجم الملف 50 ميجابايت لفيديو مدته 5 دقائق
        'format': 'bestvideo[height<=720]+bestaudio/best[height<=720]/best',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'noplaylist': True,
        'socket_timeout': 30,
        'merge_output_format': 'mp4',
    }
    
    # إنشاء مجلد التحميل إن لم يكن موجوداً
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
            # التأكد من أن صيغة الملف أصبحت mp4 بعد الدمج
            if not file_path.endswith('.mp4') and os.path.exists(file_path.rsplit('.', 1)[0] + '.mp4'):
                file_path = file_path.rsplit('.', 1)[0] + '.mp4'
            return file_path
            
    except Exception as e:
        print(f"❌ Download Error: {e}")
        return None

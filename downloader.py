import os
import yt_dlp

def download_video(url):
    """
    دالة موحدة للتحميل من جميع منصات التواصل الاجتماعي مع إضافة عداد نسبة التحميل (0% إلى 100%)
    """
    
    # دالة فرعية لالتقاط نسبة التحميل وطباعتها كعداد مئوي
    def progress_hook(d):
        if d['status'] == 'downloading':
            # استخراج النسبة المئوية للتحميل إذا توفرت
            percent_str = d.get('_percent_str', '0%').strip()
            # إزالة الرموز الزائدة مثل الألوان أو علامة النسبة للحصول على الرقم الصافي إن أمكن
            print(f"📥 جاري التحميل: {percent_str}")
        elif d['status'] == 'finished':
            print("✅ تم الانتهاء من التحميل، جاري معالجة ودمج الملف...")

    ydl_opts = {
        'format': 'best/bestvideo+bestaudio',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'noplaylist': True,
        'socket_timeout': 30,
        'merge_output_format': 'mp4',
        'progress_hooks': [progress_hook],  # ربط دالة العداد بعملية التحميل
    }
    
    # إنشاء مجلد مؤقت للتحميل إن لم يكن موجوداً
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

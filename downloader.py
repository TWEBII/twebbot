import os
import yt_dlp

def download_video(url, bot, chat_id, message_id):
    """
    دالة التحميل مع تحديث عداد نسبة التحميل (من 1% إلى 100%) مباشرة في رسالة تليجرام
    """
    
    def progress_hook(d):
        if d['status'] == 'downloading':
            percent_str = d.get('_percent_str', '0%').strip()
            # إزالة الرموز الزائدة للحصول على النسبة الصافية
            clean_percent = percent_str.replace('%', '').strip()
            try:
                p_int = int(float(clean_percent))
                # رسم شريط تقدم بسيط مع النسبة
                bar_filled = '█' * (p_int // 10) + '░' * (10 - (p_int // 10))
                text = f"⏳ جاري التحميل...\n\n[{bar_filled}] {p_int}%\nيرجى الانتظار قريباً..."
                
                # تحديث الرسالة في تليجرام (تجنب الأخطاء إذا كان النص متطابقاً)
                bot.edit_message_text(text, chat_id=chat_id, message_id=message_id)
            except Exception:
                pass
                
        elif d['status'] == 'finished':
            bot.edit_message_text("✅ تم الانتهاء من التحميل، جاري معالجة ورفع الملف...", chat_id=chat_id, message_id=message_id)

    ydl_opts = {
        'format': 'best/bestvideo+bestaudio',
        'outtmpl': 'downloads/%(id)s.%(ext)s',
        'noplaylist': True,
        'socket_timeout': 30,
        'merge_output_format': 'mp4',
        'progress_hooks': [progress_hook],
    }
    
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
        
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            if not file_path.endswith('.mp4') and os.path.exists(file_path.rsplit('.', 1)[0] + '.mp4'):
                file_path = file_path.rsplit('.', 1)[0] + '.mp4'
            return file_path
    except Exception as e:
        print(f"❌ Download Error: {e}")
        return None

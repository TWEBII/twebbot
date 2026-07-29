import io
import os
import threading
from flask import Flask, request, render_template_string, jsonify
from groq import Groq
import telebot
from PIL import Image
import pytesseract
import numpy as np

# إعدادات البوت والربط الثابتة
GROQ_API_KEY = "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"
TELEGRAM_BOT_TOKEN = "8665200275:AAGsRxks0nJWtYySayDcY1rROPtHvRtVS-s"
ADMIN_CHAT_ID = 8411608232
ADMIN_USERNAME = "@TWEBii"
RAILWAY_URL = "https://twebbot-production.up.railway.app"

users_db = set()
total_messages_sent = 0

custom_start_message = (
    "هلا بيك أحمد. أنا تويبي (Tweby)، مساعدك الشخصي.\n\n"
    "🌐 تم تفعيل متصفح **TWEB** المتكامل بالداخل لترجمة الصور والمستندات بدقة مطابقة لجوجل تماماً، وتم إيقاف الترجمة التلقائية داخل محادثة البوت.\n"
    "اضغط على الزر أدناه لفتح المتصفح:"
)

client = Groq(api_key=GROQ_API_KEY)
bot = telebot.TeleBot(TELEGRAM_BOT_TOKEN)
server = Flask(__name__)


def set_bot_commands():
    try:
        bot.set_my_commands([types.BotCommand("start", "القائمة الرئيسية")])
    except Exception:
        pass


@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    users_db.add(user_id)
    
    markup = types.InlineKeyboardMarkup()
    web_app = types.WebAppInfo(url=f"{RAILWAY_URL}/webapp")
    markup.add(types.InlineKeyboardButton("🌐 فتح متصفح TWEB للترجمة", web_app=web_app))
    
    bot.reply_to(message, custom_start_message, parse_mode="Markdown", reply_markup=markup)


# منع البوت نهائياً من الترجمة داخل المحادثة وتوجيه المستخدم للمتصفح
@bot.message_handler(content_types=['photo', 'document'])
def handle_restricted_media(message):
    markup = types.InlineKeyboardMarkup()
    web_app = types.WebAppInfo(url=f"{RAILWAY_URL}/webapp")
    markup.add(types.InlineKeyboardButton("🌐 فتح متصفح TWEB", web_app=web_app))
    bot.reply_to(message, "⚠️ تم إيقاف الترجمة داخل المحادثة بناءً على طلبك.\nيرجى استخدام متصفح **TWEB** بالأسفل لرفع الصور أو الملفات وترجمتها بدقة.", reply_markup=markup)


@server.route("/webapp")
def webapp_view():
    html_template = """
    <!DOCTYPE html>
    <html lang="ar" dir="rtl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>TWEB Translate</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8f9fa; margin: 0; padding: 0; color: #202124; }
            header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid #dadce0; background: #fff; }
            .logo { font-weight: bold; font-size: 18px; color: #1a73e8; display: flex; align-items: center; gap: 8px; }
            .tabs { display: flex; justify-content: space-around; padding: 10px; background: #fff; border-bottom: 1px solid #dadce0; }
            .tab { padding: 8px 16px; border-radius: 20px; background: transparent; color: #5f6368; font-size: 14px; font-weight: 500; cursor: pointer; border: none; transition: 0.2s; }
            .tab.active { background: #e8f0fe; color: #1a73e8; }
            .lang-bar { display: flex; justify-content: space-between; align-items: center; padding: 15px; background: #fff; font-weight: 500; border-bottom: 1px solid #dadce0; font-size: 14px; }
            .content-box { padding: 40px 20px; text-align: center; }
            .upload-btn { background: #1a73e8; color: white; border: none; padding: 12px 28px; border-radius: 4px; font-size: 16px; font-weight: 500; cursor: pointer; margin-top: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }
            .upload-btn:active { background: #1557b0; }
            input[type="file"] { display: none; }
            .footer-info { margin-top: 30px; font-size: 13px; color: #5f6368; }
            #loading { display: none; margin-top: 20px; color: #1a73e8; font-weight: bold; }
            #result-container { margin-top: 20px; padding: 15px; background: #fff; border-radius: 8px; text-align: right; box-shadow: 0 1px 3px rgba(0,0,0,0.1); display: none; }
        </style>
    </head>
    <body>
        <header>
            <div class="logo">🌐 TWEB Translate</div>
        </header>
        <div class="tabs">
            <button class="tab" id="tab-doc" onclick="switchTab('doc')">📄 المستندات</button>
            <button class="tab active" id="tab-img" onclick="switchTab('img')">🖼 صور</button>
            <button class="tab" id="tab-web" onclick="switchTab('web')">🌐 مواقع</button>
        </div>
        <div class="lang-bar">
            <span>التعرّف التلقائي على اللغة</span>
            <span>⇄</span>
            <span>العربية</span>
        </div>
        <div class="content-box">
            <h3 id="instruction-text">اختر صورة أو ملفاً للترجمة.</h3>
            <label class="upload-btn">
                تصفُّح الملفات والصور
                <input type="file" id="fileInput" accept="image/*,.pdf" onchange="uploadFile()">
            </label>
            <div id="loading">⏳ جاري معالجة الترجمة بدقة عالية...</div>
            <div id="result-container">
                <h4>نتيجة الترجمة:</h4>
                <p id="result-text" style="white-space: pre-wrap; font-size: 15px;"></p>
            </div>
            <div class="footer-info">
                أنواع الملفات المتوافقة: الصور و .pdf<br><br>
                <span>مطور بواسطة TWEB</span>
            </div>
        </div>

        <script>
            function switchTab(tab) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                if(tab === 'img') document.getElementById('tab-img').classList.add('active');
                if(tab === 'doc') document.getElementById('tab-doc').classList.add('active');
                if(tab === 'web') document.getElementById('tab-web').classList.add('active');
            }

            function uploadFile() {
                const fileInput = document.getElementById('fileInput');
                if (fileInput.files.length === 0) return;
                
                const formData = new FormData();
                formData.append('file', fileInput.files[0]);

                document.getElementById('loading').style.display = 'block';
                document.getElementById('result-container').style.display = 'none';

                fetch('/api/translate', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('loading').style.display = 'none';
                    if(data.success) {
                        document.getElementById('result-text').innerText = data.translation;
                        document.getElementById('result-container').style.display = 'block';
                    } else {
                        alert('حدث خطأ: ' + data.error);
                    }
                })
                .catch(err => {
                    document.getElementById('loading').style.display = 'none';
                    alert('خطأ في الاتصال بالخادم');
                });
            }
        </script>
    </body>
    </html>
    """
    return render_template_string(html_template)


@server.route("/api/translate", methods=['POST'])
def api_translate():
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'لم يتم إرسال ملف'})
        
        file = request.files['file']
        file_bytes = file.read()
        
        # تحليل الصورة واستخراج النصوص وترجمتها عبر Llama / Tesseract داخل المتصفح حصراً
        img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
        text = pytesseract.image_to_string(img)
        
        if not text.strip():
            return jsonify({'success': True, 'translation': 'لم يتم العثور على نص واضح داخل الصورة.'})
            
        prompt = f"Translate the following English text into professional Arabic. Return ONLY the translated text:\n{text}"
        chat_completion = client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model="llama-3.3-70b-versatile",
            temperature=0.1
        )
        translated_text = chat_completion.choices[0].message.content.strip()
        
        return jsonify({'success': True, 'translation': translated_text})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@server.route(f'/{TELEGRAM_BOT_TOKEN}', methods=['POST'])
def redirect_message():
    json_string = request.get_data().decode('utf-8')
    update = types.Update.de_json(json_string)
    threading.Thread(target=bot.process_new_updates, args=([update],)).start()
    return "!", 200

@server.route("/")
def index():
    return "TWEB WebApp Translate Running Smoothly!", 200

if __name__ == "__main__":
    print("جاري بدء تشغيل البوت...")
    set_bot_commands()
    
    try:
        bot.remove_webhook()
        bot.set_webhook(url=f"{RAILWAY_URL}/{TELEGRAM_BOT_TOKEN}")
    except Exception as e:
        print(f"Webhook error: {e}")
        
    port = int(os.environ.get("PORT", 8080))
    server.run(host='0.0.0.0', port=port)

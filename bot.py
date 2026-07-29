import io
import os
import threading
from flask import Flask, request, render_template_string, jsonify
from groq import Groq
import telebot
from telebot import types
from PIL import Image
import pytesseract
import fitz  # PyMuPDF
import numpy as np
import base64

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
    "🌐 تم تفعيل متصفح **TWEB** المتكامل بالداخل لترجمة الصور والمستندات بنفس واجهة ودقة مترجم جوجل تماماً، وتم إيقاف الترجمة التلقائية داخل محادثة البوت.\n"
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
        <title>ترجمة TWEB</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background-color: #f8f9fa; margin: 0; padding: 0; color: #202124; }
            header { display: flex; justify-content: space-between; align-items: center; padding: 12px 16px; border-bottom: 1px solid #dadce0; background: #fff; }
            .logo { font-weight: bold; font-size: 18px; color: #1a73e8; display: flex; align-items: center; gap: 8px; }
            .tabs { display: flex; justify-content: space-around; padding: 10px; background: #fff; border-bottom: 1px solid #dadce0; }
            .tab { padding: 8px 16px; border-radius: 20px; background: transparent; color: #5f6368; font-size: 14px; font-weight: 500; cursor: pointer; border: none; transition: 0.2s; }
            .tab.active { background: #e8f0fe; color: #1a73e8; }
            .lang-bar { display: flex; justify-content: space-between; align-items: center; padding: 15px; background: #fff; font-weight: 500; border-bottom: 1px solid #dadce0; font-size: 14px; }
            .content-box { padding: 20px; text-align: center; }
            .upload-btn { background: #1a73e8; color: white; border: none; padding: 12px 28px; border-radius: 4px; font-size: 16px; font-weight: 500; cursor: pointer; margin-top: 15px; box-shadow: 0 1px 3px rgba(0,0,0,0.2); display: inline-block; }
            .upload-btn:active { background: #1557b0; }
            input[type="file"] { display: none; }
            
            /* تصميم شبيه بمترجم جوجل للصور */
            .google-view { display: none; margin-top: 15px; background: #202124; border-radius: 8px; overflow: hidden; position: relative; box-shadow: 0 1px 3px rgba(0,0,0,0.2); }
            .image-container { position: relative; width: 100%; max-height: 400px; display: flex; justify-content: center; align-items: center; overflow: hidden; }
            .image-container img { width: 100%; height: auto; object-fit: contain; transition: opacity 0.3s; }
            
            .controls-bar { display: flex; justify-content: space-between; align-items: center; background: #fff; padding: 10px 15px; border-top: 1px solid #dadce0; }
            .switch-container { display: flex; align-items: center; gap: 8px; font-size: 14px; color: #5f6368; }
            
            /* زر التبديل (Switch) شبيه بجوجل */
            .switch { position: relative; display: inline-block; width: 44px; height: 24px; }
            .switch input { opacity: 0; width: 0; height: 0; }
            .slider { position: absolute; cursor: pointer; top: 0; left: 0; right: 0; bottom: 0; background-color: #5f6368; transition: .3s; border-radius: 24px; }
            .slider:before { position: absolute; content: ""; height: 18px; width: 18px; left: 3px; bottom: 3px; background-color: white; transition: .3s; border-radius: 50%; }
            input:checked + .slider { background-color: #1a73e8; }
            input:checked + .slider:before { transform: translateX(20px); }

            .text-result-box { padding: 20px; background: #fff; text-align: right; border-top: 1px solid #dadce0; display: none; }
            .footer-info { margin-top: 30px; font-size: 13px; color: #5f6368; }
            #loading { display: none; margin-top: 20px; color: #1a73e8; font-weight: bold; }
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
            <div id="upload-section">
                <h3>اختر صورة أو ملفاً (PDF) للترجمة.</h3>
                <label class="upload-btn">
                    تصفُّح الملفات والصور
                    <input type="file" id="fileInput" accept="image/*,.pdf" onchange="uploadFile()">
                </label>
            </div>

            <div id="loading">⏳ جاري معالجة وترجمة الملف بنفس دقة جوجل...</div>

            <!-- واجهة شبيهة بمترجم جوجل -->
            <div class="google-view" id="googleView">
                <div class="image-container">
                    <img id="previewImage" src="" alt="Uploaded Image">
                </div>
                <div class="controls-bar">
                    <button class="upload-btn" style="margin:0; padding: 6px 14px; font-size: 13px;" onclick="document.getElementById('fileInput').click()">صورة أخرى</button>
                    <div class="switch-container">
                        <span>عرض النص الأصلي</span>
                        <label class="switch">
                            <input type="checkbox" id="toggleOriginal" checked onchange="toggleOriginalView()">
                            <span class="slider"></span>
                        </label>
                    </div>
                </div>
            </div>

            <div class="text-result-box" id="textResultBox">
                <h4>نتيجة الترجمة:</h4>
                <p id="result-text" style="white-space: pre-wrap; font-size: 15px; line-height: 1.6;"></p>
            </div>

            <div class="footer-info">
                أنواع الملفات المتوافقة: الصور و .pdf<br><br>
                <span>مطور بواسطة TWEB</span>
            </div>
        </div>

        <script>
            let originalFileUrl = "";

            function switchTab(tab) {
                document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
                if(tab === 'img') document.getElementById('tab-img').classList.add('active');
                if(tab === 'doc') document.getElementById('tab-doc').classList.add('active');
                if(tab === 'web') document.getElementById('tab-web').classList.add('active');
            }

            function toggleOriginalView() {
                const isChecked = document.getElementById('toggleOriginal').checked;
                const imgElem = document.getElementById('previewImage');
                imgElem.style.opacity = isChecked ? "1" : "0.2";
            }

            function uploadFile() {
                const fileInput = document.getElementById('fileInput');
                if (fileInput.files.length === 0) return;
                
                const file = fileInput.files[0];
                originalFileUrl = URL.createObjectURL(file);
                
                const formData = new FormData();
                formData.append('file', file);

                document.getElementById('upload-section').style.display = 'none';
                document.getElementById('loading').style.display = 'block';
                document.getElementById('googleView').style.display = 'none';
                document.getElementById('textResultBox').style.display = 'none';

                fetch('/api/translate', {
                    method: 'POST',
                    body: formData
                })
                .then(response => response.json())
                .then(data => {
                    document.getElementById('loading').style.display = 'none';
                    if(data.success) {
                        if(file.type.startsWith('image/')) {
                            document.getElementById('previewImage').src = originalFileUrl;
                            document.getElementById('googleView').style.display = 'block';
                        }
                        document.getElementById('result-text').innerText = data.translation;
                        document.getElementById('textResultBox').style.display = 'block';
                    } else {
                        alert('حدث خطأ: ' + data.error);
                        document.getElementById('upload-section').style.display = 'block';
                    }
                })
                .catch(err => {
                    document.getElementById('loading').style.display = 'none';
                    alert('خطأ في الاتصال بالخادم');
                    document.getElementById('upload-section').style.display = 'block';
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
        filename = file.filename.lower()
        
        extracted_text = ""
        
        if filename.endswith('.pdf'):
            doc = fitz.open(stream=file_bytes, filetype="pdf")
            for page in doc:
                extracted_text += page.get_text() + "\n"
            doc.close()
        else:
            img = Image.open(io.BytesIO(file_bytes)).convert("RGB")
            extracted_text = pytesseract.image_to_string(img)
        
        if not extracted_text.strip():
            return jsonify({'success': True, 'translation': 'لم يتم العثور على نص واضح داخل الملف أو الصورة.'})
            
        prompt = f"Translate the following English text into professional Arabic matching professional translation standards. Return ONLY the translated text:\n{extracted_text}"
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
    return "TWEB Google-Style Translate Running Smoothly!", 200

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

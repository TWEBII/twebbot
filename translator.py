import os
import requests
from deep_translator import GoogleTranslator

def translate_text(text, target_lang='ar'):
    """
    دالة ترجمة النصوص الفورية
    """
    try:
        translated = GoogleTranslator(source='auto', target=target_lang).translate(text)
        return translated
    except Exception as e:
        print(f"Translation Error: {e}")
        return text

def extract_and_translate_image(image_path, target_lang='ar'):
    """
    استخراج النص من الصورة عبر OCR مجاني وترجمته فوراً
    """
    if not os.path.exists(image_path):
        return "❌ ملف الصورة غير موجود."
    
    try:
        url = 'https://api.ocr.space/parse/image'
        api_key = 'helloworld' # مفتاح مجاني عام للاستخدام الخفيف
        
        with open(image_path, 'rb') as f:
            response = requests.post(
                url,
                files={'file': f},
                data={'apikey': api_key, 'language': 'ara'}
            )
        result = response.json()
        
        if result.get('ParsedResults'):
            parsed_text = result['ParsedResults'][0]['ParsedText']
            if parsed_text.strip():
                translated = translate_text(parsed_text, target_lang=target_lang)
                return f"📝 **النص المستخرج:**\n{parsed_text}\n\n🌍 **الترجمة:**\n{translated}"
            else:
                return "❌ لم يتم العثور على نص واضح داخل الصورة."
        else:
            return "❌ فشل قراءة الصورة، حاول بوضوح أعلى."
    except Exception as e:
        return f"❌ حدث خطأ أثناء معالجة الصورة: {str(e)}"

def process_document(file_path, target_lang='ar'):
    """
    معالجة وترجمة المستندات
    """
    if not os.path.exists(file_path):
        return None
    
    # حالياً نوجه المستخدم لروابط أو نقوم بقراءة بسيطة
    return file_path

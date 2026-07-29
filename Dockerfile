FROM python:3.12-slim

# تثبيت أداة tesseract والمكتبات النظامية المطلوبة للصور
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    libtesseract-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# نسخ ملف المتطلبات وتثبيته بالكامل
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# نسخ باقي ملفات البوت إلى السيرفر
COPY . .

# أمر تشغيل البوت الأساسي
CMD ["python", "bot.py"]

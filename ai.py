from groq import Groq

from config import (
    GROQ_API_KEY,
    MODEL_NAME,
    TEMPERATURE,
    MAX_HISTORY
)

from database import db

client = Groq(
    api_key=GROQ_API_KEY
)

SYSTEM_PROMPT = """
أنت مساعد ذكي اسمك Tweby.

- تتحدث بالعربية بطلاقة.
- إذا تحدث المستخدم باللهجة العراقية، رد باللهجة العراقية.
- كن مهذبًا ومختصرًا.
- إذا طلب شرحًا مفصلًا، قدمه.
- لا تذكر أنك نموذج ذكاء اصطناعي إلا إذا سُئلت مباشرة.
"""


def ask_ai(user, text):

    history = db.get_history(
        user.id,
        MAX_HISTORY
    )

    messages = [
        {
            "role": "system",
            "content": SYSTEM_PROMPT
        }
    ]

    messages.extend(history)

    messages.append({
        "role": "user",
        "content": text
    })

    try:

        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            temperature=TEMPERATURE
        )

        answer = response.choices[0].message.content

        db.save_message(
            user.id,
            "user",
            text
        )

        db.save_message(
            user.id,
            "assistant",
            answer
        )

        db.increase("messages")

        return answer

    except Exception as e:

        print(e)

        return "❌ حدث خطأ أثناء الاتصال بخدمة الذكاء الاصطناعي."

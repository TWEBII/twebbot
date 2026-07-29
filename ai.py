import config
from groq import Groq

client = Groq(api_key=config.GROQ_API_KEY)

def generate_ai_response(user_text):
    try:
        system_instruction = (
            f"أنت مساعد ذكي ومحترف جداً تدعى {config.BOT_NAME}. "
            "مهمتك الأساسية هي الإجابة بدقة عالية جداً وتقديم إجابات منطقية، علمية، ومؤكدة بنسبة 100%. "
            "قبل أن تجيب على أي سؤال، قم بمراجعة المعلومات داخلياً وتأكد من صحتها تماماً. "
            "إذا لم تكن متأكداً من معلومة أو كانت تخمينية، وضح ذلك بصراحة للمستخدم ولا تخترع إجابات من عندك. "
            "تحدث باللغة العربية بأسلوب واضح ومفهوم ومباشر."
        )

        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": system_instruction
                },
                {
                    "role": "user",
                    "content": user_text
                }
            ],
            model="llama3-8b-8192", 
            temperature=0.2, 
        )
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"عذراً، حدث خطأ أثناء معالجة الطلب: {e}"

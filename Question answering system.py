from openai import OpenAI
import os
import re

class QuestionAnsweringSystem:
    """
    نظام توليد الأسئلة الاستيضاحية بناءً على المعايير ومعلومات الشركة
    """

    def __init__(self, temperature=0.2, max_tokens=800):
        """
        Initialize the Question Answering System

        Args:
            temperature: درجة حرارة النموذج (0.0 = دقيق، 1.0 = إبداعي)
            max_tokens: أقصى عدد tokens للإجابة
        """
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate_questions(self, criteria_text, company_info_text, n_questions=10):
        """
        توليد أسئلة استيضاحية بناءً على المعايير ومعلومات الشركة

        Args:
            criteria_text: نص المعايير المستخرجة (string أو list of strings)
            company_info_text: معلومات الشركة من الموقع (string)
            n_questions: عدد الأسئلة المطلوبة

        Returns:
            list: قائمة الأسئلة
        """

        # تحويل المعايير إلى نص إذا كانت list
        if isinstance(criteria_text, list):
            criteria_text = "\n".join([f"- {c}" for c in criteria_text])

        # بناء الـ prompt
        prompt = f"""
أنت خبير في إعداد مقترحات المناقصات. لديك المعلومات التالية:

## المعايير والمتطلبات المستخرجة من RFP:
{criteria_text}

## معلومات الشركة المتوفرة:
{company_info_text}

---

**المهمة:**
بناءً على المعايير المذكورة أعلاه ومعلومات الشركة المتوفرة، قم بتوليد {n_questions} أسئلة استيضاحية دقيقة وعملية 
لجمع المعلومات الناقصة التي نحتاجها لكتابة مقترح قوي ومقنع.

**إرشادات الأسئلة:**
1. يجب أن يكون كل سؤال مرتبطاً مباشرة بأحد المعايير المذكورة
2. ركّز على المعلومات الناقصة أو غير الواضحة
3. اجعل الأسئلة محددة وقابلة للإجابة (تجنب الأسئلة العامة)
4. استخدم لغة عربية فصحى واضحة ومختصرة
5. رتّب الأسئلة حسب الأولوية (الأهم أولاً)
6. اجعل كل سؤال في سطر واحد

**المجالات المحتملة للأسئلة:**
- الميزانية والتسعير
- الجداول الزمنية والمدد
- المؤهلات والخبرات والشهادات
- المواصفات الفنية والمتطلبات
- التسليمات والمخرجات
- معايير القبول والجودة
- الأمان والامتثال
- فريق العمل والموارد
- المشاريع السابقة المشابهة
- الدعم الفني والصيانة

**الصيغة المطلوبة:**
أكتب الأسئلة مرقّمة من 1 إلى {n_questions} بدون أي شرح أو تعليق إضافي.

مثال على الصيغة:
1. ما هي المشاريع المشابهة التي نفذتها الشركة في السنوات الثلاث الماضية؟
2. ما هو عدد الموظفين الفنيين المتخصصين المتاحين للمشروع؟
...

الآن، اكتب {n_questions} أسئلة:
"""

        try:
            # استدعاء OpenAI API
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role":"system",
                        "content":"أنت خبير في إعداد مقترحات المناقصات وتوليد الأسئلة الاستيضاحية الدقيقة."
                    },
                    {
                        "role":"user",
                        "content":prompt
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )

            content = response.choices[0].message.content.strip()

            # استخراج الأسئلة من النص
            questions = self._extract_questions(content, n_questions)

            return questions

        except Exception as e:
            print(f"❌ خطأ في توليد الأسئلة: {str(e)}")
            return []

    def _extract_questions(self, content, n_questions):
        """
        استخراج الأسئلة من نص الإجابة
        هذه دالة مساعدة داخلية - تستخرج الأسئلة المرقمة من النص
        """
        lines = [l.strip() for l in content.splitlines() if l.strip()]
        questions = []

        # استخراج الأسطر المرقمة (1. سؤال، 2. سؤال، ...)
        for line in lines:
            # البحث عن أرقام في بداية السطر
            if re.match(r"^(\d+|[٠-٩]+)\s*[).\-–:؛]?\s*", line):
                # إزالة الرقم والحصول على السؤال
                question = re.sub(r"^(\d+|[٠-٩]+)\s*[).\-–:؛]?\s*", "", line).strip()
                if len(question) > 5:
                    questions.append(question)

        # إذا ما لقينا أسئلة كافية، خذ أي أسطر فيها علامة استفهام
        if len(questions) < n_questions:
            questions = [l for l in lines if len(l) > 10 and '؟' in l][:n_questions]

        return questions[:n_questions]

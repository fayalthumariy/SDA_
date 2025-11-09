from openai import OpenAI
from langchain.prompts import ChatPromptTemplate
import os
from concurrent.futures import ThreadPoolExecutor, as_completed


class SummarizeChunk:
    def __init__(self, text_chunk, temperature1=.2, temperature2=.1, max_token=500):
        self.text_chunk = text_chunk
        self.client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.temperature1 = temperature1
        self.temperature2 = temperature2
        self.max_token = max_token

    def generate_summary_ar(self, text):
        """
يلخّص فقط العناصر التالية من أي نص عربي:
- نطاق عمل المشروع
- برنامج العمل/خطة التنفيذ
- مكان تنفيذ الأعمال
- جدول الكميات والأسعار
الناتج: ملخص عربي رسمي من 8 إلى 10 جمل. يكتب "غير مذكور" عند غياب أي عنصر.
        """
        if not text or len(text.strip()) == 0:
            return None

        max_chars = 15000
        if len(text) > max_chars:
            text = text[:max_chars]

        summary_prompt = ChatPromptTemplate.from_template("""
        أنت مساعد متخصص في تلخيص مستندات المناقصات باللغة العربية.

        الهدف: إنتاج ملخص رسمي باللغة العربية الفصحى مكوّن من 8 إلى 10 جمل متصلة، يركّز حصراً على:
        1) نطاق عمل المشروع،
        2) برنامج العمل أو خطة التنفيذ،
        3) مكان تنفيذ الأعمال،
        4) جدول الكميات والأسعار (إن وُجد).

        قواعد صارمة:
        - لا تضف أي معلومات عامة أو متكررة مثل "يجب على مقدمي العروض" أو "وفقاً للشروط والمواصفات".
        - لا تختلق أي معلومة غير موجودة في النص. عند غياب معلومة اكتب: "غير مذكور".
        - لا تكرّر نفس الفكرة أو الفقرة مرتين.
        - التزم بثماني إلى عشر جمل كاملة مترابطة.
        - استخدم لغة رسمية وواضحة، دون عناوين أو نقاط.

        النص:
        {text}

        أنتج الآن 8–10 جمل تغطي العناصر الأربعة بالترتيب المنطقي (نطاق العمل → البرنامج → المكان → جدول الكميات والأسعار).
        لا تضف عناوين أو كلمة "الملخص"، فقط الجمل النهائية.
        """)

        filled_prompt = summary_prompt.format(text=text)

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system",
                     "content": "مساعد متخصص في تلخيص مستندات المناقصات باللغة العربية، دقيق وغير مُهلْهِل."},
                    {"role": "user", "content": filled_prompt}
                ],
                temperature=self.temperature1,
                max_tokens=self.max_token
            )

            summary = response.choices[0].message.content.strip()

            sentences = [s for s in summary.replace("؟", ".").split(".") if s.strip()]
            if len(sentences) < 8:
                filled_prompt_retry = filled_prompt + "\n\nتذكير: يجب أن يكون الملخص 8–10 جُمَل كاملة. اكتب \"غير مذكور\" للعناصر الغائبة."
                response2 = self.client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system",
                         "content": "مساعد متخصص في تلخيص مستندات المناقصات باللغة العربية، دقيق وغير مُهلْهِل."},
                        {"role": "user", "content": filled_prompt_retry}
                    ],
                    temperature=self.temperature2,
                    max_tokens=self.max_token
                )
                summary = response2.choices[0].message.content.strip()

            if "الملخص:" in summary:
                summary = summary.split("الملخص:", 1)[-1].strip()

            return summary

        except Exception as e:
            print(f"⚠️ Error during summarization: {e}")
            return None

    def summarize_chunks_ar_parallel(self, chunks, max_workers=6):
        def _work(idx, chunk):
            summary = self.generate_summary_ar(chunk)
            return idx, chunk, summary

        if not chunks:
            return []

        max_workers = max(1, min(max_workers, len(chunks)))
        results = [None] * len(chunks)

        with ThreadPoolExecutor(max_workers=max_workers) as ex:
            futures = {ex.submit(_work, i, ch): i for i, ch in enumerate(chunks)}
            total = len(futures)
            done_count = 0

            for fut in as_completed(futures):
                i, chunk, summary = fut.result()
                results[i] = (chunk, summary)
                done_count += 1
                print(f"\n🔹 Summarized chunk {done_count}/{total} (index {i})")

        return results

    def combine_all_summarized_chunk(self, summaries):
        combined = ''

        for item in summaries:
            if isinstance(item, tuple):
                summary = item[1]
            else:
                summary = item

            if summary:
                combined = f'{combined}\n\n{summary}'

        return combined.strip()

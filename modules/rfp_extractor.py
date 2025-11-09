# w function
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
import pdfplumber
import json
from collections import Counter
from typing import List, Literal, Optional
from itertools import groupby



# ============================================
# تعريف البنية (Schema)
# ============================================
class Criteria(BaseModel):
    name: str = Field(
        description="Section Criteria from an RFP",
    )
    category: Literal['financial','technical','quality','timeline','other'] = Field(
        description="The type of criteria we are collecting from the RFP text"
    )
    description: str = Field(
        description="Description of the criteria",
    )
    weight: Optional[float] = Field(
        default=None,
        description="Weight of the criteria if explicitly mentioned in RFP",
    )


class AllCriteria(BaseModel):
    summary: str = Field(
        description="A summary of all of the RFP criteria"
    )
    criteria: List[Criteria] = Field(
        description="All of the corresponding criteria related to finance, quality, timeline, other, etc.",
    )


# ============================================
# الفنكشن الرئيسية
# ============================================
def extract_and_weight_rfp_criteria(pdf_path='rfp.pdf', output_file="criteria_with_weights.json"):
    """استخراج وحساب أوزان معايير RFP من ملف PDF"""

    # ============================================
    # 1. استخراج النص من PDF
    # ============================================
    all_text = []
    with pdfplumber.open(pdf_path) as pdf:
        print(f"   📄 عدد الصفحات: {len(pdf.pages)}")
        for i, page in enumerate(pdf.pages, 1):
            text = page.extract_text()
            if text:
                all_text.append(text)
                if i <= 2:  # عرض أول صفحتين
                    print(f"   ✓ صفحة {i}: {len(text)} حرف")

    text = "\n".join(all_text)

    # ============================================
    # 2. إعداد النموذج واستخراج المعايير
    # ============================================
    llm = ChatOpenAI(model_name="gpt-4o-mini")

    # البرومبت
    prompt = f"""
أنت محلل خبير متخصص في كراسات الشروط السعودية.

من النص التالي، استخرج جميع معايير التقييم المذكورة أو المستنتجة بشكل منظم ومفصل.

النص:
-----------------------------
{text}
-----------------------------

استخرج المعايير وصنفها حسب الفئات التالية:

1. **معايير فنية**
   - الخبرة والكفاءة الفنية
   - المؤهلات والشهادات
   - الكوادر البشرية
   - الأدوات والتقنيات

2. **معايير مالية**
   - السعر المقترح
   - القيمة مقابل المال
   - الضمانات المالية

3. **معايير الجدول الزمني**
   - مدة التنفيذ
   - الالتزام بالمواعيد
   - خطة العمل الزمنية

4. **معايير الجودة**
   - معايير الجودة الفنية
   - ضمان الجودة
   - التدقيق والمراجعة

5. **معايير أخرى**
   - أي معايير إضافية مذكورة

اكتب باللغة العربية من اليمين لليسار.
"""

    # استخراج المعايير
    extractor = llm.with_structured_output(AllCriteria)
    result = extractor.invoke(prompt)

    # حفظ النتيجة الأولية
    initial_output = "criteria_extraction_result.json"
    with open(initial_output, "w", encoding="utf-8") as f:
        json.dump(result.model_dump(), f, ensure_ascii=False, indent=2)

    print("✅ تم استخراج المعايير")

    # ============================================
    # 3. حساب الأوزان تلقائياً
    # ============================================

    # اقرأ النتيجة المحفوظة
    with open(initial_output, "r", encoding="utf-8") as f:
        data = json.load(f)

    # احسب عدد المعايير لكل فئة
    categories = [c['category'] for c in data['criteria']]
    category_counts = Counter(categories)

    print(f"\n توزيع المعايير:")
    for cat, count in category_counts.items():
        print(f"   {cat}: {count} معيار")

    # حدد أوزان كل فئة (مجموعها = 1.0)
    category_weights = {
        'financial': 0.30,    # 30%
        'technical': 0.35,    # 35%
        'quality': 0.20,      # 20%
        'timeline': 0.10,     # 10%
        'other': 0.05         # 5%
    }

    print(f"\n أوزان الفئات:")
    for cat, weight in category_weights.items():
        if cat in category_counts:  # اطبع فقط الفئات الموجودة
            print(f"   {cat}: {weight*100}%")

    # وزّع الأوزان على المعايير
    for criteria in data['criteria']:
        category = criteria['category']
        # وزّع وزن الفئة على عدد المعايير فيها بالتساوي
        criteria['weight'] = round(category_weights[category] / category_counts[category], 4)

    # تحقق من أن مجموع الأوزان = 1.0
    total_weight = sum(c['weight'] for c in data['criteria'])
    print(f"\n مجموع الأوزان: {round(total_weight, 4)}")

    # احفظ النتيجة النهائية
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"\n تم حساب وحفظ الأوزان في: {output_file}")

    # ============================================
    # 4. طباعة النتائج
    # ============================================
    print("\n" + "="*60)
    print(" المعايير النهائية مع الأوزان:")
    print("="*60)

    # رتب حسب الفئة
    sorted_criteria = sorted(data['criteria'], key=lambda x: x['category'])
    for category, items in groupby(sorted_criteria, key=lambda x: x['category']):
        items_list = list(items)
        category_total = sum(c['weight'] for c in items_list)
        print(f"\n🔹 {category.upper()} (إجمالي: {category_total*100:.1f}%)")
        for c in items_list:
            print(f"   • {c['name']}: {c['weight']*100:.2f}%")
            print(f"     └─ {c['description']}")

    print("\n" + "="*60)

    return data
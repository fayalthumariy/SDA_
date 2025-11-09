"""
Gap Analyzer Module
تحليل الفجوات بين متطلبات RFP وقدرات الشركة
"""

import json
from openai import OpenAI


def analyze_gaps(
    requirements_text: str, 
    company_text: str,
    api_key: str = None,
    model: str = "gpt-4o-mini"
):
    """
    مقارنة متطلبات RFP مع قدرات الشركة باستخدام GPT
    
    Args:
        requirements_text: نص متطلبات RFP
        company_text: نص قدرات الشركة
        api_key: مفتاح OpenAI API (اختياري)
        model: اسم النموذج
        
    Returns:
        list: قائمة بالمتطلبات مع حالتها (مغطى/غير مغطى/غير واضح)
    """
    
    # Initialize OpenAI client
    if api_key:
        client = OpenAI(api_key=api_key)
    else:
        client = OpenAI()  # من البيئة
    
    prompt = f"""
أنت تعمل كمراجع عطاءات (Procurement Compliance Checker).

مهمتك:
- قارن بين (متطلبات العمل في المناقصة) و (قدرات الشركة).
- أخرج النتيجة بصيغة JSON فقط بدون أي شرح إضافي.

لكل بند قيّم الحالة التالية:
- "status":
   - "مغطى ✅"  = الشركة قادرة عليه بوضوح
   - "غير مغطى ❌" = الشركة لا تذكر أنها تقوم بهذا
   - "غير واضح ⚠" = مذكور بشكل غير مؤكد
- "evidence": انسخ السطر أو الفكرة من نص الشركة الذي يثبت ذلك.

المدخلات:
[متطلبات المناقصة]
{requirements_text}

[قدرات الشركة]
{company_text}

أعد النتيجة في صيغة JSON كقائمة عناصر مثل:
[
  {{
    "requirement": "نص المتطلب",
    "status": "مغطى ✅ / غير مغطى ❌ / غير واضح ⚠",
    "evidence": "الدليل من نص الشركة (إن وُجد)"
  }}
]
"""
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "أنت خبير تدقيق عطاءات صارم."},
                {"role": "user", "content": prompt}
            ],
            temperature=0,
            max_tokens=1500,
        )
        
        raw_out = response.choices[0].message.content.strip()
        print("✓ تم استلام الرد من LLM")
        
        # تنظيف الرد
        cleaned = raw_out.replace("```json", "").replace("```", "").strip()
        
        try:
            result = json.loads(cleaned)
            print(f"✓ تم تحليل {len(result)} متطلب")
            return result
        except json.JSONDecodeError:
            print("⚠ فشل تحليل JSON، إرجاع الرد الخام")
            return [{"raw_output": raw_out}]
            
    except Exception as e:
        print(f"❌ خطأ في analyze_gaps: {e}")
        raise


def generate_questions_based_gap(
    missing_points: list,
    api_key: str = None,
    model: str = "gpt-4o-mini"
):
    """
    توليد أسئلة توضيحية بناءً على المتطلبات غير المغطاة
    
    Args:
        missing_points: قائمة بالمتطلبات غير المغطاة
        api_key: مفتاح OpenAI API (اختياري)
        model: اسم النموذج
        
    Returns:
        list: قائمة بالأسئلة التوضيحية
    """
    
    if not missing_points:
        return ["لا توجد فجوات واضحة تستدعي استفسارات إضافية."]
    
    # Initialize OpenAI client
    if api_key:
        client = OpenAI(api_key=api_key)
    else:
        client = OpenAI()
    
    joined_points = "\n".join(f"- {m}" for m in missing_points)

    prompt = f"""
أنت خبير في المناقصات وتوليد الاستفسارات الرسمية.

المطلوب:
أنشئ أسئلة توضيحية رسمية بناءً على البنود التالية غير المغطاة من قبل الشركة:

{joined_points}

قواعد:
- استخدم أسلوب رسمي واضح مثل "يرجى توضيح..."، "قدّم تفاصيل..."، "اشرح آلية..."
- لا تكرر نفس الفكرة بصياغات مختلفة.
- لا تضف مقدمة أو شرح.
- أخرج {len(missing_points)} أسئلة فقط.
"""
    
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "خبير مناقصات"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=600
        )
        
        raw = response.choices[0].message.content.strip()
        print(f"✓ تم توليد {len(missing_points)} سؤال")
        
        # تنظيف الأسئلة
        questions = [q.strip("1234567890).:-– ") for q in raw.split("\n") if q.strip()]
        return questions
        
    except Exception as e:
        print(f"❌ خطأ في generate_questions: {e}")
        raise


def perform_full_gap_analysis(
    rfp_criteria_file: str,
    company_profile_file: str,
    output_file: str = "gap_analysis.json",
    api_key: str = None
):
    """
    تحليل شامل للفجوات بين RFP والشركة
    
    Args:
        rfp_criteria_file: ملف معايير RFP (JSON)
        company_profile_file: ملف بروفايل الشركة (JSON)
        output_file: ملف حفظ النتيجة
        api_key: مفتاح OpenAI API
        
    Returns:
        dict: تقرير شامل بالفجوات والأسئلة
    """
    
    print("\n" + "="*60)
    print("🔍 بدء تحليل الفجوات")
    print("="*60)
    
    # 1. قراءة ملف RFP
    print(f"\n📄 قراءة معايير RFP من: {rfp_criteria_file}")
    with open(rfp_criteria_file, 'r', encoding='utf-8') as f:
        rfp_data = json.load(f)
    
    # تحويل المعايير إلى نص
    rfp_text = ""
    for criteria in rfp_data.get('criteria', []):
        rfp_text += f"- {criteria['name']}: {criteria['description']}\n"
    
    print(f"✓ تم تحميل {len(rfp_data.get('criteria', []))} معيار")
    
    # 2. قراءة ملف الشركة
    print(f"\n🏢 قراءة بروفايل الشركة من: {company_profile_file}")
    with open(company_profile_file, 'r', encoding='utf-8') as f:
        company_data = json.load(f)
    
    # تحويل البروفايل إلى نص
    company_text = f"""
اسم الشركة: {company_data.get('company_names', {}).get('ar', [''])[0]}
نبذة: {company_data.get('about_us', '')}
الخدمات: {', '.join(company_data.get('services', []))}
المجالات: {', '.join(company_data.get('industries_or_focus', []))}
التراخيص: {', '.join(company_data.get('licenses_or_certifications', []))}
سنوات الخبرة: {company_data.get('experience_years', '')}
الأعمال السابقة: {', '.join(company_data.get('previous_work', []))}
"""
    
    print(f"✓ تم تحميل بروفايل الشركة")
    
    # 3. تحليل الفجوات
    print(f"\n⚙️ بدء المقارنة...")
    gap_results = analyze_gaps(rfp_text, company_text, api_key=api_key)
    
    # 4. تصنيف النتائج
    covered = []
    not_covered = []
    unclear = []
    
    for item in gap_results:
        status = item.get('status', '')
        if 'مغطى ✅' in status:
            covered.append(item)
        elif 'غير مغطى ❌' in status:
            not_covered.append(item)
        elif 'غير واضح ⚠' in status:
            unclear.append(item)
    
    print(f"\n📊 النتائج:")
    print(f"   ✅ مغطى: {len(covered)}")
    print(f"   ❌ غير مغطى: {len(not_covered)}")
    print(f"   ⚠ غير واضح: {len(unclear)}")
    
    # 5. توليد الأسئلة
    print(f"\n❓ توليد الأسئلة التوضيحية...")
    missing_requirements = [item['requirement'] for item in not_covered + unclear]
    questions = generate_questions_based_gap(missing_requirements, api_key=api_key)
    
    # 6. إنشاء التقرير
    report = {
        "summary": {
            "total_requirements": len(gap_results),
            "covered": len(covered),
            "not_covered": len(not_covered),
            "unclear": len(unclear)
        },
        "covered_requirements": covered,
        "not_covered_requirements": not_covered,
        "unclear_requirements": unclear,
        "clarification_questions": questions
    }
    
    # 7. حفظ التقرير
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"\n✅ تم حفظ التقرير في: {output_file}")
    print("="*60)
    
    return report


def print_gap_analysis(report: dict):
    """
    طباعة تقرير الفجوات بشكل منسق
    
    Args:
        report: تقرير الفجوات
    """
    
    print("\n" + "="*60)
    print("📊 تقرير تحليل الفجوات")
    print("="*60)
    
    summary = report['summary']
    print(f"\n📈 الملخص:")
    print(f"   إجمالي المتطلبات: {summary['total_requirements']}")
    print(f"   ✅ مغطى: {summary['covered']}")
    print(f"   ❌ غير مغطى: {summary['not_covered']}")
    print(f"   ⚠ غير واضح: {summary['unclear']}")
    
    # المتطلبات المغطاة
    if report['covered_requirements']:
        print(f"\n✅ المتطلبات المغطاة:")
        for i, item in enumerate(report['covered_requirements'], 1):
            print(f"\n{i}. {item['requirement']}")
            if item.get('evidence'):
                print(f"   الدليل: {item['evidence']}")
    
    # المتطلبات غير المغطاة
    if report['not_covered_requirements']:
        print(f"\n❌ المتطلبات غير المغطاة:")
        for i, item in enumerate(report['not_covered_requirements'], 1):
            print(f"\n{i}. {item['requirement']}")
    
    # المتطلبات غير الواضحة
    if report['unclear_requirements']:
        print(f"\n⚠ المتطلبات غير الواضحة:")
        for i, item in enumerate(report['unclear_requirements'], 1):
            print(f"\n{i}. {item['requirement']}")
            if item.get('evidence'):
                print(f"   الدليل: {item['evidence']}")
    
    # الأسئلة التوضيحية
    if report['clarification_questions']:
        print(f"\n❓ أسئلة توضيحية ({len(report['clarification_questions'])} سؤال):")
        for i, question in enumerate(report['clarification_questions'], 1):
            print(f"   {i}. {question}")
    
    print("\n" + "="*60)
"""
Company Profile Extractor Module
استخراج ملف تعريف الشركة من PDF
"""

import re
import json
import os
from openai import OpenAI
import pdfplumber


def _read_pdf_text(pdf_path: str) -> str:
    """
    Extract text from PDF using multiple methods.
    Priority: pdfplumber -> pytesseract OCR
    """
    text = ""

    # Try pdfplumber first
    try:
        pages = []
        with pdfplumber.open(pdf_path) as pdf:
            for p in pdf.pages:
                t = p.extract_text() or ""
                pages.append(t)
        text = "\n".join(pages).strip()
        if text:
            print(f"✓ تم استخراج النص باستخدام pdfplumber ({len(text)} حرف)")
            return text
    except Exception as e:
        print(f"فشل في pdfplumber: {e}")

    # Fallback to OCR with pytesseract
    if not text:
        try:
            import pytesseract
            from pdf2image import convert_from_path
            print("محاولة استخراج بـ OCR...")
            pages = convert_from_path(pdf_path, dpi=300)
            ocr_texts = []
            for i, page in enumerate(pages, 1):
                print(f"  OCR صفحة {i}/{len(pages)}...")
                page_text = pytesseract.image_to_string(page, lang='ara+eng')
                ocr_texts.append(page_text)
            text = "\n".join(ocr_texts).strip()
            if text:
                print(f"✓ تم استخراج النص باستخدام OCR ({len(text)} حرف)")
        except Exception as e:
            print(f"فشل في OCR: {e}")

    return text


def _basic_clean(s: str) -> str:
    """تنظيف النص المستخرج"""
    s = s.replace("\x00", " ")
    s = s.replace("\ufeff", "")  # Remove BOM
    # Collapse excessive whitespace
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def extract_company_profile_from_pdf(
    pdf_path: str,
    api_key: str = None,
    model: str = "gpt-4o-mini",
    max_ctx_chars: int = 20000,
    return_dict: bool = True,
    output_file: str = "company_profile.json"
):
    """
    قراءة ملف PDF للشركة واستخراج الملف التعريفي

    Args:
        pdf_path: مسار ملف PDF
        api_key: مفتاح OpenAI API
        model: النموذج المستخدم
        max_ctx_chars: الحد الأقصى للأحرف
        return_dict: إرجاع كـ dict أم JSON string
        output_file: مسار ملف الحفظ

    Returns:
        Dict أو JSON string مع بيانات ملف الشركة
    """
    
    # Initialize OpenAI client
    if api_key:
        llm_client = OpenAI(api_key=api_key)
    else:
        # Use from environment
        llm_client = OpenAI()

    # Extract text from PDF
    print(f"قراءة ملف PDF: {pdf_path}")
    full_text = _read_pdf_text(pdf_path)

    if not full_text:
        raise RuntimeError(f"لم يتم استخراج أي نص من: {pdf_path}")

    # Clean and truncate text
    full_text = _basic_clean(full_text)
    snippet = full_text[:max_ctx_chars]

    print(f"إرسال {len(snippet)} حرف إلى LLM (model: {model})...")

    prompt = f"""
أنت محلل ملفات تعريف شركات.

أُعطيت نصاً خاماً مُستخرجاً من ملف PDF للتعريف بالشركة (قد يحتوي على العربية والإنجليزية).
استخرج كل المعلومات الموجودة حرفياً في النص بدون أي اختراع أو تلخيص.

القواعد:
- اكتب المعلومات بالعربي فقط.
- إستخرج المعلومات العربية فقط.
- إستخرج حسابات التواصل الإجتماعي و السوشل ميديا و رابط الموقع و الإيميل بالإنجليزي.
- إذا لم تتوفر اي معلومة او لم تكن متواجدة اكتب لا توجد.
- اكتب فقط ما هو مذكور نصاً.
- لا تضف أو تتخيل أي معلومة.
- إذا لم توجد معلومة، أعدها كقيمة فارغة "" أو قائمة [].
- أعد القوائم كما هي (خدمات، مجالات، أهداف...).
- أعد النتيجة في صيغة JSON فقط وفق الهيكل التالي:

{{
  "company_names": {{
    "ar": ["اسم الشركة بالعربية"],
    "en": ["Company name in English"]
  }},

  "previous_work": ["اسم الشركة 1", "الخدمة المقدمة إلى الشركة 1" , "اسم الشركة 2", "الخدمة المقدمة إلى الشركة 2", "اسم الشركة 3", "الخدمة المقدمة إلى الشركة 3" ],
  "about_us": " نبذة عن الشركة كما ورد في النص.",
  "description": "وصف الشركة كما ورد في النص.",
  "services": ["خدمة 1", "خدمة 2"],
  "industries_or_focus": ["مجال 1", "مجال 2"],
  "values_or_objectives": ["قيمة 1", "هدف 1"],
  "licenses_or_certifications": ["ترخيص 1", "شهادة 1"],
  "locations": ["عنوان موقع 1", "عنوان مقر الشركة 1"],
  "contact": {{
    "phones": ["+966..."],
    "emails": ["email@example.com"],
    "social": ["https://..."],
    "website": "https://..."
  }},
  "vision": "رؤية الشركة",
  "mission": "رسالة الشركة",
  "goals": ["هدف 1", "هدف 2"],
  "values": ["قيمة 1", "قيمة 2"],
  "experience_years": "عدد سنوات الخبرة إن وجدت إن لم توجد لا تذكرها",
  "established_year": "سنة التأسيس إن وجدت",
  "additional_info": "أي معلومات إضافية مهمة"
}}

النص (من ملف PDF):
-----------------------------------
{snippet}
-----------------------------------

أجب بالـ JSON فقط بدون أي شرح إضافي.
    """.strip()

    try:
        resp = llm_client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=2500,
            temperature=0
        )
        out = resp.choices[0].message.content.strip()
        print("✓ تم استلام الرد من LLM")

    except Exception as e:
        raise RuntimeError(f"فشل استدعاء LLM API: {e}")

    # Remove markdown code fences if present
    if out.startswith("```"):
        out = re.sub(r"^```(?:json)?\s*", "", out)
        out = re.sub(r"\s*```$", "", out)

    if return_dict:
        try:
            result = json.loads(out)
            print("✓ تم تحليل JSON بنجاح")
            
            # حفظ النتيجة في ملف
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(result, f, ensure_ascii=False, indent=2)
            print(f"✓ تم حفظ النتيجة في {output_file}")
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"فشل في تحليل JSON: {e}")
            # Try to fix common JSON issues
            out_fixed = out.replace("\u201c", '"').replace("\u201d", '"')
            out_fixed = out_fixed.replace("\u2019", "'").replace("\u2018", "'")
            out_fixed = re.sub(r",(\s*[}\]])", r"\1", out_fixed)  # Remove trailing commas
            try:
                result = json.loads(out_fixed)
                print("✓ تم تحليل JSON بنجاح بعد الإصلاح")
                
                # حفظ النتيجة في ملف
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, ensure_ascii=False, indent=2)
                print(f"✓ تم حفظ النتيجة في {output_file}")
                
                return result
            except:
                print("لا يمكن تحليل JSON. إرجاع النص الخام.")
                return {"raw_response": out, "error": "JSON parsing failed"}

    return out


# ============================================
# طباعة النتائج المنسقة
# ============================================
def print_company_profile(company_data):
    """طباعة ملف الشركة بشكل منسق"""
    
    print("\n" + "="*50)
    print("ملف تعريف الشركة المستخرج")
    print("="*50)
    
    # اسماء الشركة
    if "company_names" in company_data:
        print(f"\n🏢 اسم الشركة:")
        if company_data["company_names"].get("ar"):
            print(f"   العربي: {', '.join(company_data['company_names']['ar'])}")
        if company_data["company_names"].get("en"):
            print(f"   English: {', '.join(company_data['company_names']['en'])}")
    
    # نبذة عن الشركة
    if company_data.get("about_us"):
        print(f"\n📖 نبذة عن الشركة:")
        print(f"   {company_data['about_us']}")
    
    # الخدمات
    if company_data.get("services"):
        print(f"\n⚙️ الخدمات:")
        for service in company_data["services"]:
            print(f"   • {service}")
    
    # معلومات الاتصال
    if company_data.get("contact"):
        print(f"\n📞 معلومات الاتصال:")
        contact = company_data["contact"]
        if contact.get("phones"):
            print(f"   الهواتف: {', '.join(contact['phones'])}")
        if contact.get("emails"):
            print(f"   الإيميلات: {', '.join(contact['emails'])}")
        if contact.get("website"):
            print(f"   الموقع: {contact['website']}")
    
    print("\n" + "="*50)
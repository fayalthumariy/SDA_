"""
Main Pipeline - RFP Processing System
Complete RFP processing from start to finish
"""

from pdf_handler import HandlePDF
from chunker import Chunker
from summarize_chunk import SummarizeChunk
from company_info_extractor_original import process_company
import os
import json

# ═══════════════════════════════════════════════════════════════
# Configuration
# ═══════════════════════════════════════════════════════════════

# Folders
PDF_FOLDER = './pdfs/RFP'
OUTPUT_FOLDER = './outputs'

# Company website
COMPANY_WEBSITE = "https://rnec.sa/"

# Create output folder
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

print("=" * 60)
print(" 🔹 نظام معالجة RFP 🔹")
print("=" * 60)

# ═══════════════════════════════════════════════════════════════
# Read PDF files
# ═══════════════════════════════════════════════════════════════

all_rfps = os.listdir(PDF_FOLDER)
print(f"\n عدد ملفات المناقصات: {len(all_rfps)}\n")

# ═══════════════════════════════════════════════════════════════
# Process each file
# ═══════════════════════════════════════════════════════════════

for i, each_rfp in enumerate(all_rfps, 1):
    print(f"\n{'=' * 60}")
    print(f"🔄 جاري معالجة الملف {i}/{len(all_rfps)}: {each_rfp}")
    print(f"{'=' * 60}\n")

    # ═══════════════════════════════════════════════════════════════
    # Stage 1: Extract text from PDF
    # ═══════════════════════════════════════════════════════════════
    try:
        print(f"📄 [1/5] استخراج النصوص من الـ PDF ...")
        pdf_path = os.path.join(PDF_FOLDER, each_rfp)
        pdf_handler = HandlePDF(pdf_path)
        extracted_text = pdf_handler.extract_text()

        if not extracted_text or len(extracted_text.strip()) == 0:
            print(f"⚠️ الملف {each_rfp} لا يحتوي على نصوص")
            continue

        print(f"✅ تم استخراج {len(extracted_text)} حرفًا\n")

    except Exception as e:
        print(f"❌ خطأ أثناء استخراج النصوص: {str(e)}\n")
        continue

    # ═══════════════════════════════════════════════════════════════
    # Stage 2: Clean and chunk text
    # ═══════════════════════════════════════════════════════════════
    try:
        print(f" [2/5] تنظيف وتجزئة النص ...")

        chunker = Chunker()
        cleaned_text = chunker.clean_text(extracted_text)
        chunks = chunker.chunk_text(cleaned_text)

        print(f"✅ تم تقسيم النص إلى {len(chunks)} جزء\n")

    except Exception as e:
        print(f"❌ خطأ أثناء التنظيف والتقسيم: {str(e)}\n")
        continue

    # ═══════════════════════════════════════════════════════════════
    # Stage 3: Summarize chunks
    # ═══════════════════════════════════════════════════════════════
    # Stage 3: Summarize chunks
    try:
        print(f"📝 [3/5] تلخيص الأجزاء ...")

        summarizer = SummarizeChunk(chunks)


        print(f"   ⏳ تلخيص {len(chunks)} قطعة بشكل متوازي...")
        results = summarizer.summarize_chunks_ar_parallel(chunks, max_workers=6)


        summaries = [summary for _, summary in results if summary]

        print(f"\n✅ تم تلخيص {len(summaries)}/{len(chunks)} أجزاء")

        # merge
        combined_summary = summarizer.combine_all_summarized_chunk(results)
        print(f"✅ حجم الملخص النهائي: {len(combined_summary)} حرف\n")

    except Exception as e:
        print(f"❌ خطأ أثناء التلخيص: {str(e)}\n")
        combined_summary = ""
        continue

    # ═══════════════════════════════════════════════════════════════
    # Stage 4: Fetch company info (once only)
    # ═══════════════════════════════════════════════════════════════
    if i == 1:
        try:
            print(f"🏢 [4/5] جلب معلومات الشركة من الموقع الإلكتروني ...")

            company_data = process_company(COMPANY_WEBSITE)

            if company_data:
                print(f"✅ تم جلب معلومات الشركة بنجاح\n")

                company_file = os.path.join(OUTPUT_FOLDER, "company_info.json")
                with open(company_file, 'w', encoding='utf-8') as f:
                    json.dump(company_data, f, ensure_ascii=False, indent=2)

                print(f"💾 تم حفظ معلومات الشركة في: {company_file}\n")
            else:
                print(f"⚠️ تعذر الحصول على معلومات الشركة\n")
                company_data = {}

        except Exception as e:
            print(f"❌ خطأ أثناء جلب معلومات الشركة: {str(e)}\n")
            company_data = {}

    # ═══════════════════════════════════════════════════════════════
    # Stage 5: Save results
    # ═══════════════════════════════════════════════════════════════
    try:
        print(f"💾 [5/5] حفظ النتائج ...")

        base_name = each_rfp.replace('.pdf', '')

        summary_file = os.path.join(OUTPUT_FOLDER, f"summary_{base_name}.txt")
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(f"🔹 ملخص RFP: {each_rfp}\n\n")
            f.write(combined_summary)

        print(f"   ✅ الملخص → {summary_file}")

        cleaned_file = os.path.join(OUTPUT_FOLDER, f"cleaned_{base_name}.txt")
        with open(cleaned_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)

        print(f"   ✅ النص المنظف → {cleaned_file}")

        chunks_file = os.path.join(OUTPUT_FOLDER, f"chunks_{base_name}.json")
        with open(chunks_file, 'w', encoding='utf-8') as f:
            json.dump({"chunks": chunks, "count": len(chunks)}, f, ensure_ascii=False, indent=2)

        print(f"   ✅ الأجزاء → {chunks_file}")

        print(f"\n✅ تم حفظ جميع الملفات في: {OUTPUT_FOLDER}\n")

    except Exception as e:
        print(f"❌ خطأ أثناء حفظ النتائج: {str(e)}\n")

# ═══════════════════════════════════════════════════════════════
# Finish
# ═══════════════════════════════════════════════════════════════

print("\n" + "=" * 60)
print("🎉 تمت معالجة جميع الملفات بنجاح!")
print("=" * 60)

print(f"\n📊 الإحصائيات:")
print(f"   - عدد الملفات المُعالجة: {len(all_rfps)}")
print(f"   - مجلد الإخراج: {OUTPUT_FOLDER}")
print(f"   - معلومات الشركة: company_info.csv & company_info.json")



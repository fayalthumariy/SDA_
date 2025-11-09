"""
Company Info Extractor - النسخة الأصلية
استخراج معلومات الشركة من موقعها
"""

import re
import requests
import pandas as pd
from bs4 import BeautifulSoup
from openai import OpenAI
import os
import json


def fetch_html(url: str) -> str:
    """
    Fetch raw HTML from a website.

    Args:
        url: رابط الموقع

    Returns:
        str: محتوى HTML
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    resp = requests.get(url, headers=headers, timeout=15)
    resp.raise_for_status()
    return resp.text


def get_visible_text_and_soup(html: str):
    """
    Remove scripts/styles and return visible text + BeautifulSoup.

    Args:
        html: محتوى HTML

    Returns:
        tuple: (النص المرئي, BeautifulSoup object)
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    text = soup.get_text(separator=" ", strip=True)
    text = re.sub(r"\s+", " ", text)
    return text, soup


# Regular expressions
PHONE_RE = re.compile(r"(?:\+?966\s?\d{8,9}|\b05\d{8}\b)")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")


def extract_contacts(full_text: str, soup: BeautifulSoup):
    """
    Extract all phone numbers & emails.

    Args:
        full_text: النص الكامل
        soup: BeautifulSoup object

    Returns:
        dict: {"phones": [...], "emails": [...]}
    """
    phones, emails = [], []

    phones += PHONE_RE.findall(full_text)
    emails += EMAIL_RE.findall(full_text)

    # also catch tel:/mailto:
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if href.startswith("tel:"):
            phones.append(href.replace("tel:", "").strip())
        if href.startswith("mailto:"):
            emails.append(href.replace("mailto:", "").strip())

    # ---- Clean / Normalize phones ----
    clean_phones = []
    for p in phones:
        p2 = re.sub(r"[^\d+]", "", p)
        if p2.startswith("05"):
            p2 = "+966" + p2[1:]
        if p2.startswith("966") and not p2.startswith("+"):
            p2 = "+" + p2

        # التأكد من طول الرقم السعودي (10-13 رقم)
        digits_only = re.sub(r"\D", "", p2)
        if 10 <= len(digits_only) <= 13:
            clean_phones.append(p2)

    # ---- Deduplicate ----
    clean_phones = list(set(clean_phones))
    clean_emails = [e for e in set(emails) if not any(bad in e.lower() for bad in ["example", "mysite"])]

    return {"phones": clean_phones, "emails": clean_emails}


def ask_llm_freeform(full_text: str, client: OpenAI):
    """
    Send full text to GPT and return structured JSON.

    Args:
        full_text: النص الكامل
        client: OpenAI client

    Returns:
        str: JSON response من GPT
    """
    prompt = f"""
أنت محلل مواقع شركات.

أُعطيت نصاً خاماً من موقع شركة (قد يحتوي على العربية والإنجليزية).
استخرج كل المعلومات الموجودة حرفياً في النص بدون أي اختراع أو تلخيص.

القواعد:
- لا تكتب إلا ما هو مذكور نصاً.
- لا تضف أو تتخيل أي معلومة.
- إذا لم توجد معلومة، أعدها كقيمة فارغة "" أو قائمة [].
- أعد القوائم كما هي (خدمات، مجالات، أهداف...).
- أعد النتيجة في صيغة JSON فقط كما في الهيكل التالي:

{{
  "company_names": {{
    "ar": ["..." ],
    "en": ["..." ]
  }},
  "description": "وصف الشركة كما ورد في النص.",
  "services": ["...", "..."],
  "industries_or_focus": ["...", "..."],
  "values_or_objectives": ["...", "..."],
  "licenses_or_certifications": ["...", "..."],
  "locations": ["...", "..."],
  "contact": {{
    "phones": ["...", "..."],
    "emails": ["...", "..."],
    "social": ["روابط التواصل إن وجدت"]
  }}
}}

النص:
-----------------------------------
{full_text[:16000]}
-----------------------------------


    """.strip()

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": prompt}],
        max_tokens=1500,
    )

    return response.choices[0].message.content


def process_company(url: str):
    """
    Main pipeline: fetch, parse, extract, and save.

    Args:
        url: رابط موقع الشركة

    Returns:
        dict: معلومات الشركة
    """

    client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

    print(f"🌐 Fetching {url} ...")


    html = fetch_html(url)


    full_text, soup = get_visible_text_and_soup(html)


    contacts = extract_contacts(full_text, soup)


    raw_json = ask_llm_freeform(full_text, client)

    # Clean markdown fences and extra text
    cleaned = (
        raw_json.replace("```json", "")
        .replace("```", "")
        .strip()
    )

    # ---  Try JSON parsing safely ---
    try:
        data = json.loads(cleaned)
    except Exception as e:
        print(f"⚠️ JSON parsing failed: {e}")
        data = {"raw_text": cleaned}

    # --- 📞 Normalize phone numbers ---
    if "contact" in data and "phones" in data["contact"]:
        normalized = []
        for p in data["contact"]["phones"]:
            p = re.sub(r"[^\d+]", "", p)
            if p.startswith("05"):
                p = "+966" + p[1:]
            if p.startswith("966") and not p.startswith("+"):
                p = "+" + p
            normalized.append(p)
        data["contact"]["phones"] = list(set(normalized))

    # --- 🧼 Remove hallucinated socials ---
    if "contact" in data and "social" in data["contact"]:
        data["contact"]["social"] = [
            s for s in data["contact"]["social"]
            if "http" in s or "@" in s or len(s.split()) == 1
        ]

    # --- 💾 Save cleanly ---
    df = pd.DataFrame([{
        "url": url,
        "llm_json": json.dumps(data, ensure_ascii=False, indent=2),
        "phones_regex": ", ".join(contacts["phones"]),
        "emails_regex": ", ".join(contacts["emails"])
    }])
    df.to_csv("company_info.csv", index=False, encoding="utf-8-sig")

    print("\n🧠 النتيجة (تحليل شامل من الذكاء الاصطناعي):\n")
    print(json.dumps(data, ensure_ascii=False, indent=2))
    print("\n📞 بيانات الاتصال المستخرجة بالـ Regex (حقيقية):", contacts)
    print("\n💾 Saved → company_info.csv")


    return data



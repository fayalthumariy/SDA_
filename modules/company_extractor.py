
"""
Company Profile Extractor Module - Enhanced Version
استخراج ملف تعريف الشركة من الموقع الإلكتروني باستخدام web scraping و AI
"""

import warnings
warnings.filterwarnings("ignore")

import re
import json
import unicodedata
import requests
import pandas as pd
import html as ihtml
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup, NavigableString, Comment
from openai import OpenAI
import advertools as adv
import os
from dotenv import load_dotenv

# ====== API KEY Setup ======
load_dotenv()  # Load from .env file
# Or set directly (for testing only):
# os.environ["OPENAI_API_KEY"] = "your-api-key-here"

OPENAI_MODEL = "gpt-4o-mini"
HEADERS = {"User-Agent": "Mozilla/5.0 (X11; Linux x86_64)"}
TIMEOUT = 20

# ---- Feature Toggles ----
def _env_flag(name: str, default: bool = False) -> bool:
    val = os.getenv(name)
    if val is None:
        return default
    return val.strip().lower() in {"1", "true", "yes", "on"}


def _has_easyocr() -> bool:
    try:
        import importlib.util
        return importlib.util.find_spec("easyocr") is not None
    except Exception:
        return False


ENABLE_OCR_PARTNERS = _env_flag("ENABLE_OCR_PARTNERS", default=_has_easyocr())
ENABLE_JS_RENDER = True  # Set to True to render JavaScript pages (requires requests-html)

# ===================== Regex Patterns =====================
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)
EMAIL_RE = re.compile(r"[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}", re.I)
HANDLE_RE = re.compile(r"@[A-Za-z0-9_]{2,}")
ARABIC = re.compile(r"[\u0600-\u06FF]")
LATIN = re.compile(r"^[A-Za-z0-9 ,.&()''\-/|]+$")
PHONE = re.compile(r"(?:\+?966|0)5\d{8}")
INVIS_RE = re.compile(r"[\u200e\u200f\u202A-\u202E\u2066-\u2069\u00A0]")  # bidi/nbsp

# ---- partner hints / detector ----
PARTNER_HINTS_AR = ("شركاء", "شركاؤنا", "عملاؤنا", "العملاء")
PARTNER_HINTS_EN = ("partners", "clients", "our-clients", "our-partners", "swiper", "carousel", "slider")

# ---- branch / location hints ----
BRANCH_TEXT_HINTS_AR = (
    "فروع", "فرع", "فروعنا", "فرعنا", "مواقعنا", "موقعنا", "العنوان", "عنوان",
    "الموقع", "المقر", "مقرنا", "مكاتبنا", "المكاتب"
)
BRANCH_TEXT_HINTS_EN = (
    "branch", "branches", "location", "locations", "address", "addresses",
    "office", "offices", "headquarter", "headquarters", "hq"
)
LOCATION_HINTS_AR = (
    "المملكة العربية السعودية", "المملكة", "السعودية", "السعوديه", "الرياض", "جدة",
    "جده", "الدمام", "الخبر", "مكة", "مكه", "المدينة", "المدينة المنورة", "بريدة",
    "القصيم", "حائل", "تبوك", "نجران", "جازان", "ينبع", "الطائف", "الجبيل",
    "الاحساء", "الأحساء", "أبها", "ابها", "خميس مشيط", "عرعر", "سكاكا", "الباحة"
)
LOCATION_HINTS_EN = (
    "kingdom of saudi arabia", "saudi arabia", "ksa", "riyadh", "jeddah", "dammam",
    "khobar", "al khobar", "mecca", "makkah", "madinah", "medina", "yanbu", "jazan",
    "abha", "najran", "tabuk", "hail", "taif", "jubail", "ahsa", "buraidah", "qassim",
    "sakaka", "arar", "khamis mushait", "khamis mushayt", "al baha"
)
BRANCH_SECTION_SELECTORS = [
    "address",
    "[class*='address']",
    "[class*='Address']",
    "[id*='address']",
    "[id*='Address']",
    "[class*='location']",
    "[class*='Location']",
    "[id*='location']",
    "[id*='Location']",
    "[class*='branch']",
    "[class*='Branch']",
    "[id*='branch']",
    "[id*='Branch']",
    "[class*='office']",
    "[class*='Office']",
    "[id*='office']",
    "[id*='Office']",
    "[class*='map']",
    "[class*='Map']",
    "[id*='map']",
    "[id*='Map']",
    "[class*='contact-info']",
    "[class*='Contact-info']",
    "[class*='contactinfo']"
]
BRANCH_LABEL_PREFIXES = ("العنوان", "عنوان", "الموقع", "location", "address")
CONSULTATION_HINTS_AR = ("الاستشارات", "استشارات", "خدمات استشارية", "حلول استشارية")
CONSULTATION_HINTS_EN = ("consultation", "consultations", "consulting", "advisory", "advisories")

def looks_like_partner_section(html_text: str) -> bool:
    t = html_text.lower()
    if any(h in t for h in PARTNER_HINTS_EN):
        return True
    return any(h in html_text for h in PARTNER_HINTS_AR)

# ===================== Helper Functions =====================

def strip_invisible(s: str) -> str:
    """Remove invisible Unicode characters (bidi marks, nbsp, etc.)"""
    return INVIS_RE.sub("", s or "")


def get_html(url: str) -> str:
    """Fetch HTML content from URL"""
    r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, allow_redirects=True)
    r.raise_for_status()
    r.encoding = r.apparent_encoding or r.encoding
    return r.text


def get_html_js(url: str) -> str:
    """Render JavaScript and fetch HTML content (for Elementor and dynamic pages)"""
    if not ENABLE_JS_RENDER:
        return ""
    
    try:
        from requests_html import HTMLSession
        sess = HTMLSession()
        r = sess.get(url, headers=HEADERS, timeout=TIMEOUT)
        # Small sleep helps Elementor populate nodes
        r.html.render(timeout=30, sleep=1.0, reload=False, keep_page=True)
        return r.html.html
    except Exception as e:
        print(f"⚠️ JS rendering failed for {url}: {e}")
        return ""


def visible_text(html: str) -> str:
    """Extract visible text from HTML, removing scripts, styles, etc."""
    soup = BeautifulSoup(html, "html.parser")
    
    # Remove non-visible tags
    for tag in soup(["script", "style", "noscript", "svg", "canvas", "iframe"]):
        tag.decompose()
    
    # Remove comments
    for comment in soup.find_all(string=lambda s: isinstance(s, Comment)):
        comment.extract()
    
    body = soup.body or soup
    out = []
    
    for node in body.descendants:
        if isinstance(node, NavigableString):
            s = str(node).strip()
            if s:
                out.append(s)
    
    text = "\n".join(out)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{2,}", "\n\n", text)
    
    return unicodedata.normalize("NFC", text.strip())


def keep_arabic(text: str) -> str:
    """Keep only lines containing Arabic text"""
    return "\n".join([line for line in text.splitlines() if ARABIC.search(line)]).strip()


def clean_links(s: str) -> str:
    """Remove URLs, emails, and social handles from text"""
    s = URL_RE.sub("", s)
    s = EMAIL_RE.sub("", s)
    s = HANDLE_RE.sub("", s)
    return re.sub(r"\n{3,}", "\n\n", s.strip())


def detect_english_name(htmls: list) -> str:
    """Detect English company name from HTML meta tags and headings"""
    soup = BeautifulSoup(" ".join(htmls), "html.parser")
    candidates = []
    
    # Check title tag
    if soup.title and soup.title.string:
        candidates.append(soup.title.string)
    
    # Check meta tags
    for prop in ["og:site_name", "og:title", "twitter:title"]:
        meta = soup.find("meta", attrs={"property": prop}) or soup.find("meta", attrs={"name": prop})
        if meta and meta.get("content"):
            candidates.append(meta["content"])
    
    # Check headings
    for h in soup.find_all(["h1", "h2"]):
        candidates.append(h.get_text(" ", strip=True))
    
    # Filter for Latin/English text only
    hits = [c for c in candidates if LATIN.match(c.strip())]
    return sorted(hits, key=len, reverse=True)[0] if hits else "غير متوفر"


# ===================== Contact Extraction =====================

def normalize_sa_phone(num: str) -> str:
    """Normalize Saudi phone numbers to +966XXXXXXXXX format"""
    digits = re.sub(r"\D", "", num)
    
    if digits.startswith("05") and len(digits) >= 10:
        return "+966" + digits[1:10]  # +966 5xxxxxxxx
    if digits.startswith("9665"):
        return "+" + digits[:12]  # +9665xxxxxxxx
    if digits.startswith("966") and not digits.startswith("9665"):
        return "+" + digits
    
    return "+" + digits if digits else num


def collect_attr_values(element) -> list:
    """Collect all attribute values from an HTML element"""
    vals = []
    for _, v in element.attrs.items():
        if isinstance(v, list):
            vals += [str(x) for x in v]
        else:
            vals.append(str(v))
    return vals


FUZZY_EMAIL = re.compile(
    r"([A-Z0-9._%+\-\u200e\u200f\u202A-\u202E\u2066-\u2069\u00A0\s]{1,64})"
    r"@"
    r"([A-Z0-9.\-\u200e\u200f\u202A-\u202E\u2066-\u2069\u00A0\s]{1,255})",
    re.I
)


def _normalize_email_candidate(s: str) -> str:
    """Normalize email candidate by removing invisible chars and spaces"""
    s = strip_invisible(ihtml.unescape(s))
    s = re.sub(r"\s+", "", s)
    s = s.replace("٫", ".").replace("·", ".").replace("•", ".")
    return s


def harvest_emails_all_channels(html: str, soup: BeautifulSoup) -> set:
    """Comprehensive email extraction from multiple sources"""
    emails = set()
    
    # 1) mailto: links
    for a in soup.select('a[href^="mailto:"]'):
        emails.add(a.get("href", "").replace("mailto:", "").strip())
    
    # 2) visible text (two passes)
    txt1 = strip_invisible(soup.get_text(" ", strip=True))
    txt2 = strip_invisible(soup.get_text("", strip=True))
    
    for blob in (txt1, txt2):
        emails |= set(EMAIL_RE.findall(blob))
        for m in FUZZY_EMAIL.finditer(blob):
            emails.add(_normalize_email_candidate(m.group(0)))
    
    # 3) raw HTML (entity-decoded)
    raw = strip_invisible(ihtml.unescape(html))
    emails |= set(EMAIL_RE.findall(raw))
    
    for m in FUZZY_EMAIL.finditer(raw):
        emails.add(_normalize_email_candidate(m.group(0)))
    
    # 4) HTML element attributes
    for el in soup.find_all(True):
        for val in collect_attr_values(el):
            v = strip_invisible(ihtml.unescape(str(val)))
            if "@" in v:
                emails |= set(EMAIL_RE.findall(v))
                for m in FUZZY_EMAIL.finditer(v):
                    emails.add(_normalize_email_candidate(m.group(0)))
    
    # 5) Elementor list text (direct selector)
    for sp in soup.select("span.elementor-icon-list-text"):
        txt = sp.get_text(" ", strip=True)
        if txt:
            n = _normalize_email_candidate(txt)
            if EMAIL_RE.fullmatch(n):
                emails.add(n)
    
    # Final strict validation
    return {e.lower() for e in emails if EMAIL_RE.fullmatch(e)}


def extract_social_media(html: str, soup: BeautifulSoup) -> set:
    """Extract social media links from HTML"""
    social_pattern = re.compile(
        r"(?:https?://|//)?(?:www\.)?"
        r"(instagram\.com|twitter\.com|x\.com|linkedin\.com|facebook\.com|snapchat\.com|tiktok\.com|youtube\.com)"
        r"/[^\s\"'<>)]{1,200}",
        re.I
    )
    
    def _norm(u: str) -> str:
        """Normalize social media URL"""
        u = u.strip()
        if u.startswith("//"):
            return "https:" + u
        if not u.startswith("http"):
            return "https://" + u.lstrip("/")
        return u
    
    socials = set()
    
    # 1) From visible text
    txt = soup.get_text(" ", strip=True)
    for match in social_pattern.finditer(txt):
        socials.add(_norm(match.group(0)))
    
    # 2) From all href attributes (including icon links)
    for a in soup.find_all("a", href=True):
        href = a.get("href", "")
        m = social_pattern.search(href)
        if m:
            socials.add(_norm(m.group(0)))
    
    # 3) From raw HTML
    raw = ihtml.unescape(html)
    for match in social_pattern.finditer(raw):
        socials.add(_norm(match.group(0)))
    
    return socials


def get_contacts_from_html(html: str):
    """Extract phone numbers, emails, and social media from HTML"""
    soup = BeautifulSoup(html, "html.parser")
    phones = set()
    
    # Extract from tel: links
    for a in soup.select('a[href^="tel:"]'):
        phones.add(a.get("href", "").replace("tel:", "").strip())
    
    # Extract from text and attributes
    txt = strip_invisible(soup.get_text(" ", strip=True))
    raw = strip_invisible(ihtml.unescape(html))
    
    phones.update(PHONE.findall(txt))
    
    for el in soup.find_all(True):
        for val in collect_attr_values(el):
            v = strip_invisible(ihtml.unescape(str(val)))
            phones.update(PHONE.findall(v))
    
    # Extract from WhatsApp links
    for a in soup.select('a[href*="wa.me/"], a[href*="api.whatsapp.com/send"]'):
        href = a.get("href", "")
        m = re.search(r"(?:\+?966|0)5\d{8}", href)
        if m:
            phones.add(m.group(0))
    
    # Normalize phone numbers with + prefix
    normalized = []
    for p in phones:
        n = normalize_sa_phone(p)
        if "966" in n and len(n) >= 13:  # +9665xxxxxxxx
            normalized.append(n)
    
    # Extract emails and social media
    emails = harvest_emails_all_channels(html, soup)
    socials = extract_social_media(html, soup)

    return sorted(set(normalized)), sorted(emails), sorted(socials)


# ===================== Branch Locations Extraction =====================

def extract_branch_locations(html: str) -> list:
    """Extract branch/location snippets from the HTML."""
    soup = BeautifulSoup(html, "html.parser")
    results = []
    seen = set()

    def contains_location_hint(text: str) -> bool:
        if not text:
            return False
        lower = text.lower()
        return any(token in text for token in LOCATION_HINTS_AR) or any(
            token in lower for token in LOCATION_HINTS_EN
        )

    def contains_branch_hint(text: str) -> bool:
        if not text:
            return False
        lower = text.lower()
        return any(token in text for token in BRANCH_TEXT_HINTS_AR) or any(
            token in lower for token in BRANCH_TEXT_HINTS_EN
        )

    def normalize_branch_text(text: str) -> str:
        s = strip_invisible(text or "")
        if not s:
            return ""
        s = clean_links(s)
        s = re.sub(r"\s+", " ", s)
        s = s.strip(" -–—•|،؛")
        for prefix in BRANCH_LABEL_PREFIXES:
            if s.startswith(prefix):
                s = s[len(prefix):].lstrip(" :：-–—•|،؛")
                break
            if s.lower().startswith(prefix):
                s = s[len(prefix):].lstrip(" :：-–—•|،؛")
                break
        return s.strip(" -–—•|،؛")

    def consider(text: str):
        text = normalize_branch_text(text)
        if not text:
            return
        if len(text) < 3 or len(text) > 120:
            return
        if URL_RE.search(text) or EMAIL_RE.search(text) or PHONE.search(text):
            return
        if text.count(" ") > 20:
            return
        if not contains_location_hint(text):
            return
        if text in seen:
            return
        seen.add(text)
        results.append(text)

    selectors = ", ".join(BRANCH_SECTION_SELECTORS)
    branch_sections = list(soup.select(selectors)) if selectors else []

    for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "strong", "b"]):
        if contains_branch_hint(heading.get_text(" ", strip=True)):
            sec = heading.find_parent(["section", "div", "ul", "ol"]) or heading.parent
            if sec:
                branch_sections.append(sec)

    seen_ids = set()
    deduped = []
    for sec in branch_sections:
        sid = id(sec)
        if sid in seen_ids:
            continue
        seen_ids.add(sid)
        deduped.append(sec)
    branch_sections = deduped

    for sec in branch_sections:
        consider(sec.get_text(" ", strip=True))
        for node in sec.find_all(["li", "p", "span", "div", "address"]):
            consider(node.get_text(" ", strip=True))

    if not results:
        for line in soup.get_text("\n", strip=True).splitlines():
            consider(line)

    return results


# ===================== Branch List Normalization =====================

def _normalize_branch_text(entry: str) -> str:
    s = strip_invisible(entry or "")
    s = clean_links(s)
    s = re.sub(r"\s+", " ", s)
    return s.strip(" -–—•|،؛")


def dedupe_branch_entries(values: list) -> list:
    """Keep at most one Arabic and one non-Arabic branch entry."""
    arabic_entry = None
    latin_entry = None
    seen = set()

    for val in values or []:
        s = _normalize_branch_text(val)
        if not s or s == "غير متوفر":
            continue
        key = re.sub(r"[\s\-–—,،]+", " ", s).strip().lower()
        if key in seen:
            continue
        seen.add(key)
        if ARABIC.search(s):
            if not arabic_entry:
                arabic_entry = s
        else:
            if not latin_entry:
                latin_entry = s

    result = []
    if arabic_entry:
        result.append(arabic_entry)
    if latin_entry:
        result.append(latin_entry)

    return result if result else ["غير متوفر"]


# ===================== Consultations Extraction =====================

def extract_consultations_from_html(html: str) -> list:
    """Extract consultation-related descriptions from the website."""
    soup = BeautifulSoup(html, "html.parser")
    heading_re = re.compile(r"(الاستشارات|استشارات|consultations?|consulting|advisory)", re.I)
    candidate_sections = []

    for heading in soup.find_all(["h1", "h2", "h3", "h4", "h5", "strong", "b"]):
        txt = heading.get_text(" ", strip=True)
        if heading_re.search(txt or ""):
            sec = heading.find_parent(["section", "div", "article"]) or heading.parent
            if sec:
                candidate_sections.append(sec)

    if not candidate_sections:
        candidate_sections = []
        for el in soup.find_all(True):
            descriptor = " ".join(el.get("class") or []) + " " + (el.get("id") or "")
            if any(h in descriptor.lower() for h in ("consult", "advisory", "استشار")):
                candidate_sections.append(el)

    results = []
    seen = set()

    def consider(text: str):
        text = strip_invisible(text or "")
        text = clean_links(text)
        if not text:
            return
        if len(text) < 20 or len(text) > 280:
            return
        if text in seen:
            return
        seen.add(text)
        results.append(text)

    for sec in candidate_sections:
        consider(sec.get_text(" ", strip=True))
        for node in sec.find_all(["p", "div", "span", "li"]):
            consider(node.get_text(" ", strip=True))
            if len(results) >= 5:
                break
        if len(results) >= 5:
            break

    return results


# ===================== Partners Extraction =====================

def extract_partners_from_html(html: str, base_url: str, ocr=False) -> list:
    """Extract success partners/clients from HTML (including sliders and carousels)"""
    soup = BeautifulSoup(html, "html.parser")
    names = set()
    
    # Find sections with partner headings
    heading_re = re.compile(r"(شركاء\s*النجاح|شركاؤنا|عملاؤنا|العملاء)", re.I)
    candidate_sections = []
    
    for h in soup.find_all(["h1", "h2", "h3", "h4", "h5"]):
        if heading_re.search(h.get_text(" ", strip=True) or ""):
            sec = h.find_parent(["section", "div"]) or h.parent
            if sec:
                candidate_sections.append(sec)
    
    # If no heading found, look for common slider classes
    if not candidate_sections:
        candidate_sections = soup.select(".swiper, .swiper-container, .carousel, .slider, .clients, .partners")
    
    def sanitize_from_src(src: str) -> str:
        """Extract company name from image filename"""
        m = re.search(r"/([^/]+?)\.(?:png|jpe?g|svg|webp)", src or "", re.I)
        if not m:
            return ""
        base = m.group(1)
        base = re.sub(r"[-_]+", " ", base)
        base = re.sub(r"\d+", "", base)
        return base.strip()
    
    img_urls = []
    
    for sec in candidate_sections:
        # Extract from images
        for img in sec.find_all("img"):
            for key in ["alt", "title", "aria-label", "data-alt", "data-title", "data-name"]:
                val = (img.get(key) or "").strip()
                if val:
                    names.add(val)
            
            src = img.get("data-src") or img.get("data-lazy") or img.get("src") or ""
            if src:
                guess = sanitize_from_src(src)
                if guess:
                    names.add(guess)
                img_urls.append(urljoin(base_url, src))
        
        # Extract from links
        for a in sec.find_all("a"):
            txt = a.get_text(" ", strip=True)
            if txt and len(txt) <= 120:
                names.add(txt)
        
        # Extract from captions and text elements
        for cap in sec.find_all(["figcaption", "p", "span", "div"]):
            txt = cap.get_text(" ", strip=True)
            if 2 <= len(txt) <= 120 and not URL_RE.search(txt):
                names.add(txt)
    
    # OCR for logos (optional)
    if ocr and ENABLE_OCR_PARTNERS and img_urls:
        try:
            import easyocr
            import numpy as np
            from PIL import Image
            import io
            
            reader = easyocr.Reader(["ar", "en"], gpu=False)
            
            for u in img_urls[:15]:  # Limit to 15 images
                try:
                    img_bytes = requests.get(u, headers=HEADERS, timeout=10).content
                    im = Image.open(io.BytesIO(img_bytes)).convert("RGB")
                    res = reader.readtext(np.array(im), detail=0, paragraph=True)
                    
                    for r in res:
                        s = r.strip()
                        if (ARABIC.search(s) or re.search(r"[A-Za-z]{3,}", s)) and 2 <= len(s) <= 80:
                            names.add(s)
                except Exception:
                    continue
        except Exception:
            pass
    
    # Filter valid names
    filtered = []
    for n in names:
        s = strip_invisible(n).strip()
        if not s:
            continue
        if ARABIC.search(s) or re.search(r"[A-Za-z]{3,}", s):
            filtered.append(s)
    
    return list(dict.fromkeys(filtered))


# ===================== Previous Projects Extraction =====================

def extract_previous_projects(html: str) -> list:
    """Extract previous projects from the website"""
    soup = BeautifulSoup(html, "html.parser")
    projects = []
    
    # Look for project-related headings
    heading_re = re.compile(r"(مشاريع|أعمال|المشاريع|الأعمال|projects|portfolio)", re.I)
    
    # Find sections with project headings
    for h in soup.find_all(["h1", "h2", "h3", "h4", "h5"]):
        if heading_re.search(h.get_text(" ", strip=True) or ""):
            sec = h.find_parent(["section", "div", "article"]) or h.parent
            if sec:
                # Extract project names from this section
                for item in sec.find_all(["h3", "h4", "h5", "p", "li", "figcaption"]):
                    txt = item.get_text(" ", strip=True)
                    if txt and ARABIC.search(txt) and 5 <= len(txt) <= 150:
                        projects.append(txt)
    
    return list(dict.fromkeys(projects))[:20]  # Limit to 20 projects


# ===================== Why Us Extraction =====================

def extract_why_us_from_html(html: str) -> list:
    """Extract 'Why Us' section from HTML"""
    soup = BeautifulSoup(html, "html.parser")
    items = []
    
    # Find "لماذا نحن" heading
    heading_re = re.compile(r"^\s*لماذا\s*نحن\s*$", re.I)
    container = None
    
    for h in soup.find_all(["h1", "h2", "h3", "h4", "div", "span"]):
        text = h.get_text(" ", strip=True)
        if text and heading_re.search(text):
            container = h.find_parent(["section", "div", "article"]) or h.parent
            break
    
    # If no heading, look for common container classes
    if container is None:
        hits = soup.select(".why-us, .features, .advantages, .elementor-section")
        container = hits[0] if hits else soup
    
    # Extract from Elementor icon boxes
    cards = container.select(".elementor-widget-icon-box, .elementor-icon-box-wrapper, .elementor-column, .elementor-widget")
    found = False
    
    for card in cards:
        t = card.select_one(".elementor-icon-box-title")
        d = card.select_one(".elementor-icon-box-description")
        
        if t and d:
            tt = t.get_text(" ", strip=True)
            dd = d.get_text(" ", strip=True)
            if ARABIC.search(tt) and ARABIC.search(dd):
                items.append(f"{tt}: {dd}")
                found = True
    
    # Fallback: extract from headings + paragraphs
    if not found:
        for title_node in container.find_all(["h3", "h4", "strong", "b", "span"]):
            tt = title_node.get_text(" ", strip=True)
            if not tt or not ARABIC.search(tt) or len(tt) > 30:
                continue
            
            p = title_node.find_next("p")
            if p:
                dd = p.get_text(" ", strip=True)
                if dd and ARABIC.search(dd):
                    items.append(f"{tt}: {dd}")
    
    # Last resort: extract from list items
    if not items:
        for li in container.find_all("li"):
            txt = li.get_text(" ", strip=True)
            if txt and ARABIC.search(txt):
                items.append(txt)
    
    return list(dict.fromkeys(items))


# ===================== AI Extraction Prompt =====================

PROMPT_AR = """استخرج معلومات الشركة من النص العربي أدناه حسب هذا القالب فقط.
أعد جميع الحقول بالعربية، ولا تخترع معلومات غير موجودة. إذا لم توجد معلومة اكتب "غير متوفر".

{
  "اسم_الشركة": "",
  "الاسم_بالإنجليزية": "<<EN_NAME>>",
  "نبذة_عن_الشركة": "",
  "الخدمات": [],
  "المجالات": [],
  "الرؤية": "",
  "الرسالة": "",
  "الأهداف": [],
  "القيم": [],
  "التراخيص": [],
  "فروع_الشركة": [],
  "سنة_التأسيس": "",
  "الخبرات_المتراكمة": "",
  "Extensive_Expertise": "",
  "الاستشارات": "",
  "مشاريع_سابقة": [],
  "شركاء_النجاح": [],
  "لماذا_نحن": [],
  "التواصل": {"الهواتف": [],"الإيميلات": [],"وسائل_التواصل": []},
  "معلومات_إضافية": ""
}

النص العربي:
<<AR_TEXT>>"""

# Define schema keys
LIST_KEYS = {
    "الخدمات", "المجالات", "الأهداف", "القيم", "التراخيص", "فروع_الشركة",
    "مشاريع_سابقة", "شركاء_النجاح", "لماذا_نحن", "وسائل_التواصل"
}

STR_KEYS = {
    "اسم_الشركة", "الاسم_بالإنجليزية", "نبذة_عن_الشركة", "الرؤية", "الرسالة",
    "سنة_التأسيس", "الخبرات_المتراكمة", "Extensive_Expertise", "الاستشارات", "معلومات_إضافية"
}


def coerce_schema(data: dict) -> dict:
    """Ensure schema compliance and replace empty values with 'غير متوفر'"""
    # Ensure contact section exists
    if "التواصل" not in data or not isinstance(data["التواصل"], dict):
        data["التواصل"] = {"الهواتف": [], "الإيميلات": [], "وسائل_التواصل": []}
    
    # Ensure contact sub-keys
    for k in ["الهواتف", "الإيميلات", "وسائل_التواصل"]:
        if k not in data["التواصل"] or not isinstance(data["التواصل"][k], list):
            data["التواصل"][k] = []
    
    # Replace empty lists with "غير متوفر" for list keys
    for k in LIST_KEYS:
        if k not in data or not isinstance(data.get(k), list):
            data[k] = ["غير متوفر"]
        elif len(data[k]) == 0:
            data[k] = ["غير متوفر"]
    
    # Replace empty strings with "غير متوفر" for string keys
    for k in STR_KEYS:
        if k not in data or not isinstance(data.get(k), str):
            data[k] = "غير متوفر"
        elif data[k].strip() == "":
            data[k] = "غير متوفر"
    
    return data


def strip_links_text(v):
    """Recursively remove links from text values"""
    if isinstance(v, str):
        return clean_links(v)
    if isinstance(v, list):
        return [strip_links_text(x) for x in v]
    return v


# ===================== Core Extractor =====================

def extract_company_info_from_urls(urls, api_key=None):
    """Extract company information from multiple URLs"""
    htmls, texts = [], []
    phones, emails, socials = set(), set(), set()
    partners = set()
    why_us = set()
    projects = set()
    branches = set()
    consultations = []
    contact_like = []
    
    print(f"🔍 Processing {len(urls)} URLs...")
    
    for u in urls:
        try:
            print(f"  📄 Fetching: {u}")
            h = get_html(u)
            htmls.append(h)
            
            t = visible_text(h)
            texts.append(t)
            
            # Mark contact-like pages for JS rendering fallback
            path_lower = urlparse(u).path.lower()
            if any(k in path_lower for k in ["contact", "تواصل", "اتصل"]):
                contact_like.append(u)
            
            # Extract contacts (first pass, non-JS)
            p, e, s = get_contacts_from_html(h)
            phones.update(p)
            emails.update(e)
            socials.update(s)
            
            # Extract partners, why-us, projects, branches, and consultations
            partners.update(extract_partners_from_html(h, base_url=u, ocr=ENABLE_OCR_PARTNERS))
            why_us.update(extract_why_us_from_html(h))
            projects.update(extract_previous_projects(h))
            branches.update(extract_branch_locations(h))
            for item in extract_consultations_from_html(h):
                if item not in consultations:
                    consultations.append(item)

        except Exception as ex:
            print(f"  ⚠️ Skip {u}: {ex}")
    
    # If no emails found and JS rendering enabled, try contact pages with JS
    if not emails and ENABLE_JS_RENDER and contact_like:
        print("📧 No emails found, trying JS rendering on contact pages...")
        for u in contact_like[:3]:  # Limit to 3 pages
            print(f"  🔄 Rendering JS: {u}")
            h_js = get_html_js(u)
            if not h_js:
                continue
            
            # Re-parse with JS-rendered DOM
            p2, e2, s2 = get_contacts_from_html(h_js)
            phones.update(p2)
            emails.update(e2)
            socials.update(s2)
            
            # Also try لماذا نحن, branches, and consultations again (in case lazy-loaded)
            why_us.update(extract_why_us_from_html(h_js))
            branches.update(extract_branch_locations(h_js))
            for item in extract_consultations_from_html(h_js):
                if item not in consultations:
                    consultations.append(item)
    
    # Detect English name
    english = detect_english_name(htmls)
    
    # Merge all Arabic text
    merged = keep_arabic(clean_links("\n\n".join(texts)))
    
    # Call OpenAI API for extraction
    print("🤖 Calling OpenAI API for data extraction...")
    client = OpenAI()
    prompt = PROMPT_AR.replace("<<EN_NAME>>", english).replace("<<AR_TEXT>>", merged[:18000])
    
    resp = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": "أعد JSON صالح فقط."},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        response_format={"type": "json_object"}
    )
    
    data = json.loads(resp.choices[0].message.content)
    
    # Enforce schema and fill contacts
    data = coerce_schema(data)
    
    # Fill contact information
    data["التواصل"]["الهواتف"] = sorted(phones) if phones else ["غير متوفر"]
    data["التواصل"]["الإيميلات"] = sorted(emails) if emails else ["غير متوفر"]
    data["التواصل"]["وسائل_التواصل"] = sorted(socials) if socials else ["غير متوفر"]
    
    # Merge scraped lists with AI-extracted lists
    scraped_partners = list(partners) if partners else []
    scraped_why_us = list(why_us) if why_us else []
    scraped_projects = list(projects) if projects else []
    scraped_branches = list(branches) if branches else []

    # Merge and dedupe branches
    merged_branches = (data.get("فروع_الشركة") or []) + scraped_branches
    data["فروع_الشركة"] = dedupe_branch_entries(merged_branches)

    data["شركاء_النجاح"] = list(dict.fromkeys(
        (data.get("شركاء_النجاح") or []) + scraped_partners
    )) if (data.get("شركاء_النجاح") and data["شركاء_النجاح"] != ["غير متوفر"]) or scraped_partners else ["غير متوفر"]
    
    data["لماذا_نحن"] = list(dict.fromkeys(
        (data.get("لماذا_نحن") or []) + scraped_why_us
    )) if (data.get("لماذا_نحن") and data["لماذا_نحن"] != ["غير متوفر"]) or scraped_why_us else ["غير متوفر"]
    
    data["مشاريع_سابقة"] = list(dict.fromkeys(
        (data.get("مشاريع_سابقة") or []) + scraped_projects
    )) if (data.get("مشاريع_سابقة") and data["مشاريع_سابقة"] != ["غير متوفر"]) or scraped_projects else ["غير متوفر"]

    # Merge consultations
    if consultations:
        existing_consult = data.get("الاستشارات") or ""
        existing_consult = existing_consult if existing_consult != "غير متوفر" else ""
        merged_consults = []
        if existing_consult:
            merged_consults.append(existing_consult.strip())
        merged_consults.extend(consultations)
        cleaned_consults = []
        seen_consults = set()
        for text in merged_consults:
            txt = strip_invisible(text or "")
            txt = clean_links(txt)
            txt = txt.strip()
            if not txt:
                continue
            if txt in seen_consults:
                continue
            seen_consults.add(txt)
            cleaned_consults.append(txt)
        data["الاستشارات"] = "\n\n".join(cleaned_consults) if cleaned_consults else "غير متوفر"
    
    # Remove links from non-contact fields
    for k in list(data.keys()):
        if k != "التواصل":
            data[k] = strip_links_text(data[k])
    
    # Remove duplicate وسائل_التواصل if exists at root level
    if "وسائل_التواصل" in data and isinstance(data["وسائل_التواصل"], list):
        print("⚙️ Removing duplicate وسائل_التواصل from root level")
        del data["وسائل_التواصل"]
    
    print("✅ Extraction complete!")
    return data


# ===================== Sitemap Integration =====================

def _same_host(url, root):
    """Check if URL belongs to same host as root"""
    return urlparse(url).netloc == urlparse(root).netloc


def load_sitemap_urls(root_url: str) -> pd.DataFrame:
    """Load URLs from website sitemap"""
    candidates = [
        urljoin(root_url, "sitemap.xml"),
        urljoin(root_url, "/sitemap.xml"),
        urljoin(root_url, "wp-sitemap.xml"),
        urljoin(root_url, "/wp-sitemap.xml"),
        urljoin(root_url, "wp-sitemap-posts-page-1.xml"),
        urljoin(root_url, "en/wp-sitemap-posts-page-1.xml"),
        urljoin(root_url, "wp-sitemap-users-1.xml"),
        urljoin(root_url, "en/wp-sitemap-users-1.xml"),
    ]
    
    errors = []
    
    for sm in candidates:
        try:
            df = adv.sitemaps.sitemap_to_df(sm)
            if "loc" in df and not df.empty:
                df = df[df["loc"].apply(lambda u: _same_host(u, root_url))]
                if not df.empty:
                    return df[["loc", "lastmod"]] if "lastmod" in df else df[["loc"]]
        except Exception as e:
            errors.append(f"{sm}: {e}")
    
    raise RuntimeError("No sitemap found/parsed. Tried:\n" + "\n".join(errors))


def pick_pages(df: pd.DataFrame, max_pages: int = 30) -> list:
    """Select best pages from sitemap based on relevance"""
    urls = df["loc"].dropna().astype(str).tolist()
    urls = list(dict.fromkeys(urls))
    
    # Prioritize Arabic pages
    arabic = [u for u in urls if "/en/" not in u.lower()]
    rest = [u for u in urls if u not in arabic]
    
    def score(u: str) -> int:
        """Score URL based on relevant keywords"""
        path = urlparse(u).path.lower()
        hits = 0
        keywords = [
            "about", "من-نحن", "نبذة", "services", "الخدمات",
            "contact", "تواصل", "vision", "الرؤية", "mission", "الرسالة",
            "why-us", "لماذا", "projects", "مشاريع", "portfolio", "أعمال"
        ]
        for kw in keywords:
            if kw in path:
                hits += 1
        return hits
    
    arabic_sorted = sorted(arabic, key=score, reverse=True)
    selected = (arabic_sorted + rest)[:max_pages]
    
    return selected


def extract_company_info_with_advertools(root_url: str, max_pages: int = 30, api_key=None) -> dict:
    """
    Main function: Extract company information from website using sitemap
    
    Args:
        root_url: Website root URL (e.g., "https://example.com")
        max_pages: Maximum number of pages to scrape (default: 30)
        api_key: OpenAI API key (optional, uses env var if not provided)
    
    Returns:
        Dictionary containing extracted company information
    """
    print(f"🌐 Starting extraction for: {root_url}")
    print(f"📋 Loading sitemap...")
    
    df = load_sitemap_urls(root_url)
    selected = pick_pages(df, max_pages=max_pages)
    
    print(f"✅ Selected {len(selected)} pages from sitemap")
    
    return extract_company_info_from_urls(selected, api_key=api_key)


# ===================== Main Execution =====================

if __name__ == "__main__":
    # Example usage
    ROOT_URL = "https://rnec.sa"  # Change this to your target website
    
    try:
        data = extract_company_info_with_advertools(ROOT_URL, max_pages=25)
        
        # Print results
        print("\n" + "="*50)
        print("📊 EXTRACTION RESULTS")
        print("="*50)
        print(json.dumps(data, ensure_ascii=False, indent=2))
        
        # Save to file
        output_file = "company_info.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n✅ تم حفظ الملف: {output_file}")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
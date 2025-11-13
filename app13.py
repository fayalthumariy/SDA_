"""
RFP Proposal Generator - Streamlit App
Multi-page application for RFP processing and proposal generation
"""

import streamlit as st
import os
import json
from datetime import datetime

# ============================================
# Setup
# ============================================
# Set page config
st.set_page_config(
    page_title="RFP Proposal Generator",
    page_icon="📄",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for beautiful design
st.markdown("""
<style>
    /* Main theme colors */
    :root {
        --primary-color: #2E7D32;
        --secondary-color: #1976D2;
        --accent-color: #FF6F00;
        --background-light: #F5F7FA;
        --text-dark: #1A1A1A;
        --border-radius: 15px;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
    }
    
    /* Content block styling */
    .block-container {
        background: white;
        border-radius: 20px;
        padding: 3rem 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        max-width: 1400px;
        margin: 0 auto;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3c72 0%, #2a5298 100%);
        padding: 2rem 1rem;
    }
    
    [data-testid="stSidebar"] .element-container {
        color: white !important;
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p {
        color: white !important;
    }
    
    /* Title styling */
    h1 {
        color: #1A1A1A;
        font-size: 2.5rem !important;
        font-weight: 700 !important;
        margin-bottom: 1.5rem !important;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    h2 {
        color: #2E7D32;
        font-size: 1.8rem !important;
        font-weight: 600 !important;
        margin: 2rem 0 1rem 0 !important;
    }
    
    h3 {
        color: #1976D2;
        font-size: 1.4rem !important;
        font-weight: 600 !important;
    }
    
    /* Button styling */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }
    
    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }
    
    .stButton > button:active {
        transform: translateY(0);
    }
    
    /* Disabled button */
    .stButton > button:disabled {
        background: #cccccc;
        box-shadow: none;
        cursor: not-allowed;
    }
    
    /* File uploader styling */
    [data-testid="stFileUploader"] {
        background: #F8F9FA;
        border: 2px dashed #667eea;
        border-radius: 15px;
        padding: 2rem;
        transition: all 0.3s ease;
    }
    
    [data-testid="stFileUploader"]:hover {
        border-color: #764ba2;
        background: #F0F4FF;
    }
    
    /* Success/Warning/Error boxes */
    .stSuccess {
        background: linear-gradient(135deg, #00C9A7 0%, #00B894 100%);
        color: white;
        border-radius: 12px;
        padding: 1rem;
        border: none;
    }
    
    .stWarning {
        background: linear-gradient(135deg, #FFB900 0%, #FF8C00 100%);
        color: white;
        border-radius: 12px;
        padding: 1rem;
        border: none;
    }
    
    .stError {
        background: linear-gradient(135deg, #FF6B6B 0%, #EE5A6F 100%);
        color: white;
        border-radius: 12px;
        padding: 1rem;
        border: none;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #4FC3F7 0%, #29B6F6 100%);
        color: white;
        border-radius: 12px;
        padding: 1rem;
        border: none;
    }
    
    /* Progress bar */
    .stProgress > div > div > div > div {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        border-radius: 10px;
    }
    
    /* Chat message bubbles */
    .ai-message {
        background: linear-gradient(135deg, #E8EAF6 0%, #C5CAE9 100%);
        padding: 1.2rem;
        border-radius: 18px 18px 18px 4px;
        margin: 1rem 0;
        margin-left: 10%;
        text-align: right;
        box-shadow: 0 2px 10px rgba(0,0,0,0.08);
        animation: slideIn 0.3s ease;
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.2rem;
        border-radius: 18px 18px 4px 18px;
        margin: 1rem 0;
        margin-right: 10%;
        text-align: right;
        box-shadow: 0 2px 10px rgba(102, 126, 234, 0.3);
        animation: slideIn 0.3s ease;
    }
    
    .message-label {
        font-weight: 700;
        font-size: 0.9rem;
        margin-bottom: 0.5rem;
        opacity: 0.9;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Text input/textarea */
    .stTextInput > div > div > input,
    .stTextArea > div > div > textarea {
        border-radius: 12px;
        border: 2px solid #E0E0E0;
        padding: 0.75rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput > div > div > input:focus,
    .stTextArea > div > div > textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Metrics */
    [data-testid="stMetric"] {
        background: linear-gradient(135deg, #F8F9FA 0%, #E9ECEF 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
    }
    
    [data-testid="stMetric"] label {
        font-size: 1rem !important;
        color: #666 !important;
        font-weight: 600 !important;
    }
    
    [data-testid="stMetric"] [data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
        color: #667eea !important;
    }
    
    /* Divider */
    hr {
        margin: 2rem 0;
        border: none;
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
    }
    
    /* Expander */
    .streamlit-expanderHeader {
        background: linear-gradient(135deg, #F8F9FA 0%, #E9ECEF 100%);
        border-radius: 12px;
        padding: 1rem;
        font-weight: 600;
    }
    
    /* Download button */
    .stDownloadButton > button {
        background: linear-gradient(135deg, #00C9A7 0%, #00B894 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        box-shadow: 0 4px 15px rgba(0, 201, 167, 0.4);
    }
    
    .stDownloadButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 201, 167, 0.6);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
    
    /* Columns */
    [data-testid="column"] {
        padding: 0.5rem;
    }
    
    /* Caption */
    .caption {
        color: #666;
        font-size: 0.9rem;
        margin-top: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)

# Setup API Key
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

# ============================================
# Session State Initialization
# ============================================
if 'page' not in st.session_state:
    st.session_state.page = 1

if 'rfp_uploaded' not in st.session_state:
    st.session_state.rfp_uploaded = False

if 'company_uploaded' not in st.session_state:
    st.session_state.company_uploaded = False

if 'processing_done' not in st.session_state:
    st.session_state.processing_done = False

if 'questions' not in st.session_state:
    st.session_state.questions = []

if 'current_question_index' not in st.session_state:
    st.session_state.current_question_index = 0

if 'answers' not in st.session_state:
    st.session_state.answers = {}

if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

if 'first_question_added' not in st.session_state:
    st.session_state.first_question_added = False

if 'additional_info_asked' not in st.session_state:
    st.session_state.additional_info_asked = False

if 'proposal_generated' not in st.session_state:
    st.session_state.proposal_generated = False

if 'conversation_model' not in st.session_state:
    st.session_state.conversation_model = None

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'waiting_for_answer' not in st.session_state:
    st.session_state.waiting_for_answer = True

if 'current_answer_collected' not in st.session_state:
    st.session_state.current_answer_collected = False

if 'show_regenerate_input' not in st.session_state:
    st.session_state.show_regenerate_input = False


# ============================================
# PAGE 1: Upload Files
# ============================================
def page_upload():
    # ─────────────────────────────────────────
    # Title (already good in your theme)
    # ─────────────────────────────────────────
    st.markdown("""
    <div style='text-align:center; padding: 2rem 0;'>
        <h1 style='font-size:3rem; margin-bottom:0.4rem;'>وِفاق</h1>
        <p style='font-size:1.1rem; color:#666; font-weight:500;'>نظام ذكي لتحليل المتطلبات وتوليد عروض فنية متكاملة</p>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # ─────────────────────────────────────────
    # (1) Centered step header + helper text
    # ─────────────────────────────────────────
    st.markdown("""
    <div style="
        text-align:center;
        background: linear-gradient(135deg, #E8EAF6 0%, #C5CAE9 100%);
        padding: 1.25rem 1rem;
        border-radius: 15px;
        margin: 0 auto 2rem auto;">
        <h3 style="color:#5E35B1; margin:0 0 0.4rem 0;">الخطوة الأولى: رفع المستندات الأساسية</h3>
        <div style="color:#666; font-size:0.98rem;">
            يرجى رفع المستندات المطلوبة لبدء تحليل المتطلبات الفنية ومطابقة قدرات الشركة مع نطاق العمل
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Two equal columns
    col1, col2 = st.columns(2, gap="large")

    # ─────────────────────────────────────────
    # Left card: RFP uploader
    # ─────────────────────────────────────────
    with col1:
        st.markdown("""
        <div style="background:white; padding:1.25rem; border-radius:15px; border:2px solid #E8EAF6; margin-bottom:0.75rem;">
            <h3 style="margin:0; color:#5E35B1; text-align:center;">(RFP) وثيقة طلب العرض</h3>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="text-align:center; margin-bottom:0.6rem; font-size:0.95rem; color:#777;">
            PDF : صيغة الملف المطلوبة
        </div>
        """, unsafe_allow_html=True)

        # --- Compact style for ALL file uploaders on the page ---
        st.markdown("""
        <style>
        /* Make the uploader look like a single-line input */
        div[data-testid="stFileUploader"] {
            padding: 8 !important;
            background: #FFFFFF !important;
            border: 1px dashed #667eea !important; 
            border-radius: 8px !important;
            box-shadow: none !important; 
        }

        /* Shrink inner sections/paddings */
        div[data-testid="stFileUploader"] section {
            padding: 4px 4px !important;
            min-height: 4px !important;   /* height similar to a text input */
        }

        /* Reduce dropzone padding to zero */
        div[data-testid="stFileUploader"] [data-testid="stFileUploaderDropzone"] {
            padding: 0 !important;
            min-height: 0 !important;
            border: none !important;        /* remove nested border */
        }

        /* Hide the big default label inside the dropzone */
        div[data-testid="stFileUploader"] label {
            display: none !important;
        }

        /* Keep uploaded-file chip tight */
        div[data-testid="stFileUploader"] .uploadedFile {
            margin: 15px 16px !important;
        }
        </style>
        """, unsafe_allow_html=True)

        # Small caption (optional)
        #st.markdown("<div style='font-size:0.9rem; color:#555; margin:0 4px 6px;'>📄 ارفع ملف وثيقة طلب العرض (PDF)</div>", unsafe_allow_html=True)


        rfp_file = st.file_uploader(
                                    label=" ",                      # keep label collapsed
                                    type=["pdf"],
                                    key="rfp_uploader",
                                    label_visibility="collapsed",
                                    accept_multiple_files=False,
                                    help="ملف وثيقة طلب العرض / كراسة الشروط والمواصفات"
                                )

        # rfp_file = st.file_uploader(
        #     label=" ",  # hide default label
        #     type=["pdf"],
        #     key="rfp_uploader",
        #     help="ملف وثيقة طلب العرض / كراسة الشروط والمواصفات"
        # )
        

        if rfp_file:
            # Save to disk
            os.makedirs("data/uploads", exist_ok=True)
            rfp_path = f"data/uploads/rfp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            with open(rfp_path, "wb") as f:
                f.write(rfp_file.getbuffer())

            st.session_state.rfp_uploaded = True
            st.session_state.rfp_path = rfp_path

            # subtle inline success under the uploader
            # st.markdown(f"""
            # <div style="margin-top:0.75rem; background:#E8F5E9; color:#2E7D32; padding:0.6rem 0.9rem; border-radius:10px; text-align:center;">
            #     تم رفع ملف RFP: {rfp_file.name}
            # </div>
            # """, unsafe_allow_html=True)

    # ─────────────────────────────────────────
    # Right card: website input (styled like the uploader)
    # ─────────────────────────────────────────
    with col2:
        st.markdown("""
        <div style="background:white; padding:1.25rem; border-radius:15px; border:2px solid #E8EAF6; margin-bottom:0.75rem;">
            <h3 style="margin:0; color:#5E35B1; text-align:center;"> موقع الشركة</h3>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <div style="text-align:center; margin-bottom:0.6rem; font-size:0.95rem; color:#777;">
            يرجى إدخال رابط موقع الشركة لاستخراج البيانات والخبرات<br/>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("""
                <style>
                /* make the company URL input the same size and look as the uploader */
                div[data-testid="stTextInput"] {
                    padding: 0 !important;
                    background: #FFFFFF !important;
                    border: 2px dashed #667eea !important;
                    border-radius: 12px !important;
                    box-shadow: none !important;
                    height: 46px !important;      /* same height */
                    display: flex !important;
                    align-items: center !important;
                }

                /* inner text field */
                div[data-testid="stTextInput"] input {
                    height: 44px !important;
                    font-size: 0.9rem !important;
                    border: none !important;
                    box-shadow: none !important;
                    background: transparent !important;
                    text-align: right;  /* keep Arabic direction clean */
                    direction: rtl;
                    padding-right: 12px;
                }

                /* on focus */
                div[data-testid="stTextInput"] input:focus {
                    outline: none !important;
                    border: none !important;
                    box-shadow: none !important;
                }
                </style>
                """, unsafe_allow_html=True)

        # Just the input (CSS above makes its container dashed & padded)
        company_url = st.text_area(
            label=" ",
            key="company_url_input",
            placeholder="https://www.example.com",
            help="رابط موقع الشركة"
        )

        if company_url and company_url.strip():
            if company_url.startswith("http://") or company_url.startswith("https://"):
                st.session_state.company_uploaded = True
                st.session_state.company_url = company_url.strip()
                # st.markdown(f"""
                # <div style="margin-top:0.75rem; background:#E8F5E9; color:#2E7D32; padding:0.6rem 0.9rem; border-radius:10px; text-align:center;">
                #     ✅ تم إدخال رابط الموقع: {company_url}
                # </div>
                # """, unsafe_allow_html=True)
            else:
                st.session_state.company_uploaded = False
                st.markdown("""
                <div style="margin-top:0.75rem; background:#FDECEA; color:#C62828; padding:0.6rem 0.9rem; border-radius:10px; text-align:center;">
                    ⚠️ يرجى إدخال رابط صحيح يبدأ بـ http:// أو https://
                </div>
                """, unsafe_allow_html=True)

    # ─────────────────────────────────────────
    # (4 + 5) Centered success (no yellow warnings at all)
    # ─────────────────────────────────────────
    if st.session_state.rfp_uploaded and st.session_state.company_uploaded:
        st.markdown("""
        <div style="
            text-align:center;
            background:linear-gradient(135deg,#E8F5E9 0%,#C8E6C9 100%);
            color:#2E7D32;
            border-radius:12px;
            padding:1rem 0;
            font-weight:700;
            font-size:1.15rem;
            margin:1.2rem auto;">
             تم رفع جميع الملفات المطلوبة 
        </div>
        """, unsafe_allow_html=True)

    # ─────────────────────────────────────────
    # Next button (centered)
    # ─────────────────────────────────────────
    st.markdown("<div style='height:0.5rem;'></div>", unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        next_disabled = not (st.session_state.rfp_uploaded and st.session_state.company_uploaded)

        if st.button("التالي", disabled=next_disabled, use_container_width=True, type="primary"):
            # right-aligned status above the spinner
            status = st.empty()
            status.markdown(
                "<div style='text-align:right; direction:rtl;'>جاري فحص الملفات والتأكد من سلامة البيانات</div>",
                unsafe_allow_html=True,
            )

            with st.spinner(" "):        # blank text inside spinner
                ok = process_files()

            status.empty()               # remove the status line

            if ok:
                st.session_state.page = 2
                st.rerun()
            else:
                st.error("حدث خطأ في معالجة الملفات")
# ============================================
# Initialize Conversational AI
# ============================================
def initialize_chatbot(current_question, question_index, total_questions):
    """Initialize conversational chatbot for current question"""
    from langchain_openai import ChatOpenAI
    
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
    
    system_prompt = f"""أنت مساعد ذكي متخصص في جمع معلومات للعطاءات والمناقصات.

السؤال الحالي ({question_index + 1} من {total_questions}):
{current_question}

مهمتك:
1. إذا سألك المستخدم استفساراً أو طلب توضيح - أجب عليه بوضوح
2. إذا أعطاك المستخدم إجابة كاملة - قل له "شكراً، تم تسجيل إجابتك" 
3. كن مهذباً ورسمياً
4. ساعده على فهم السؤال إذا احتاج
5. لا تنتقل للسؤال التالي - فقط ساعده بالسؤال الحالي

عند تأكيد الإجابة، استخدم العبارة الدقيقة: "✅ تم تسجيل إجابتك"
"""
    
    return model, system_prompt


def get_ai_response(user_message, model, conversation_history):
    """Get AI response for user message"""
    
    # Add user message to history
    conversation_history.append({"role": "user", "content": user_message})
    
    # Get AI response
    messages = [{"role": msg["role"], "content": msg["content"]} for msg in conversation_history]
    response = model.invoke(messages)
    ai_message = response.content
    
    # Add AI response to history
    conversation_history.append({"role": "assistant", "content": ai_message})
    
    return ai_message, conversation_history


def is_answer_confirmed(ai_message):
    """Check if AI confirmed the answer"""
    confirmation_phrases = [
        "تم تسجيل إجابتك",
        "✅ تم تسجيل",
        "شكراً، تم تسجيل"
    ]
    return any(phrase in ai_message for phrase in confirmation_phrases)


# ============================================
# File Processing Function
# ============================================
# ============================================
# File Processing Function
# ============================================
def process_files():
    """Process uploaded files and extract questions"""
    try:
        from modules.rfp_extractor import extract_and_weight_rfp_criteria
        from modules.company_extractor import extract_company_info_with_advertools
        from modules.gap_analyzer import perform_full_gap_analysis
        import json
        
        # Step 1: Extract RFP
        rfp_result = extract_and_weight_rfp_criteria(
            pdf_path=st.session_state.rfp_path,
            output_file="data/outputs/criteria_with_weights.json"
        )
        
        # Step 2: Extract Company Profile from Website
        company_result = extract_company_info_with_advertools(
            root_url=st.session_state.company_url,
            max_pages=25
        )
        
        # Save company profile to file
        os.makedirs("data/outputs", exist_ok=True)
        with open("data/outputs/company_profile.json", 'w', encoding='utf-8') as f:
            json.dump(company_result, f, ensure_ascii=False, indent=2)
        
        # Step 3: Gap Analysis
        gap_result = perform_full_gap_analysis(
            rfp_criteria_file="data/outputs/criteria_with_weights.json",
            company_profile_file="data/outputs/company_profile.json",
            output_file="data/outputs/gap_analysis.json"
        )
        
        # Load questions
        st.session_state.questions = gap_result.get('clarification_questions', [])
        st.session_state.processing_done = True
        
        st.success(f"✅ تم استخراج {len(st.session_state.questions)} سؤال")
        
        return True
        
    except Exception as e:
        st.error(f"خطأ: {str(e)}")
        import traceback
        st.code(traceback.format_exc())
        return False


# ============================================
# PAGE 2: Chatbot (ChatGPT Style)
# ============================================
def page_chatbot():
    st.markdown("""
    <div style='text-align: center; padding: 1.5rem 0;'>
        <h1 style='font-size: 2.5rem; margin-bottom: 0.5rem;'>
              وِفاق
        </h1>
        <p style='font-size: 1.1rem; color: #666;'>
            الرجاء الاجابة على الأسئلة وتوضيح المعلومات الناقصة
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if there are questions
    if not st.session_state.questions:
        st.success(" لا توجد فجوات - الشركة تلبي جميع المتطلبات!")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("إنشاء العرض الفني", use_container_width=True, type="primary"):
                st.session_state.page = 3
                st.rerun()
        return
    
    # Progress bar at top
    total_questions = len(st.session_state.questions)
    current_index = st.session_state.current_question_index
    progress = current_index / total_questions if not st.session_state.additional_info_asked else 1.0
    
    st.progress(progress)
    st.markdown(
        f"<p style='text-align:right; direction:rtl; color:gray; font-size:0.9rem; margin:0;'>السؤال {current_index+1} من {total_questions}</p>",
        unsafe_allow_html=True
)
    #st.markdown("---")
    
    # Add first question to history if not added yet
    if not st.session_state.first_question_added and current_index == 0 and total_questions > 0:
        st.session_state.chat_history.append({
            'type': 'question',
            'index': 0,
            'content': st.session_state.questions[0]
        })
        st.session_state.first_question_added = True
    
    # Chat container with custom CSS
    st.markdown("""
    <style>
    .ai-message {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0;
        margin-left: 20%;
        text-align: right;
    }
    .user-message {
        background-color: #e3f2fd;
        padding: 15px;
        border-radius: 15px;
        margin: 10px 0;
        margin-right: 20%;
        text-align: right;
    }
    .message-label {
        font-weight: bold;
        margin-bottom: 5px;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Chat history display
    chat_container = st.container()
    with chat_container:
        # Display all previous messages
        for entry in st.session_state.chat_history:
            if entry['type'] == 'question':
                st.markdown(f"""
                <div class="ai-message">
                    <div class="message-label"> وِفاق - السؤال {entry['index'] + 1}</div>
                    <div>{entry['content']}</div>
                </div>
                """, unsafe_allow_html=True)
            elif entry['type'] == 'answer':
                st.markdown(f"""
                <div class="user-message">
                    <div class="message-label"> أنت</div>
                    <div>{entry['content']}</div>
                </div>
                """, unsafe_allow_html=True)
            elif entry['type'] == 'user_message':
                st.markdown(f"""
                <div class="user-message">
                    <div class="message-label"> أنت</div>
                    <div>{entry['content']}</div>
                </div>
                """, unsafe_allow_html=True)
            elif entry['type'] == 'ai_response':
                st.markdown(f"""
                <div class="ai-message">
                    <div class="message-label"> وِفاق</div>
                    <div>{entry['content']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Show additional info question if all questions answered
        if not st.session_state.additional_info_asked and current_index >= total_questions:
            st.markdown(f"""
            <div class="ai-message">
                <div class="message-label"> وِفاق</div>
                <div>هل ترغب بإضافة أي معلومات إضافية لدمجها داخل العرض الفني؟</div>
                <div style="margin-top:10px; font-size:0.9em; color:#666;">
                (مثل: شهادات، جوائز، مشاريع سابقة، ميزات تنافسية)
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    #st.markdown("---")
    
    # Input area at bottom (ChatGPT style with conversational AI)
    if not st.session_state.additional_info_asked:
        if current_index < total_questions:
            # Initialize chatbot for current question if not initialized
            if st.session_state.conversation_model is None:
                from langchain_openai import ChatOpenAI
                st.session_state.conversation_model = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)
                
                # Initialize conversation with system prompt
                system_msg = f"""أنت مساعد ذكي متخصص في جمع معلومات للعطاءات والمناقصات.

السؤال الحالي ({current_index + 1} من {total_questions}):
{st.session_state.questions[current_index]}

مهمتك:
1. إذا سألك المستخدم استفساراً أو طلب توضيح - أجب عليه بوضوح ومهنياً
2. إذا أعطاك المستخدم إجابة كاملة للسؤال - قل "✅ شكراً، تم تسجيل إجابتك. سننتقل للسؤال التالي"
3. كن مهذباً ورسمياً
4. ساعده على فهم السؤال إذا احتاج
5. لا تنتقل للسؤال التالي بنفسك - فقط ساعده بالسؤال الحالي

قواعد مهمة:
- إذا كانت الإجابة واضحة وكاملة، أكد التسجيل باستخدام: "✅ شكراً، تم تسجيل إجابتك"
- إذا كانت الإجابة ناقصة، اطلب التوضيح
- إذا كان سؤال استفساري، أجب عليه بوضوح
"""
                st.session_state.conversation_history = [
                    {"role": "system", "content": system_msg}
                ]
            
            # Regular question input with AI conversation
            col1, col2 = st.columns([5, 1])
            
            # Use session state to control input value
            if f'input_value_{current_index}' not in st.session_state:
                st.session_state[f'input_value_{current_index}'] = ''
            
            with col1:
                # Custom CSS to align text area to the right (RTL)
                st.markdown("""
                    <style>
                    /* Make text area content RTL and aligned right */
                    textarea {
                        direction: rtl;
                        text-align: right;
                        font-family: "Tajawal", "Cairo", sans-serif;
                        font-size: 1rem;
                    }
                    /* Align the whole text area container to the right */
                    div[data-testid="stTextArea"] {
                        direction: rtl;
                        text-align: right;
                    }
                    </style>
                    """, unsafe_allow_html=True)

                user_input = st.text_area(
                    "",
                    value=st.session_state[f'input_value_{current_index}'],
                    key=f"chat_input_{current_index}",
                    height=100,
                    placeholder="اكتب إجابتك أو استفسارك هنا",
                    label_visibility="collapsed"
                )
            with col2:
                st.write("")  # spacing
                st.write("")  # spacing
                send_button = st.button("إرسال ", use_container_width=True, type="primary")
            
            if send_button and user_input.strip():
                # Clear input box
                st.session_state[f'input_value_{current_index}'] = ''
                
                # Add user message to chat history display
                st.session_state.chat_history.append({
                    'type': 'user_message',
                    'index': current_index,
                    'content': user_input
                })
                
                # Get AI response
                st.session_state.conversation_history.append({
                    "role": "user",
                    "content": user_input
                })
                
                messages = [
                    {"role": msg["role"], "content": msg["content"]} 
                    for msg in st.session_state.conversation_history
                ]
                response = st.session_state.conversation_model.invoke(messages)
                ai_message = response.content
                
                st.session_state.conversation_history.append({
                    "role": "assistant",
                    "content": ai_message
                })
                
                # Add AI response to chat history display
                st.session_state.chat_history.append({
                    'type': 'ai_response',
                    'index': current_index,
                    'content': ai_message
                })
                
                # Check if answer is confirmed
                if "✅" in ai_message and "تم تسجيل" in ai_message:
                    # Save the actual answer (the user's last substantive message)
                    # Find the last user message that looks like an answer
                    user_messages = [
                        msg['content'] for msg in st.session_state.conversation_history 
                        if msg['role'] == 'user'
                    ]
                    
                    if user_messages:
                        st.session_state.answers[current_index] = {
                            'question': st.session_state.questions[current_index],
                            'answer': user_messages[-1],  # Last user message
                            'full_conversation': st.session_state.conversation_history.copy()
                        }
                    
                    # Reset for next question
                    st.session_state.current_question_index += 1
                    st.session_state.conversation_model = None
                    st.session_state.conversation_history = []
                    
                    # Add next question to history if available
                    if st.session_state.current_question_index < total_questions:
                        st.session_state.chat_history.append({
                            'type': 'question',
                            'index': st.session_state.current_question_index,
                            'content': st.session_state.questions[st.session_state.current_question_index]
                        })
                
                st.rerun()
        
        else:
            # Additional info input
            col1, col2 = st.columns([5, 1])
            with col1:
                additional_input = st.text_area(
                    "",
                    key="additional_info_input",
                    height=100,
                    placeholder="اكتب المعلومات الإضافية أو اتركه فارغاً واضغط إرسال...",
                    label_visibility="collapsed"
                )
            with col2:
                st.write("")  # spacing
                st.write("")  # spacing
                finish_button = st.button("إرسال", use_container_width=True, type="primary")
            
            if finish_button:
                st.session_state.additional_info = additional_input if additional_input.strip() else None
                st.session_state.additional_info_asked = True
                
                # Add to chat history
                if additional_input.strip():
                    st.session_state.chat_history.append({
                        'type': 'answer',
                        'index': -1,
                        'content': additional_input
                    })
                else:
                    st.session_state.chat_history.append({
                        'type': 'answer',
                        'index': -1,
                        'content': "لا توجد معلومات إضافية"
                    })
                
                # Save chat history
                save_chat_history()
                
                st.rerun()
    
    else:
        st.markdown(
    """
    <div style="
        text-align: center;
        direction: rtl;
        background-color: #E8F5E9;
        color: #2E7D32;
        border-radius: 10px;
        padding: 12px;
        font-size: 1.2rem;
        font-weight: 600;
        width: 80%;
        margin: 1rem auto;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    ">
         تم الانتهاء من جمع المعلومات
    </div>
    """,
    unsafe_allow_html=True
)
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            count = len(st.session_state.answers)
            extra_msg = "تم إضافة معلومات إضافية" if st.session_state.additional_info else "لا توجد معلومات إضافية"

            st.markdown(f"""
            <div style="
                direction: rtl;
                text-align: center;
                margin: 0.5rem auto 0;
                background: linear-gradient(135deg, #F8F9FA 0%, #E9ECEF 100%);
                border-radius: 22px;
                padding: 24px 18px;
                box-shadow: 0 8px 24px rgba(0,0,0,0.06);
                max-width: 100%;
            ">
                <div style="font-size:1.1rem; color:#607D8B; margin-bottom:6px;">عدد الأسئلة</div>
                <div style="font-size:2.2rem; font-weight:800; color:#667eea; margin-bottom:12px;">{count}</div>
                <div style="
                    display:inline-block;
                    padding:8px 14px;
                    border-radius:12px;
                    background:#E8F0FE;
                    color:#1A73E8;
                    font-size:1rem;
                ">{extra_msg}</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("الانتقال لتوليد عرض وِفاق", use_container_width=True, type="primary"):
                st.session_state.page = 3
                st.rerun()
# ============================================
# Save Chat History
# ============================================
def save_chat_history():
    """Save complete chat session to file"""
    session_data = {
        "timestamp": datetime.now().isoformat(),
        "total_questions": len(st.session_state.questions),
        "questions": st.session_state.questions,
        "answers": st.session_state.answers,
        "chat_history": st.session_state.chat_history,
        "additional_info": st.session_state.additional_info
    }
    
    os.makedirs("data/outputs", exist_ok=True)
    with open("data/outputs/chat_history.json", 'w', encoding='utf-8') as f:
        json.dump(session_data, f, ensure_ascii=False, indent=2)


# ============================================
# PAGE 3: Generate Proposal
# ============================================
#headline of the page

# 
# 
def generate_proposal_workflow():
    """Run the proposal generation workflow"""
    
    with st.spinner("جاري توليد العرض... (قد يستغرق 2-5 دقائق)"):
        try:
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            from modules.proposal_generator import generate_proposal
            
            proposal = generate_proposal(
                rfp_criteria_file="data/outputs/criteria_with_weights.json",
                company_profile_file="data/outputs/company_profile.json",
                gap_analysis_file="data/outputs/gap_analysis.json",
                chat_history_file="data/outputs/chat_history.json",
                output_file="data/outputs/proposal.md",
                generate_word=True
            )
            
            progress_bar.progress(100)
            
            # Mark as generated in session
            st.session_state.proposal_generated = True
            
            # الحل: rerun مباشرة
            st.rerun()
            
        except FileNotFoundError as e:
            st.error(f" خطأ: ملف مفقود - {e}")
            st.info(" تأكد من إكمال جميع الخطوات السابقة")
            
        except Exception as e:
            st.error(f" حدث خطأ: {e}")
            with st.expander("تفاصيل الخطأ"):
                import traceback
                st.code(traceback.format_exc())
    def page_proposal():
        st.markdown("""
        <div style='text-align: center; padding: 1.5rem 0;'>
            <h1 style='font-size: 2.5rem; margin-bottom: 0.5rem;'>
                العرض الفني
            </h1>
            <p style='font-size: 1.1rem; color: #666;'>
                
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        st.markdown(
        """
        <div style='text-align:center; direction:rtl;'>
            <h3 style='font-weight:600; color:#1A237E;'>المعلومات المدخلة</h3>
        </div>
        """,
        unsafe_allow_html=True
    )

    # Center everything
    col_space_left, col_center, col_space_right = st.columns([1, 3, 1])
    with col_center:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("متطلبات المناقصة", "جاهز")
        with col2:
            st.metric("معلومات الشركة", "جاهز")
    with col3:
        answers_count = len(st.session_state.answers)
        st.metric("إجابات الاستفسارات", f"{answers_count} سؤال")

    # Centered success message
    st.markdown(
        """
        <div style='text-align:center; direction:rtl; background-color:#E8F5E9;
                    color:#2E7D32; border-radius:10px; padding:10px; 
                    margin-top:10px; font-weight:500; font-size:1rem;'>
            تم جمع المعلومات المطلوبة 
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Check if previous steps are completed
    if not st.session_state.additional_info_asked:
        st.warning(" يجب إكمال جمع المعلومات أولاً")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button(" العودة للمحادثة", use_container_width=True):
                st.session_state.page = 2
                st.rerun()
        return
    
# Summary of collected data

    
    st.markdown("---")
    
    # ========== الفيتشرز الجديدة ==========
    if st.session_state.get('proposal_generated', False):
        # إذا ضغط "توليد جديد" → يطلع text box
        if st.session_state.get('show_regenerate_input', False):
            #st.markdown("---")
            st.markdown("""
            <div style='text-align: center; font-size: 1.2rem; font-weight: 600; margin-bottom: 1rem;'>
                هل ترغب بإضافة تعديلات أو نقاط تركيز جديدة في العرض الفني؟
            </div>
            """, unsafe_allow_html=True)
            
            col_input, col_btn = st.columns([5, 1])
            
            with col_input:
                regenerate_input = st.text_area(
                    "",
                    key="regenerate_input",
                    height=100,
                    placeholder="اكتب تعديلاتك أو اتركه فارغاً...",
                    label_visibility="collapsed"
                )
            
            with col_btn:
                st.write("")
                st.write("")
                if st.button("إرسال", use_container_width=True, type="primary", key="regenerate_submit"):
                    # حفظ التعديلات
                    if regenerate_input.strip():
                        st.session_state.additional_info = (st.session_state.get('additional_info', '') + 
                                                           "\n\n--- تعديلات جديدة ---\n" + 
                                                           regenerate_input)
                        save_chat_history()
                    
                    # إعادة التوليد
                    st.session_state.show_regenerate_input = False
                    st.session_state.proposal_generated = False
                    st.rerun()
        
        else:
            # 🔥 الزرين يطلعون مع بعض بعد التوليد
            st.markdown("""
                <div style="
                    text-align:center; direction:rtl;
                    background:#E8F5E9; color:#2E7D32;
                    border-radius:12px; padding:12px 16px;
                    font-weight:600; width:80%; margin:1rem auto;">
                    تم توليد عرض وِفاق بنجاح
                </div>
                """, unsafe_allow_html=True)
            
            proposal_docx_exists = os.path.exists("data/outputs/proposal.docx")
            proposal_md_exists = os.path.exists("data/outputs/proposal.md")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if proposal_docx_exists:
                    with open("data/outputs/proposal.docx", 'rb') as f:
                        docx_content = f.read()
                    
                    st.download_button(
                        label=" تحميل عرض وِفاق ",
                        data=docx_content,
                        file_name="عرض وِفاق.docx",
                        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                        use_container_width=True,
                        key="download_proposal_main"
                    )
                elif proposal_md_exists:
                    with open("data/outputs/proposal.md", 'r', encoding='utf-8') as f:
                        md_content = f.read()
                    
                    st.download_button(
                        label=" تحميل العرض (Markdown)",
                        data=md_content,
                        file_name="proposal.md",
                        mime="text/markdown",
                        use_container_width=True,
                        key="download_proposal_md"
                    )
            
            with col2:
                if st.button(" انشاء عرض وِفاق جديد", use_container_width=True, type="primary", key="btn_new_proposal"):
                    st.session_state.show_regenerate_input = True
                    st.rerun()
            
            # Show preview
            st.markdown("---")
            st.subheader(" معاينة العرض")
            
            if os.path.exists("data/outputs/proposal.md"):
                with open("data/outputs/proposal.md", 'r', encoding='utf-8') as f:
                    proposal_content = f.read()
                
                with st.expander("عرض المحتوى", expanded=False):
                    st.markdown(proposal_content)
    
    else:
        # Generate new proposal
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button(" توليد عرض وِفاق", use_container_width=True, type="primary", key="btn_generate_initial"):
                generate_proposal_workflow()

# def generate_proposal_workflow():
#     """Run the proposal generation workflow"""
    
#     with st.spinner("جاري توليد العرض... (قد يستغرق 2-5 دقائق)"):
#         try:
#             # Progress indicators
#             progress_bar = st.progress(0)
#             status_text = st.empty()
            
#             # # Import proposal generator
#             # status_text.text(" تحميل الموديول...")
#             # progress_bar.progress(10)
            
#             from modules.proposal_generator import generate_proposal
            
#             # # Generate proposal (both MD and Word)
#             # status_text.text(" بدء توليد الأقسام...")
#             # progress_bar.progress(30)
            
#             proposal = generate_proposal(
#                 rfp_criteria_file="data/outputs/criteria_with_weights.json",
#                 company_profile_file="data/outputs/company_profile.json",
#                 gap_analysis_file="data/outputs/gap_analysis.json",
#                 chat_history_file="data/outputs/chat_history.json",
#                 output_file="data/outputs/proposal.md",
#                 generate_word=True  # Generate Word document
#             )
            
#             progress_bar.progress(100)
#             #status_text.text(" !تم توليد العرض بنجاح")
            
#             # Mark as generated in session
#             st.session_state.proposal_generated = True
            
#             st.success(" تم توليد عرض وِفاق بنجاح")
            
#             # Check if Word was created
#             docx_exists = os.path.exists("data/outputs/proposal.docx")
            
#             if docx_exists:
#                 # Offer Word download
#                 with open("data/outputs/proposal.docx", 'rb') as f:
#                     docx_content = f.read()
                
#                 st.download_button(
#                     label=" تحميل عرض وِفاق ",
#                     data=docx_content,
#                     file_name="عرض وِفاق.docx",
#                     mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
#                     use_container_width=True
#                 )
#             else:
#                 # Fallback to markdown
#                 st.download_button(
#                     label=" تحميل العرض (Markdown)",
#                     data=proposal,
#                     file_name="proposal.md",
#                     mime="text/markdown",العرض الفني 
#                     use_container_width=True
#                 )
            
#             # Show preview
#             st.markdown("---")
#             st.subheader(" معاينة العرض")
            
#             with st.expander("عرض المحتوى", expanded=True):
#                 st.markdown(proposal)
            
#         except FileNotFoundError as e:
#             st.error(f" خطأ: ملف مفقود - {e}")
#             st.info(" تأكد من إكمال جميع الخطوات السابقة")
            
#         except Exception as e:
#             st.error(f" حدث خطأ: {e}")
#             with st.expander("تفاصيل الخطأ"):
#                 import traceback
#                 st.code(traceback.format_exc())


# ============================================
# Main App Logic
# ============================================
def main():
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 1rem 0; margin-bottom: 2rem;'>
            <h1 style='font-size: 2rem; color: white; margin: 0;'>
                📄
            </h1>
            <h2 style='font-size: 1.3rem; color: white; margin: 0.5rem 0;'>
                وِفاق
            </h2>
            <p style='color: rgba(255,255,255,0.8); font-size: 0.9rem; margin: 0;'>
                مولّد العروض الذكي
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        #st.markdown("---")
        
        # Show current page
        page_names = {
            1: " رفع الملفات",
            2: " جمع المعلومات",
            3: " توليد عرض وِفاق"
        }
        
        st.markdown("""
    <p style='color: rgba(255,255,255,0.8); 
              font-size: 0.9rem; 
              margin: 0; 
              text-align: right;
              direction: rtl;'>
         الصفحة الحالية :
    </p>
</div>
""", unsafe_allow_html=True)
        
        for page_num, page_name in page_names.items():
            if page_num == st.session_state.page:
                st.markdown(f"""
                <div style='background: rgba(255,255,255,0.2);
                            padding: 0.8rem;
                            border-radius: 8px;
                            margin-bottom: 0.5rem;
                            text-align: right;
                            direction: rtl;'>
                    <p style='color: white;
                            font-weight: 600;
                            margin: 0;
                            font-size: 1.1rem;'>
                         {page_name}  
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='padding: 0.8rem;
                            margin-bottom: 0.5rem;
                            text-align: right;
                            direction: rtl;'>
                    <p style='color: rgba(255,255,255,0.6);
                            margin: 0;'>
                        {page_name}
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        #st.markdown("---")
        # Status indicators
        # st.markdown("""
        # <div style='background: rgba(255,255,255,0.1); padding: 1rem; 
        #             border-radius: 10px;'>
        #     <p style='color: rgba(255,255,255,0.8); font-size: 0.9rem; margin-bottom: 1rem;'>
        #         حالة التقدم:
        #     </p>
        # </div>
        # """, unsafe_allow_html=True)
        
        status_items = []
        # if st.session_state.rfp_uploaded:
        #     status_items.append(("", "RFP مرفوع", True))
        # else:
        #     status_items.append(("", "RFP غير مرفوع", False))
        
        # if st.session_state.company_uploaded:
        #     status_items.append(("", "رابط الموقع مُدخل", True))
        # else:
        #     status_items.append(("", "رابط الموقع غير مُدخل", False))
        
        # if st.session_state.processing_done:
        #     questions_count = len(st.session_state.questions)
        #     status_items.append(("", f"تم استخراج {questions_count} سؤال", True))
        
        # if st.session_state.additional_info_asked:
        #     status_items.append(("", " تم استكمال جميع البيانات المطلوبة بنجاح.يمكنك الآن توليد العرض الفني النهائي.", True))
        
        for icon, text, is_complete in status_items:
            color = "rgba(76, 175, 80, 0.9)" if is_complete else "rgba(255,255,255,0.5)"
            st.markdown(f"""
            <div style='padding: 0.5rem; margin: 0.3rem 0;'>
                <p style='color: {color}; margin: 0; font-size: 0.95rem;'>
                    {icon} {text}
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    # Route to correct page
    if st.session_state.page == 1:
        page_upload()
    elif st.session_state.page == 2:
        page_chatbot()
    elif st.session_state.page == 3:
        page_proposal()


# ============================================
# Run App
# ============================================
if __name__ == "__main__":
    main()
#
############################
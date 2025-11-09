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

import streamlit as st
os.environ["OPENAI_API_KEY"] = st.secrets("OPENAI_API_KEY")

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

if 'conversation_model' not in st.session_state:
    st.session_state.conversation_model = None

if 'conversation_history' not in st.session_state:
    st.session_state.conversation_history = []

if 'waiting_for_answer' not in st.session_state:
    st.session_state.waiting_for_answer = True

if 'current_answer_collected' not in st.session_state:
    st.session_state.current_answer_collected = False


# ============================================
# PAGE 1: Upload Files
# ============================================
def page_upload():
    # Animated title with icon
    st.markdown("""
    <div style='text-align: center; padding: 2rem 0;'>
        <h1 style='font-size: 3rem; margin-bottom: 0.5rem;'>
            📄 مولّد العروض الفنية للمناقصات
        </h1>
        <p style='font-size: 1.2rem; color: #666; font-weight: 500;'>
            RFP Proposal Generator - نظام ذكي لإنشاء عروض احترافية
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    st.markdown("""
    <div style='background: linear-gradient(135deg, #E8EAF6 0%, #C5CAE9 100%); 
                padding: 1.5rem; border-radius: 15px; margin-bottom: 2rem;'>
        <h3 style='color: #5E35B1; margin: 0;'>📋 الخطوة 1: رفع الملفات</h3>
        <p style='color: #666; margin-top: 0.5rem;'>
            ارفع ملفات RFP والشركة لبدء عملية إنشاء العرض التلقائي
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2, gap="large")
    
    with col1:
        st.markdown("""
        <div style='background: white; padding: 1.5rem; border-radius: 15px; 
                    border: 2px solid #E8EAF6; margin-bottom: 1rem;'>
            <h3 style='color: #5E35B1; margin: 0; display: flex; align-items: center;'>
                📋 <span style='margin-right: 0.5rem;'>ملف RFP</span>
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        rfp_file = st.file_uploader(
            "ارفع ملف RFP (PDF)",
            type=['pdf'],
            key='rfp_uploader',
            help="ملف كراسة الشروط والمواصفات"
        )
        
        if rfp_file:
            # Save file
            os.makedirs("data/uploads", exist_ok=True)
            rfp_path = f"data/uploads/rfp_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            with open(rfp_path, "wb") as f:
                f.write(rfp_file.getbuffer())
            
            st.session_state.rfp_uploaded = True
            st.session_state.rfp_path = rfp_path
            st.success(f"✅ تم رفع ملف RFP: {rfp_file.name}")
    
    with col2:
        st.markdown("""
        <div style='background: white; padding: 1.5rem; border-radius: 15px; 
                    border: 2px solid #E8EAF6; margin-bottom: 1rem;'>
            <h3 style='color: #5E35B1; margin: 0; display: flex; align-items: center;'>
                🏢 <span style='margin-right: 0.5rem;'>ملف الشركة</span>
            </h3>
        </div>
        """, unsafe_allow_html=True)
        
        company_file = st.file_uploader(
            "ارفع ملف بروفايل الشركة (PDF)",
            type=['pdf'],
            key='company_uploader',
            help="ملف التعريف بالشركة وقدراتها"
        )
        
        if company_file:
            # Save file
            os.makedirs("data/uploads", exist_ok=True)
            company_path = f"data/uploads/company_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
            with open(company_path, "wb") as f:
                f.write(company_file.getbuffer())
            
            st.session_state.company_uploaded = True
            st.session_state.company_path = company_path
            st.success(f"✅ تم رفع ملف الشركة: {company_file.name}")
    
    st.markdown("---")
    
    # Status
    if st.session_state.rfp_uploaded and st.session_state.company_uploaded:
        st.success("✅ تم رفع جميع الملفات المطلوبة!")
    else:
        st.warning("⚠️ يرجى رفع كلا الملفين للمتابعة")
    
    # Next button
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        next_disabled = not (st.session_state.rfp_uploaded and st.session_state.company_uploaded)
        
        button_html = f"""
        <div style='text-align: center; margin: 2rem 0;'>
            {'<p style="color: #999; font-size: 0.9rem; margin-bottom: 1rem;">⚠️ يرجى رفع كلا الملفين للمتابعة</p>' if next_disabled else ''}
        </div>
        """
        st.markdown(button_html, unsafe_allow_html=True)
        
        if st.button(
            "🚀 التالي: تحليل الفجوات",
            disabled=next_disabled,
            use_container_width=True,
            type="primary"
        ):
            with st.spinner("جاري معالجة الملفات..."):
                # Process files
                success = process_files()
                
                if success:
                    st.session_state.page = 2
                    st.rerun()
                else:
                    st.error("❌ حدث خطأ في معالجة الملفات")


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
def process_files():
    """Process uploaded files and extract questions"""
    try:
        from modules.rfp_extractor import extract_and_weight_rfp_criteria
        from modules.company_extractor import extract_company_profile_from_pdf
        from modules.gap_analyzer import perform_full_gap_analysis
        
        # Step 1: Extract RFP
        st.write("📋 استخراج معايير RFP...")
        rfp_result = extract_and_weight_rfp_criteria(
            pdf_path=st.session_state.rfp_path,
            output_file="data/outputs/criteria_with_weights.json"
        )
        
        # Step 2: Extract Company Profile
        st.write("🏢 استخراج بروفايل الشركة...")
        company_result = extract_company_profile_from_pdf(
            pdf_path=st.session_state.company_path,
            output_file="data/outputs/company_profile.json"
        )
        
        # Step 3: Gap Analysis
        st.write("🔍 تحليل الفجوات...")
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
        return False


# ============================================
# PAGE 2: Chatbot (ChatGPT Style)
# ============================================
def page_chatbot():
    st.markdown("""
    <div style='text-align: center; padding: 1.5rem 0;'>
        <h1 style='font-size: 2.5rem; margin-bottom: 0.5rem;'>
            💬 مساعد جمع المعلومات الذكي
        </h1>
        <p style='font-size: 1.1rem; color: #666;'>
            تفاعل معنا للإجابة على الأسئلة وتوضيح المعلومات الناقصة
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if there are questions
    if not st.session_state.questions:
        st.success("✅ لا توجد فجوات - الشركة تلبي جميع المتطلبات!")
        
        col1, col2, col3 = st.columns([1, 1, 1])
        with col2:
            if st.button("الانتقال لتوليد العرض ⬅️", use_container_width=True, type="primary"):
                st.session_state.page = 3
                st.rerun()
        return
    
    # Progress bar at top
    total_questions = len(st.session_state.questions)
    current_index = st.session_state.current_question_index
    progress = current_index / total_questions if not st.session_state.additional_info_asked else 1.0
    
    st.progress(progress)
    st.caption(f"📊 السؤال {current_index} من {total_questions}")
    st.markdown("---")
    
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
                    <div class="message-label">🤖 المساعد - السؤال {entry['index'] + 1}</div>
                    <div>{entry['content']}</div>
                </div>
                """, unsafe_allow_html=True)
            elif entry['type'] == 'answer':
                st.markdown(f"""
                <div class="user-message">
                    <div class="message-label">👤 أنت</div>
                    <div>{entry['content']}</div>
                </div>
                """, unsafe_allow_html=True)
            elif entry['type'] == 'user_message':
                st.markdown(f"""
                <div class="user-message">
                    <div class="message-label">👤 أنت</div>
                    <div>{entry['content']}</div>
                </div>
                """, unsafe_allow_html=True)
            elif entry['type'] == 'ai_response':
                st.markdown(f"""
                <div class="ai-message">
                    <div class="message-label">🤖 المساعد</div>
                    <div>{entry['content']}</div>
                </div>
                """, unsafe_allow_html=True)
        
        # Show additional info question if all questions answered
        if not st.session_state.additional_info_asked and current_index >= total_questions:
            st.markdown(f"""
            <div class="ai-message">
                <div class="message-label">🤖 المساعد</div>
                <div>هل تود إضافة أي معلومات إضافية للعرض؟</div>
                <div style="margin-top:10px; font-size:0.9em; color:#666;">
                (مثل: شهادات، جوائز، مشاريع سابقة، ميزات تنافسية)
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    st.markdown("---")
    
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
                user_input = st.text_area(
                    "",
                    value=st.session_state[f'input_value_{current_index}'],
                    key=f"chat_input_{current_index}",
                    height=100,
                    placeholder="اكتب إجابتك أو استفسارك هنا...",
                    label_visibility="collapsed"
                )
            with col2:
                st.write("")  # spacing
                st.write("")  # spacing
                send_button = st.button("إرسال ⬆️", use_container_width=True, type="primary")
            
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
                finish_button = st.button("إرسال ⬆️", use_container_width=True, type="primary")
            
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
        # All done - show summary and next button
        st.success("✅ تم الانتهاء من جمع جميع المعلومات!")
        
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            st.metric("عدد الأسئلة", len(st.session_state.answers))
            if st.session_state.additional_info:
                st.info("✅ تم إضافة معلومات إضافية")
            
            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("الانتقال لتوليد العرض ⬅️", use_container_width=True, type="primary"):
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
def page_proposal():
    st.markdown("""
    <div style='text-align: center; padding: 1.5rem 0;'>
        <h1 style='font-size: 2.5rem; margin-bottom: 0.5rem;'>
            📄 توليد العرض الفني
        </h1>
        <p style='font-size: 1.1rem; color: #666;'>
            إنشاء عرض فني احترافي بالذكاء الاصطناعي
        </p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown("---")
    
    # Check if previous steps are completed
    if not st.session_state.additional_info_asked:
        st.warning("⚠️ يجب إكمال جمع المعلومات أولاً")
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("⬅️ العودة للمحادثة", use_container_width=True):
                st.session_state.page = 2
                st.rerun()
        return
    
    st.success("✅ تم جمع جميع المعلومات المطلوبة!")
    
    st.markdown("---")
    
    # Summary of collected data
    st.subheader("📊 ملخص البيانات المجمعة")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("معايير RFP", "✅ جاهز")
    
    with col2:
        st.metric("معلومات الشركة", "✅ جاهز")
    
    with col3:
        answers_count = len(st.session_state.answers)
        st.metric("الإجابات المجمعة", f"{answers_count} سؤال")
    
    st.markdown("---")
    
    # Generation section
    st.subheader("🚀 توليد العرض")
    
    st.info("""
    💡 **ملاحظة:** عملية توليد العرض قد تستغرق 2-5 دقائق حيث يقوم الذكاء الاصطناعي بـ:
    - تحليل جميع البيانات المجمعة
    - كتابة 16 قسم من العرض الفني
    - مراجعة وتنسيق المحتوى
    """)
    
    # Check if proposal already generated
    proposal_md_exists = os.path.exists("data/outputs/proposal.md")
    proposal_pdf_exists = os.path.exists("data/outputs/proposal.pdf")
    
    if proposal_pdf_exists or proposal_md_exists:
        st.success("✅ تم توليد عرض سابقاً")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 توليد عرض جديد", use_container_width=True, type="primary"):
                generate_proposal_workflow()
        
        with col2:
            # Prefer PDF if exists, otherwise MD
            if proposal_pdf_exists:
                with open("data/outputs/proposal.pdf", 'rb') as f:
                    pdf_content = f.read()
                
                st.download_button(
                    label="📥 تحميل العرض (PDF)",
                    data=pdf_content,
                    file_name="proposal.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            elif proposal_md_exists:
                with open("data/outputs/proposal.md", 'r', encoding='utf-8') as f:
                    md_content = f.read()
                
                st.download_button(
                    label="📥 تحميل العرض (Markdown)",
                    data=md_content,
                    file_name="proposal.md",
                    mime="text/markdown",
                    use_container_width=True
                )
        
        # Show preview
        st.markdown("---")
        st.subheader("👁️ معاينة العرض")
        
        # Read markdown for preview
        if proposal_md_exists:
            with open("data/outputs/proposal.md", 'r', encoding='utf-8') as f:
                proposal_content = f.read()
            
            with st.expander("عرض المحتوى", expanded=False):
                st.markdown(proposal_content)
    
    else:
        # Generate new proposal
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            if st.button("🎯 توليد العرض الفني", use_container_width=True, type="primary"):
                generate_proposal_workflow()


def generate_proposal_workflow():
    """Run the proposal generation workflow"""
    
    with st.spinner("🔄 جاري توليد العرض... (قد يستغرق 2-5 دقائق)"):
        try:
            # Progress indicators
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Import proposal generator
            status_text.text("📦 تحميل الموديول...")
            progress_bar.progress(10)
            
            from modules.proposal_generator import generate_proposal
            
            # Generate proposal (both MD and PDF)
            status_text.text("🤖 بدء توليد الأقسام...")
            progress_bar.progress(30)
            
            proposal = generate_proposal(
                rfp_criteria_file="data/outputs/criteria_with_weights.json",
                company_profile_file="data/outputs/company_profile.json",
                gap_analysis_file="data/outputs/gap_analysis.json",
                chat_history_file="data/outputs/chat_history.json",
                output_file="data/outputs/proposal.md",
                generate_pdf=True  # Generate PDF version
            )
            
            progress_bar.progress(100)
            status_text.text("✅ تم توليد العرض بنجاح!")
            
            st.success("🎉 تم توليد العرض الفني بنجاح!")
            
            # Check if PDF was created
            pdf_exists = os.path.exists("data/outputs/proposal.pdf")
            
            if pdf_exists:
                # Offer PDF download
                with open("data/outputs/proposal.pdf", 'rb') as f:
                    pdf_content = f.read()
                
                st.download_button(
                    label="📥 تحميل العرض (PDF)",
                    data=pdf_content,
                    file_name="proposal.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
            else:
                # Fallback to markdown
                st.download_button(
                    label="📥 تحميل العرض (Markdown)",
                    data=proposal,
                    file_name="proposal.md",
                    mime="text/markdown",
                    use_container_width=True
                )
            
            # Show preview
            st.markdown("---")
            st.subheader("👁️ معاينة العرض")
            
            with st.expander("عرض المحتوى", expanded=True):
                st.markdown(proposal)
            
        except FileNotFoundError as e:
            st.error(f"❌ خطأ: ملف مفقود - {e}")
            st.info("💡 تأكد من إكمال جميع الخطوات السابقة")
            
        except Exception as e:
            st.error(f"❌ حدث خطأ: {e}")
            with st.expander("تفاصيل الخطأ"):
                import traceback
                st.code(traceback.format_exc())


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
                RFP Generator
            </h2>
            <p style='color: rgba(255,255,255,0.8); font-size: 0.9rem; margin: 0;'>
                مولّد العروض الذكي
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Show current page
        page_names = {
            1: "📤 رفع الملفات",
            2: "💬 جمع المعلومات",
            3: "📄 توليد العرض"
        }
        
        st.markdown("""
        <div style='background: rgba(255,255,255,0.1); padding: 1rem; 
                    border-radius: 10px; margin-bottom: 1.5rem;'>
            <p style='color: rgba(255,255,255,0.8); font-size: 0.9rem; margin: 0;'>
                الصفحة الحالية:
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        for page_num, page_name in page_names.items():
            if page_num == st.session_state.page:
                st.markdown(f"""
                <div style='background: rgba(255,255,255,0.2); padding: 0.8rem; 
                            border-radius: 8px; margin-bottom: 0.5rem;'>
                    <p style='color: white; font-weight: 600; margin: 0; font-size: 1.1rem;'>
                        ▶ {page_name}
                    </p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style='padding: 0.8rem; margin-bottom: 0.5rem;'>
                    <p style='color: rgba(255,255,255,0.6); margin: 0;'>
                        {page_name}
                    </p>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Status indicators
        st.markdown("""
        <div style='background: rgba(255,255,255,0.1); padding: 1rem; 
                    border-radius: 10px;'>
            <p style='color: rgba(255,255,255,0.8); font-size: 0.9rem; margin-bottom: 1rem;'>
                حالة التقدم:
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        status_items = []
        if st.session_state.rfp_uploaded:
            status_items.append(("✅", "RFP مرفوع", True))
        else:
            status_items.append(("⏳", "RFP غير مرفوع", False))
        
        if st.session_state.company_uploaded:
            status_items.append(("✅", "ملف الشركة مرفوع", True))
        else:
            status_items.append(("⏳", "ملف الشركة غير مرفوع", False))
        
        if st.session_state.processing_done:
            questions_count = len(st.session_state.questions)
            status_items.append(("✅", f"تم استخراج {questions_count} سؤال", True))
        
        if st.session_state.additional_info_asked:
            status_items.append(("✅", "تم جمع جميع المعلومات", True))
        
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
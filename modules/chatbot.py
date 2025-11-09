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
    layout="wide"
)

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
    st.title("📄 RFP Proposal Generator")
    st.markdown("---")
    
    st.header("الخطوة 1: رفع الملفات")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📋 ملف RFP")
        rfp_file = st.file_uploader(
            "ارفع ملف RFP (PDF)",
            type=['pdf'],
            key='rfp_uploader'
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
        st.subheader("🏢 ملف الشركة")
        company_file = st.file_uploader(
            "ارفع ملف بروفايل الشركة (PDF)",
            type=['pdf'],
            key='company_uploader'
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
    col1, col2, col3 = st.columns([1, 1, 1])
    with col2:
        next_disabled = not (st.session_state.rfp_uploaded and st.session_state.company_uploaded)
        
        if st.button(
            "التالي: تحليل الفجوات ⬅️",
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
    st.title("💬 جمع المعلومات الناقصة")
    
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
# PAGE 3: Generate Proposal (Placeholder)
# ============================================
def page_proposal():
    st.title("📄 توليد العرض")
    st.markdown("---")
    
    st.info("🚧 هذه الصفحة قيد التطوير...")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        if st.button("⬅️ العودة", use_container_width=True):
            st.session_state.page = 2
            st.rerun()


# ============================================
# Main App Logic
# ============================================
def main():
    # Sidebar
    st.sidebar.title("📄 RFP Proposal Generator")
    st.sidebar.markdown("---")
    
    # Show current page
    page_names = {
        1: "1️⃣ رفع الملفات",
        2: "2️⃣ جمع المعلومات",
        3: "3️⃣ توليد العرض"
    }
    
    st.sidebar.write(f"**الصفحة الحالية:**")
    st.sidebar.write(f"### {page_names[st.session_state.page]}")
    
    st.sidebar.markdown("---")
    
    # Status indicators
    st.sidebar.write("**الحالة:**")
    if st.session_state.rfp_uploaded:
        st.sidebar.success("✅ RFP مرفوع")
    else:
        st.sidebar.warning("⏳ RFP غير مرفوع")
    
    if st.session_state.company_uploaded:
        st.sidebar.success("✅ ملف الشركة مرفوع")
    else:
        st.sidebar.warning("⏳ ملف الشركة غير مرفوع")
    
    if st.session_state.processing_done:
        st.sidebar.success(f"✅ تم استخراج {len(st.session_state.questions)} سؤال")
    
    if st.session_state.additional_info_asked:
        st.sidebar.success("✅ تم جمع جميع المعلومات")
    
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
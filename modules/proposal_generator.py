"""
Proposal Generator Module
Generate professional RFP proposal using LangGraph workflow
"""

import json
import os
from typing import TypedDict, Annotated, List
import operator
from pydantic import BaseModel, Field
from langgraph.graph import StateGraph, START, END
from langgraph.types import Send
from langchain_openai import ChatOpenAI
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from arabic_reshaper import reshape
from bidi.algorithm import get_display


# =========================
# Fixed Proposal Sections Schema
# =========================
class Section(BaseModel):
    name: str = Field(description="Section name in the proposal")
    description: str = Field(description="What this section should contain")


class ProposalSections(BaseModel):
    sections: List[Section]


def get_fixed_proposal_sections() -> ProposalSections:
    """Define fixed structure for proposal sections"""
    return ProposalSections(
        sections=[
            Section(
                name="مقدمة ومعلومات عن المشروع",
                description=(
                    "ملخص سياق مشروع الجهة والتحديات والغاية العامة، بالاعتماد على RFP فقط."
                ),
            ),
            Section(
                name="نبذة عن الشركة",
                description=(
                    "قدّم تعريفاً موجزاً بالشركة (التأسيس/الترخيص/الرسالة/المجالات) "
                    "بالاستناد حصراً إلى company_info. إذا لم تُذكر معلومة اكتب: غير مذكور."
                ),
            ),
            Section(
                name="المشاريع الحكومية المنجزة",
                description=(
                    "اذكر المشاريع الحكومية السابقة إن وُجدت في company_info، مع نبذة قصيرة لكل مشروع "
                    "(الجهة، الدور، النتيجة). إذا لم توجد مشاريع حكومية صرّح: غير مذكور."
                ),
            ),
            Section(
                name="أهداف المشروع",
                description=(
                    "اسرد الأهداف القابلة للقياس كما فهمناها من RFP فقط. لا تختلق أهدافاً."
                ),
            ),
            Section(
                name="نطاق العمل",
                description=(
                    "عرّف الأنشطة بدقة وفق RFP: المسح الشامل، المتابعة والتقييم، نقل الأنقاض، "
                    "قواعد بيانات/تقارير… بيّن ما نغطيه وما يحتاج توضيح."
                ),
            ),
            Section(
                name="منهجية تنفيذ المشروع ومراحل التنفيذ",
                description=(
                    "منهجية خطوة بخطوة مع مراحل واضحة ومعايير قبول كل مرحلة."
                ),
            ),
            Section(
                name="الخطة التفصيلية لتنفيذ المشروع",
                description=(
                    "خطة عمل عملية (أنشطة، مسؤوليات، نقاط تسليم). استخدم صيغاً زمنية نسبية."
                ),
            ),
            Section(
                name="مخرجات المشروع",
                description=(
                    "عدّد المخرجات (تقارير، قواعد بيانات، لوحات متابعة…)، واربط كل مخرج بمرحلته."
                ),
            ),
            Section(
                name="الكوادر البشرية (الهيكل الإداري والفني)",
                description=(
                    "قدّم هيكل الفريق والأدوار والمسؤوليات وفق company_info إن وُجد، "
                    "ومواءمته مع نطاق العمل. إن غاب تفصيل معيّن اكتب: غير مذكور."
                ),
            ),
            Section(
                name="حوكمة المشروع والهيكل التنظيمي والأدوار والمسؤوليات",
                description=(
                    "نموذج الحوكمة وقنوات الاعتماد، اجتماعات دورية، وحدود المسؤوليات."
                ),
            ),
            Section(
                name="البرنامج الزمني للعمل بالمشروع",
                description=(
                    "تصور زمني رفيع المستوى يربط المراحل بالمخرجات (قابل للتحويل إلى Gantt)."
                ),
            ),
            Section(
                name="الجودة والسلامة والامتثال",
                description=(
                    "نظام ضمان الجودة والسلامة والالتزام بالأنظمة المحلية، مع ربط بنتائج المطابقة."
                ),
            ),
            Section(
                name="الكميات والأسعار",
                description=(
                    "إذا كانت جداول الكميات/الأسعار مذكورة في RFP، لخّصها في جدول نصي "
                    "(البند، الوحدة، الكمية، السعر، الإجمالي). "
                    "إن لم تُذكر، اكتب: غير مذكور/بانتظار الاعتماد من الجهة."
                ),
            ),
            Section(
                name="الاحتياجات التأسيسية والتشغيلية",
                description=(
                    "استعرض ما يلزم إن كان مذكوراً في RFP: (إيجار مقر، توفير سيارات، معدات، وسائل سلامة، …). "
                    "إن لم يُذكر بند محدد اكتب: غير مذكور."
                ),
            ),
            Section(
                name="الأسئلة والاستفسارات والمتطلبات الإضافية من الجهة",
                description=(
                    "ادمج الأسئلة العامة وأسئلة الفجوات في قائمة مرقمة مختصرة "
                    "وتوضح ما يلزم من الجهة للاعتماد أو الإيضاح."
                ),
            ),
            Section(
                name="الخاتمة",
                description=(
                    "تأكيد الجاهزية لاجتماع قصير لمراجعة النقاط غير الواضحة والانطلاق بعد اعتماد المتطلبات."
                ),
            ),
        ]
    )


# =========================
# State Definitions
# =========================
class ProposalState(TypedDict):
    # Inputs / shared context
    rfp_summary: str
    company_info: str
    gap_analysis: dict
    user_answers: dict

    # Internal orchestration
    sections: list[Section]

    # Node outputs
    completed_sections: Annotated[list[str], operator.add]
    final_document: str


class WorkerState(TypedDict):
    # Each worker gets one section
    section: Section

    # Shared context
    rfp_summary: str
    company_info: str
    gap_analysis: dict
    user_answers: dict

    # Output
    completed_sections: Annotated[list[str], operator.add]


# =========================
# Node: Orchestrator
# =========================
def orchestrator_node(state: ProposalState):
    """Provide fixed section plan"""
    sections_plan = get_fixed_proposal_sections()
    return {"sections": sections_plan.sections}


# =========================
# Node: Writer
# =========================
def writer_node(state: WorkerState):
    """Write one section of the proposal"""
    
    section_name = state["section"].name
    section_desc = state["section"].description

    # Initialize LLM
    model = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)

    # Extra rules for sensitive sections
    extra_rules = []
    if section_name in ["نبذة عن الشركة", "المشاريع الحكومية المنجزة", 
                         "الكوادر البشرية (الهيكل الإداري والفني)"]:
        extra_rules.append("استخدم company_info فقط. إذا غابت معلومة صرّح: غير مذكور.")
    
    if section_name == "الكميات والأسعار":
        extra_rules.append(
            "إن وُجدت بيانات BoQ في RFP لخّصها في جدول نصّي: البند | الوحدة | الكمية | السعر | الإجمالي. "
            "إن لم تُذكر الأسعار أو الكميات فاذكر: غير مذكور / بانتظار جداول الكميات من الجهة."
        )
    
    if section_name == "الاحتياجات التأسيسية والتشغيلية":
        extra_rules.append(
            "اذكر فقط ما ورد في RFP (مثال: إيجار مقر، سيارات، معدات). إن لم يرد شيء فاذكر: غير مذكور."
        )

    rules_text = "\n- ".join(extra_rules) if extra_rules else "—"

    # Prepare gap analysis summary
    gap_summary = ""
    if state["gap_analysis"]:
        covered = len(state["gap_analysis"].get("covered_requirements", []))
        not_covered = len(state["gap_analysis"].get("not_covered_requirements", []))
        gap_summary = f"مغطى: {covered}, غير مغطى: {not_covered}"

    # Prepare user answers summary
    answers_summary = ""
    if state["user_answers"]:
        total_answers = state["user_answers"].get("total_questions", 0)
        answers_summary = f"إجمالي الأسئلة المجاب عليها: {total_answers}"

    prompt = f"""
أنت تكتب قسم "{section_name}" ضمن عرض رسمي.

المتطلبات العامة:
- اكتب بالعربية الفصحى المهنية، مختصر وعملي.
- لا تُخْتلق معلومات. استخدم RFP و company_info فقط.
- إذا لم تتوفر معلومة ضرورية اكتب حرفياً: غير مذكور.
- نظّم الفقرات بوضوح؛ استخدم قائمة/جدول نصّي فقط عند الحاجة.

سياق المناقصة (ملخص المتطلبات):
{state['rfp_summary']}

معلومات الشركة (قدراتنا وخدماتنا):
{state['company_info']}

نتائج المطابقة:
{gap_summary}

إجابات المستخدم على الأسئلة:
{answers_summary}

تعليمات خاصة لهذا القسم:
{section_desc}

قواعد إضافية لهذا القسم:
- {rules_text}

اكتب نص القسم النهائي فقط.
"""

    messages = [
        {"role": "system", "content": "مستشار عطاءات حكومية محترف يكتب عروضاً فنية رسمية بلا حشو."},
        {"role": "user", "content": prompt}
    ]

    response = model.invoke(messages)
    section_text = response.content.strip()

    return {"completed_sections": [f"### {section_name}\n\n{section_text}"]}


# =========================
# Node: Synthesizer
# =========================
def synthesizer_node(state: ProposalState):
    """Combine all written sections into one markdown proposal"""
    merged = "\n\n---\n\n".join(state["completed_sections"])
    
    # Add header
    final_doc = f"""# العرض الفني
# Technical Proposal

{merged}
"""
    
    return {"final_document": final_doc}


# =========================
# Edge Routing for Parallel Workers
# =========================
def assign_workers(state: ProposalState):
    """Create one Send task per section for parallel processing"""
    sends = []
    for sec in state["sections"]:
        sends.append(
            Send(
                "writer_node",
                {
                    "section": sec,
                    "rfp_summary": state["rfp_summary"],
                    "company_info": state["company_info"],
                    "gap_analysis": state["gap_analysis"],
                    "user_answers": state["user_answers"],
                },
            )
        )
    return sends


# =========================
# Build LangGraph Workflow
# =========================
def build_proposal_workflow():
    """Build and compile the proposal generation workflow"""
    
    proposal_builder = StateGraph(ProposalState)

    # Add nodes
    proposal_builder.add_node("orchestrator_node", orchestrator_node)
    proposal_builder.add_node("writer_node", writer_node)
    proposal_builder.add_node("synthesizer_node", synthesizer_node)

    # Define edges
    proposal_builder.add_edge(START, "orchestrator_node")
    
    proposal_builder.add_conditional_edges(
        "orchestrator_node",
        assign_workers,
        ["writer_node"],
    )
    
    proposal_builder.add_edge("writer_node", "synthesizer_node")
    proposal_builder.add_edge("synthesizer_node", END)

    # Compile
    return proposal_builder.compile()


def markdown_to_pdf(markdown_text: str, output_file: str):
    """
    Convert markdown proposal to PDF with Arabic support
    
    Args:
        markdown_text: Proposal in markdown format
        output_file: Path to save PDF file
    """
    
    # Create PDF document
    doc = SimpleDocTemplate(
        output_file,
        pagesize=A4,
        rightMargin=inch,
        leftMargin=inch,
        topMargin=inch,
        bottomMargin=inch
    )
    
    # Styles
    styles = getSampleStyleSheet()
    
    # Arabic title style
    title_style = ParagraphStyle(
        'ArabicTitle',
        parent=styles['Title'],
        alignment=TA_CENTER,
        fontSize=24,
        spaceAfter=30,
        textColor='#5E35B1'
    )
    
    # Arabic heading style
    heading_style = ParagraphStyle(
        'ArabicHeading',
        parent=styles['Heading1'],
        alignment=TA_RIGHT,
        fontSize=16,
        spaceAfter=12,
        spaceBefore=12,
        textColor='#1976D2'
    )
    
    # Arabic body style
    body_style = ParagraphStyle(
        'ArabicBody',
        parent=styles['BodyText'],
        alignment=TA_RIGHT,
        fontSize=11,
        leading=18,
        spaceAfter=10
    )
    
    # Build story (content)
    story = []
    
    # Parse markdown and convert to PDF elements
    lines = markdown_text.split('\n')
    
    for line in lines:
        line = line.strip()
        
        if not line:
            story.append(Spacer(1, 0.2*inch))
            continue
        
        # Handle markdown syntax
        if line.startswith('# '):
            # Main title
            text = line[2:].strip()
            reshaped_text = reshape(text)
            bidi_text = get_display(reshaped_text)
            story.append(Paragraph(bidi_text, title_style))
            story.append(Spacer(1, 0.3*inch))
            
        elif line.startswith('### '):
            # Section heading
            text = line[4:].strip()
            reshaped_text = reshape(text)
            bidi_text = get_display(reshaped_text)
            story.append(Spacer(1, 0.2*inch))
            story.append(Paragraph(bidi_text, heading_style))
            
        elif line.startswith('---'):
            # Separator - page break
            story.append(PageBreak())
            
        elif line.startswith('- '):
            # Bullet point
            text = '• ' + line[2:].strip()
            reshaped_text = reshape(text)
            bidi_text = get_display(reshaped_text)
            story.append(Paragraph(bidi_text, body_style))
            
        else:
            # Regular paragraph
            if line:
                reshaped_text = reshape(line)
                bidi_text = get_display(reshaped_text)
                story.append(Paragraph(bidi_text, body_style))
    
    # Build PDF
    doc.build(story)
    print(f"✓ PDF created: {output_file}")


# =========================
# Main Generation Function
# =========================
def generate_proposal(
    rfp_criteria_file: str = "data/outputs/criteria_with_weights.json",
    company_profile_file: str = "data/outputs/company_profile.json",
    gap_analysis_file: str = "data/outputs/gap_analysis.json",
    chat_history_file: str = "data/outputs/chat_history.json",
    output_file: str = "data/outputs/proposal.md",
    generate_pdf: bool = True
):
    """
    Generate proposal from all collected data
    
    Args:
        rfp_criteria_file: Path to RFP criteria JSON
        company_profile_file: Path to company profile JSON
        gap_analysis_file: Path to gap analysis JSON
        chat_history_file: Path to chat history JSON
        output_file: Path to save generated proposal (markdown)
        generate_pdf: Whether to also generate PDF version
        
    Returns:
        str: Generated proposal in markdown format
    """
    
    print("\n" + "="*70)
    print("🚀 Starting Proposal Generation")
    print("="*70)
    
    # Load data
    print("\n📄 Loading data files...")
    
    with open(rfp_criteria_file, 'r', encoding='utf-8') as f:
        rfp_data = json.load(f)
    print(f"✓ Loaded RFP criteria: {len(rfp_data.get('criteria', []))} criteria")
    
    with open(company_profile_file, 'r', encoding='utf-8') as f:
        company_data = json.load(f)
    print(f"✓ Loaded company profile")
    
    with open(gap_analysis_file, 'r', encoding='utf-8') as f:
        gap_data = json.load(f)
    print(f"✓ Loaded gap analysis")
    
    with open(chat_history_file, 'r', encoding='utf-8') as f:
        chat_data = json.load(f)
    print(f"✓ Loaded chat history: {chat_data.get('total_questions', 0)} questions")
    
    # Prepare RFP summary
    rfp_summary = rfp_data.get('summary', '')
    if not rfp_summary and rfp_data.get('criteria'):
        # Create summary from criteria
        criteria_list = [f"- {c['name']}: {c['description']}" 
                        for c in rfp_data['criteria'][:10]]  # First 10
        rfp_summary = "RFP Criteria:\n" + "\n".join(criteria_list)
    
    # Prepare company info as text
    company_info_text = json.dumps(company_data, ensure_ascii=False, indent=2)
    
    # Build workflow
    print("\n⚙️ Building proposal workflow...")
    proposal_app = build_proposal_workflow()
    
    # Prepare initial state
    initial_state = {
        "rfp_summary": rfp_summary,
        "company_info": company_info_text,
        "gap_analysis": gap_data,
        "user_answers": chat_data,
        "sections": [],
        "completed_sections": [],
        "final_document": "",
    }
    
    # Generate proposal
    print("\n📝 Generating proposal sections...")
    print("(This may take a few minutes...)")
    
    result_state = proposal_app.invoke(initial_state)
    
    # Get final proposal
    final_proposal = result_state["final_document"]
    
    # Save markdown version
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(final_proposal)
    
    print(f"\n✅ Markdown proposal saved to: {output_file}")
    
    # Generate PDF version
    if generate_pdf:
        print("\n📄 Converting to PDF...")
        pdf_file = output_file.replace('.md', '.pdf')
        
        try:
            markdown_to_pdf(final_proposal, pdf_file)
            print(f"✅ PDF proposal saved to: {pdf_file}")
        except Exception as e:
            print(f"⚠️ Warning: Could not generate PDF: {e}")
            print("   Markdown version is still available")
    
    print("="*70)
    
    return final_proposal


# =========================
# Example Usage
# =========================
if __name__ == "__main__":
    """Example of how to use the proposal generator"""
    
    # Generate proposal
    proposal = generate_proposal()
    
    # Print preview
    print("\n" + "="*70)
    print("📄 PROPOSAL PREVIEW (First 500 characters)")
    print("="*70)
    print(proposal[:500])
    print("...")
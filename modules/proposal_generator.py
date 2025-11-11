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
import pypandoc


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
أنت خبير في كتابة العروض الفنية للمناقصات الحكومية.

قسم العرض المطلوب: "{section_name}"

⚠️ تعليمات مهمة:
1. لا تكرر عنوان القسم في المحتوى (العنوان موجود بالفعل)
2. ابدأ مباشرة بالمحتوى بدون كتابة عنوان
3. استخدم معلومات حقيقية فقط من البيانات المتوفرة
4. إذا لم تتوفر معلومة، اكتب: "غير مذكور" أو "سيتم توفيرها لاحقاً"
5. اكتب بأسلوب رسمي واضح ومختصر
6. استخدم قوائم نقطية فقط عند الحاجة

وصف القسم المطلوب:
{section_desc}

قواعد خاصة بهذا القسم:
{rules_text}

===== البيانات المتوفرة =====

📋 معلومات المناقصة (RFP):
{state['rfp_summary']}

🏢 معلومات الشركة:
{state['company_info']}

📊 نتائج تحليل الفجوات:
{gap_summary}

💬 إجابات المستخدم:
{answers_summary}

===== المطلوب =====
اكتب محتوى القسم مباشرة باللغة العربية الفصحى، بدون كتابة العنوان مرة أخرى.
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


def markdown_to_word(markdown_file: str, output_file: str):
    """
    Convert markdown proposal to Word document with Arabic support
    
    Args:
        markdown_file: Path to markdown file
        output_file: Path to save Word document
    """
    
    try:
        pypandoc.convert_file(
            markdown_file,
            'docx',
            outputfile=output_file,
            extra_args=['--standalone']
        )
        print(f"✓ Word document created: {output_file}")
    except Exception as e:
        print(f"⚠️ Warning: Could not generate Word document: {e}")
        raise


# =========================
# Main Generation Function
# =========================
def generate_proposal(
    rfp_criteria_file: str = "data/outputs/criteria_with_weights.json",
    company_profile_file: str = "data/outputs/company_profile.json",
    gap_analysis_file: str = "data/outputs/gap_analysis.json",
    chat_history_file: str = "data/outputs/chat_history.json",
    output_file: str = "data/outputs/proposal.md",
    generate_word: bool = True
):
    """
    Generate proposal from all collected data
    
    Args:
        rfp_criteria_file: Path to RFP criteria JSON
        company_profile_file: Path to company profile JSON
        gap_analysis_file: Path to gap analysis JSON
        chat_history_file: Path to chat history JSON
        output_file: Path to save generated proposal (markdown)
        generate_word: Whether to also generate Word document
        
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
        # Create detailed summary from criteria
        criteria_texts = []
        for i, c in enumerate(rfp_data['criteria'][:15], 1):  # First 15
            criteria_texts.append(
                f"{i}. {c['name']}\n"
                f"   الوصف: {c.get('description', 'غير محدد')}\n"
                f"   الوزن: {c.get('weight', 0)}%"
            )
        rfp_summary = "معايير المناقصة:\n\n" + "\n\n".join(criteria_texts)
    
    # Prepare company info as readable text (not JSON)
    company_info_parts = []
    
    # Basic info
    company_info_parts.append("=== معلومات الشركة الأساسية ===")
    company_info_parts.append(f"اسم الشركة: {company_data.get('company_name', 'غير محدد')}")
    
    if company_data.get('establishment_date'):
        company_info_parts.append(f"تاريخ التأسيس: {company_data['establishment_date']}")
    
    if company_data.get('licenses'):
        licenses = ", ".join(company_data['licenses']) if isinstance(company_data['licenses'], list) else company_data['licenses']
        company_info_parts.append(f"التراخيص: {licenses}")
    
    if company_data.get('certifications'):
        certs = ", ".join(company_data['certifications']) if isinstance(company_data['certifications'], list) else company_data['certifications']
        company_info_parts.append(f"الشهادات: {certs}")
    
    # Services
    if company_data.get('services'):
        company_info_parts.append("\n=== الخدمات المقدمة ===")
        services = company_data['services']
        if isinstance(services, list):
            for i, service in enumerate(services, 1):
                company_info_parts.append(f"{i}. {service}")
        else:
            company_info_parts.append(str(services))
    
    # Fields/Domains
    if company_data.get('fields') or company_data.get('domains'):
        company_info_parts.append("\n=== المجالات ===")
        fields = company_data.get('fields') or company_data.get('domains')
        if isinstance(fields, list):
            for i, field in enumerate(fields, 1):
                company_info_parts.append(f"{i}. {field}")
        else:
            company_info_parts.append(str(fields))
    
    # Values and goals
    if company_data.get('values'):
        company_info_parts.append("\n=== القيم ===")
        values = company_data['values']
        if isinstance(values, list):
            for i, value in enumerate(values, 1):
                company_info_parts.append(f"{i}. {value}")
        else:
            company_info_parts.append(str(values))
    
    if company_data.get('goals'):
        company_info_parts.append("\n=== الأهداف ===")
        goals = company_data['goals']
        if isinstance(goals, list):
            for i, goal in enumerate(goals, 1):
                company_info_parts.append(f"{i}. {goal}")
        else:
            company_info_parts.append(str(goals))
    
    # Previous projects
    if company_data.get('previous_projects'):
        company_info_parts.append("\n=== المشاريع السابقة ===")
        projects = company_data['previous_projects']
        if isinstance(projects, list):
            for i, project in enumerate(projects, 1):
                if isinstance(project, dict):
                    company_info_parts.append(f"{i}. {project.get('name', 'مشروع')}")
                    if project.get('client'):
                        company_info_parts.append(f"   الجهة: {project['client']}")
                    if project.get('description'):
                        company_info_parts.append(f"   الوصف: {project['description']}")
                else:
                    company_info_parts.append(f"{i}. {project}")
    
    # Government projects
    if company_data.get('government_projects'):
        company_info_parts.append("\n=== المشاريع الحكومية ===")
        gov_projects = company_data['government_projects']
        if isinstance(gov_projects, list):
            for i, project in enumerate(gov_projects, 1):
                if isinstance(project, dict):
                    company_info_parts.append(f"{i}. {project.get('name', 'مشروع حكومي')}")
                    if project.get('entity'):
                        company_info_parts.append(f"   الجهة: {project['entity']}")
                    if project.get('role'):
                        company_info_parts.append(f"   الدور: {project['role']}")
                    if project.get('result'):
                        company_info_parts.append(f"   النتيجة: {project['result']}")
                else:
                    company_info_parts.append(f"{i}. {project}")
    
    # Team structure
    if company_data.get('team_structure'):
        company_info_parts.append("\n=== الهيكل الإداري والفني ===")
        team = company_data['team_structure']
        if isinstance(team, dict):
            for role, details in team.items():
                company_info_parts.append(f"• {role}: {details}")
        else:
            company_info_parts.append(str(team))
    
    # Contact info
    if company_data.get('phone') or company_data.get('email') or company_data.get('website'):
        company_info_parts.append("\n=== معلومات الاتصال ===")
        if company_data.get('phone'):
            company_info_parts.append(f"الهاتف: {company_data['phone']}")
        if company_data.get('email'):
            company_info_parts.append(f"البريد الإلكتروني: {company_data['email']}")
        if company_data.get('website'):
            company_info_parts.append(f"الموقع: {company_data['website']}")
    
    company_info_text = "\n".join(company_info_parts)
    
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
    
    # Generate Word document version
    if generate_word:
        print("\n📄 Converting to Word document...")
        docx_file = output_file.replace('.md', '.docx')
        
        try:
            markdown_to_word(output_file, docx_file)
            print(f"✅ Word document saved to: {docx_file}")
        except Exception as e:
            print(f"⚠️ Warning: Could not generate Word document: {e}")
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
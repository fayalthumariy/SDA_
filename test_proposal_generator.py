"""
Test Proposal Generator
Test the proposal generation workflow
"""

import os

# ============================================
# Setup API Key
# ============================================
import streamlit as st
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]


print("="*80)
print("🧪 Testing Proposal Generator")
print("="*80)

try:
    # Import proposal generator
    from modules.proposal_generator import generate_proposal
    
    print("\n✓ Proposal generator imported successfully")
    
    # Generate proposal
    print("\n🚀 Starting proposal generation...")
    print("(This will take a few minutes...)\n")
    
    proposal = generate_proposal(
        rfp_criteria_file="data/outputs/criteria_with_weights.json",
        company_profile_file="data/outputs/company_profile.json",
        gap_analysis_file="data/outputs/gap_analysis.json",
        chat_history_file="data/outputs/chat_history.json",
        output_file="data/outputs/proposal.md",
        generate_word=True  # Generate Word document
    )
    
    # Show preview
    print("\n" + "="*80)
    print("📄 PROPOSAL PREVIEW (First 1000 characters)")
    print("="*80)
    print(proposal[:1000])
    print("\n... (see full proposal in data/outputs/proposal.md)")
    
    # Check if Word document was created
    if os.path.exists("data/outputs/proposal.docx"):
        print("\n✅ Word document created: data/outputs/proposal.docx")
    else:
        print("\n⚠️ Word document was not created (check for errors above)")
    
    print("\n✅ Proposal generation test completed successfully!")
    
except FileNotFoundError as e:
    print(f"\n❌ Error: Required file not found")
    print(f"   {e}")
    print("\n💡 Make sure you have run all previous steps:")
    print("   1. Upload files and extract criteria")
    print("   2. Complete gap analysis")
    print("   3. Answer chatbot questions")
    
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print("\n💡 Make sure:")
    print("   - proposal_generator.py is in the modules/ folder")
    print("   - Required packages are installed:")
    print("     pip install langgraph python-docx")
    
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
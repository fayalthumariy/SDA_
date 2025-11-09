"""
Test Chatbot Module
Simple test to run the chatbot with questions from gap analysis
"""

import os

# ============================================
# Setup API Key
# ============================================
import streamlit as st
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]

print("="*80)
print("🤖 Testing Chatbot Module")
print("="*80)

try:
    # Import chatbot functions
    from modules.chatbot import run_chatbot_from_gap_file, print_chat_summary
    
    print("\n✓ Chatbot module imported successfully")
    
    # Run chatbot with questions from gap analysis
    print("\n🚀 Starting chatbot session...\n")
    
    session = run_chatbot_from_gap_file(
        gap_file="data/outputs/gap_analysis.json",
        output_file="data/outputs/chat_history.json"
    )
    
    # Print summary if completed
    if session:
        print_chat_summary(session)
        print("\n✅ Chatbot test completed successfully!")
    else:
        print("\n⚠️ No questions to ask")
    
except FileNotFoundError as e:
    print(f"\n❌ Error: File not found")
    print(f"   {e}")
    print("\n💡 Make sure you have run the gap analysis first:")
    print("   python test_complete_pipeline.py")
    
except ImportError as e:
    print(f"\n❌ Import Error: {e}")
    print("\n💡 Make sure chatbot.py is in the modules/ folder")
    
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "="*80)
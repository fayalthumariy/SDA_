"""
Full Pipeline Test - Complete System Testing
Tests all stages from beginning to end
"""

import os
import sys

# ============================================
# Setup API Key
# ============================================
import streamlit as st
os.environ["OPENAI_API_KEY"] = st.secrets["OPENAI_API_KEY"]


# ============================================
# Import Modules
# ============================================
try:
    import sys
    sys.path.append('.')  # Ensure reading from current directory
    
    print("✓ Importing modules...")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    sys.exit(1)

# ============================================
# File Settings
# ============================================
RFP_PDF = "data/uploads/123.pdf"                           # RFP PDF file
COMPANY_PDF = "data/uploads/257276441660654737.pdf"    # Company profile PDF

# Output files
RFP_OUTPUT = "data/outputs/criteria_with_weights.json"
COMPANY_OUTPUT = "data/outputs/company_profile.json"
GAP_OUTPUT = "data/outputs/gap_analysis.json"

# ============================================
# Step 1: Extract RFP Criteria
# ============================================
def step1_extract_rfp():
    """Extract RFP criteria from PDF"""
    print("\n" + "="*70)
    print("📋 Step 1: Extracting RFP Criteria from PDF")
    print("="*70)
    
    try:
        # Import function from modules
        from modules.rfp_extractor import extract_and_weight_rfp_criteria
        
        # Run extraction
        result = extract_and_weight_rfp_criteria(
            pdf_path=RFP_PDF,
            output_file=RFP_OUTPUT
        )
        
        print(f"\n✅ Step 1 completed successfully!")
        print(f"   📄 Saved result to: {RFP_OUTPUT}")
        print(f"   📊 Number of criteria: {len(result.get('criteria', []))}")
        
        return True
        
    except FileNotFoundError:
        print(f"\n❌ Error: File not found: {RFP_PDF}")
        print("💡 Make sure the RFP PDF file exists in data/uploads/")
        return False
        
    except Exception as e:
        print(f"\n❌ Error in Step 1: {e}")
        import traceback
        traceback.print_exc()
        return False

# ============================================
# Step 2: Extract Company Profile
# ============================================
def step2_extract_company():
    """Extract company profile from PDF"""
    print("\n" + "="*70)
    print("🏢 Step 2: Extracting Company Profile from PDF")
    print("="*70)
    
    try:
        # Import function from modules
        from modules.company_extractor import extract_company_profile_from_pdf
        
        # Run extraction
        result = extract_company_profile_from_pdf(
            pdf_path=COMPANY_PDF,
            api_key=API_KEY,
            output_file=COMPANY_OUTPUT
        )
        
        print(f"\n✅ Step 2 completed successfully!")
        print(f"   📄 Saved result to: {COMPANY_OUTPUT}")
        
        # Display some info
        if isinstance(result, dict):
            company_name = result.get('company_names', {}).get('ar', [''])[0]
            services_count = len(result.get('services', []))
            print(f"   🏢 Company name: {company_name}")
            print(f"   ⚙️ Number of services: {services_count}")
        
        return True
        
    except FileNotFoundError:
        print(f"\n❌ Error: File not found: {COMPANY_PDF}")
        print("💡 Make sure the company profile PDF file exists in data/uploads/")
        return False
        
    except Exception as e:
        print(f"\n❌ Error in Step 2: {e}")
        import traceback
        traceback.print_exc()
        return False

# ============================================
# Step 3: Gap Analysis
# ============================================
def step3_analyze_gaps():
    """Analyze gaps between RFP and company"""
    print("\n" + "="*70)
    print("🔍 Step 3: Analyzing Gaps")
    print("="*70)
    
    try:
        # Import functions from modules
        from modules.gap_analyzer import perform_full_gap_analysis, print_gap_analysis
        
        # Run analysis
        report = perform_full_gap_analysis(
            rfp_criteria_file=RFP_OUTPUT,
            company_profile_file=COMPANY_OUTPUT,
            output_file=GAP_OUTPUT,
            api_key=API_KEY
        )
        
        print(f"\n✅ Step 3 completed successfully!")
        print(f"   📄 Saved result to: {GAP_OUTPUT}")
        
        # Print results
        print_gap_analysis(report)
        
        return True
        
    except FileNotFoundError as e:
        print(f"\n❌ Error: Required file not found")
        print(f"   {e}")
        print("💡 Make sure previous steps completed successfully")
        return False
        
    except Exception as e:
        print(f"\n❌ Error in Step 3: {e}")
        import traceback
        traceback.print_exc()
        return False

# ============================================
# Run Full Pipeline
# ============================================
def run_full_pipeline():
    """Run all steps in sequence"""
    
    print("\n" + "="*70)
    print("🚀 Starting Full System Test")
    print("="*70)
    
    # Check API Key
    if API_KEY == "ضعي_مفتاحك_هنا" or API_KEY == "PUT_YOUR_KEY_HERE":
        print("\n⚠️ Warning: OpenAI API Key not set!")
        print("💡 Edit the API_KEY variable at the top of the file")
        return
    
    # Success counter
    success_count = 0
    total_steps = 3
    
    # Step 1: RFP
    print("\n🔄 Running Step 1...")
    if step1_extract_rfp():
        success_count += 1
    else:
        print("\n⛔ Step 1 failed - Test stopped")
        return
    
    # Step 2: Company
    print("\n🔄 Running Step 2...")
    if step2_extract_company():
        success_count += 1
    else:
        print("\n⛔ Step 2 failed - Test stopped")
        return
    
    # Step 3: Gap Analysis
    print("\n🔄 Running Step 3...")
    if step3_analyze_gaps():
        success_count += 1
    
    # Final result
    print("\n" + "="*70)
    print("📊 Full Test Results")
    print("="*70)
    print(f"\n✅ Completed {success_count} of {total_steps} steps successfully!")
    
    if success_count == total_steps:
        print("\n🎉 Excellent! System works completely!")
        print("\n📁 Output files:")
        print(f"   1. {RFP_OUTPUT}")
        print(f"   2. {COMPANY_OUTPUT}")
        print(f"   3. {GAP_OUTPUT}")
    else:
        print(f"\n⚠️ Some steps completed, check errors above")
    
    print("\n" + "="*70)

# ============================================
# Entry Point
# ============================================
if __name__ == "__main__":
    try:
        run_full_pipeline()
    except KeyboardInterrupt:
        print("\n\n⚠️ Test stopped by user")
    except Exception as e:
        print(f"\n\n❌ Unexpected error: {e}")
        import traceback
        traceback.print_exc()
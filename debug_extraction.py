"""
Debug script to see what ChatGPT extracts from the CV
"""

import os
import sys
import json

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from cv_converter import _extract_cv_with_chatgpt


def debug_extraction(pdf_path):
    """Extract and display raw CV data"""
    
    print(f"\n{'='*70}")
    print(f"DEBUG: ChatGPT Extraction")
    print(f"{'='*70}\n")
    
    try:
        print(f"Extracting from: {pdf_path}\n")
        cv_data = _extract_cv_with_chatgpt(pdf_path)
        
        print("RAW EXTRACTED DATA:")
        print("="*70)
        
        for key, value in cv_data.items():
            print(f"\n{key.upper()}:")
            print("-" * 70)
            if isinstance(value, str) and len(value) > 200:
                print(value[:500] + "..." if len(value) > 500 else value)
            else:
                print(value)
        
        print(f"\n{'='*70}\n")
        
        # Check if years/dates are present
        print("ANALYSIS:")
        print("-" * 70)
        
        work_exp = cv_data.get('working_experience', '')
        edu = cv_data.get('education', '')
        
        print(f"\n1. Working Experience contains dates/years: {bool(__import__('re').search(r'\\d{4}|\\d{1,2}/\\d{1,2}', work_exp))}")
        if work_exp:
            print(f"   First 300 chars: {work_exp[:300]}")
        
        print(f"\n2. Education contains dates/years: {bool(__import__('re').search(r'\\d{4}|\\d{1,2}/\\d{1,2}', edu))}")
        if edu:
            print(f"   First 300 chars: {edu[:300]}")
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    PDF_FILE = "app/static/CVS/Amirun_Harraz_Resume_PNG.pdf"
    debug_extraction(PDF_FILE)

"""
Process single CV (Amirun Harraz) using ChatGPT extraction and KLSB template
"""

import os
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from cv_converter import convert_cv_to_klsb_ocr

def process_single_cv(pdf_path, output_dir='uploads/cv'):
    """
    Process single PDF CV using ChatGPT and convert to KLSB format
    """
    
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF file not found: {pdf_path}")
        return
    
    print(f"\n{'='*70}")
    print(f"PROCESSING SINGLE CV - ChatGPT Extraction")
    print(f"{'='*70}")
    print(f"PDF File: {pdf_path}")
    print(f"Output Directory: {output_dir}")
    print(f"{'='*70}\n")
    
    try:
        print(f"Processing: {os.path.basename(pdf_path)}")
        print(f"→ Extracting and converting with ChatGPT + KLSB template...")
        
        output_path, cv_data = convert_cv_to_klsb_ocr(
            source_path=pdf_path,
            output_dir=output_dir,
            output_format="docx",
            use_chatgpt=True
        )
        
        print(f"\n✓ Successfully generated!")
        print(f"✓ Output: {os.path.basename(output_path)}")
        print(f"✓ Location: {os.path.abspath(output_path)}")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        print(f"{'='*70}\n")


if __name__ == "__main__":
    # Process Amirun Harraz CV
    CV_FILE = "app/static/CVS/Amirun_Harraz_Resume_PNG.pdf"
    OUTPUT_DIR = "uploads/cv"
    
    process_single_cv(CV_FILE, OUTPUT_DIR)

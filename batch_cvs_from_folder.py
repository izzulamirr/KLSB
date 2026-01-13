"""
Batch process CVs from app/static/CVS folder using ChatGPT extraction
and convert to KLSB_template_true.docx format
"""

import os
import sys
from pathlib import Path
from docxtpl import DocxTemplate

# Add app directory to path to import cv_converter
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from cv_converter import convert_cv_to_klsb_ocr

def process_cvs_from_folder(cv_folder, output_dir='uploads/cv'):
    """
    Process all PDFs in CV folder using ChatGPT and convert to KLSB DOCX format
    
    Args:
        cv_folder: Path to folder with PDF CVs
        output_dir: Output directory for converted CVs
    """
    
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if CV folder exists
    if not os.path.exists(cv_folder):
        print(f"❌ Error: CV folder not found: {cv_folder}")
        return
    
    print(f"\n{'='*70}")
    print(f"BATCH CV PROCESSING FROM FOLDER - ChatGPT Extraction")
    print(f"{'='*70}")
    print(f"CV Folder: {cv_folder}")
    print(f"Output Directory: {output_dir}")
    print(f"{'='*70}\n")
    
    # Find all PDF files in folder
    pdf_files = list(Path(cv_folder).glob("*.pdf"))
    
    if not pdf_files:
        print(f"⚠️  No PDF files found in {cv_folder}")
        return
    
    print(f"Found {len(pdf_files)} PDF files to process\n")
    
    generated_count = 0
    failed_count = 0
    
    for idx, pdf_path in enumerate(pdf_files, 1):
        try:
            print(f"[{idx}/{len(pdf_files)}] Processing: {pdf_path.name}")
            
            # Convert using existing converter (uses ChatGPT if configured)
            print(f"  → Extracting and converting with KLSB template...")
            output_path, cv_data = convert_cv_to_klsb_ocr(
                source_path=str(pdf_path),
                output_dir=output_dir,
                output_format="docx",
                use_chatgpt=True
            )
            
            print(f"  ✓ Generated: {os.path.basename(output_path)}")
            generated_count += 1
            
        except Exception as e:
            print(f"  ✗ Error: {str(e)}")
            failed_count += 1
    
    print(f"\n{'='*70}")
    print(f"BATCH PROCESSING COMPLETE")
    print(f"{'='*70}")
    print(f"✓ Generated: {generated_count} CVs")
    print(f"✗ Failed: {failed_count} CVs")
    print(f"Total processed: {len(pdf_files)}")
    print(f"Output directory: {os.path.abspath(output_dir)}")
    print(f"{'='*70}\n")
    
    return generated_count, failed_count


if __name__ == "__main__":
    # Configuration
    CV_FOLDER = "app/static/CVS"
    OUTPUT_DIR = "uploads/cv"
    
    # Process CVs
    process_cvs_from_folder(CV_FOLDER, OUTPUT_DIR)

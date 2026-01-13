"""
Process CV using ChatGPT extraction and docxtpl template rendering
"""

import os
import sys
from pathlib import Path

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from cv_converter import _extract_cv_with_chatgpt

try:
    from docxtpl import DocxTemplate, RichText
except ImportError:
    print("❌ docxtpl not installed. Install with: pip install docxtpl")
    sys.exit(1)

# Import the parser
from cv_data_parser import structure_cv_data


def process_cv_with_template(pdf_path, template_path, output_dir='uploads/cv'):
    """
    Extract CV with ChatGPT and render using docxtpl template
    """
    
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(pdf_path):
        print(f"❌ Error: PDF file not found: {pdf_path}")
        return
    
    if not os.path.exists(template_path):
        print(f"❌ Error: Template file not found: {template_path}")
        return
    
    print(f"\n{'='*70}")
    print(f"PROCESSING CV - ChatGPT Extraction + Template Rendering")
    print(f"{'='*70}")
    print(f"PDF File: {pdf_path}")
    print(f"Template: {template_path}")
    print(f"Output Directory: {output_dir}")
    print(f"{'='*70}\n")
    
    try:
        print(f"Processing: {os.path.basename(pdf_path)}")
        print(f"→ Step 1: Extracting CV data with ChatGPT...")
        
        # Extract CV data using ChatGPT
        cv_data = _extract_cv_with_chatgpt(pdf_path)
        
        if not cv_data:
            print(f"✗ Failed to extract CV data")
            return
        
        print(f"✓ Extraction complete")
        print(f"  Fields extracted: {len(cv_data)} fields")
        
        # Structure the data with detailed tags
        print(f"→ Step 1b: Structuring detailed tags...")
        structured_data = structure_cv_data(cv_data)
        print(f"✓ Structured {len(structured_data.get('work_experiences', []))} work experiences")
        print(f"✓ Structured {len(structured_data.get('educations', []))} education entries")
        
        # Load template
        print(f"→ Step 2: Loading template...")
        template = DocxTemplate(template_path)
        print(f"✓ Template loaded")
        
        # Prepare context - convert values appropriately and inject RichText for work header lines
        context = {}
        for key, value in structured_data.items():
            if value is None:
                context[key] = ''
            elif isinstance(value, list):
                context[key] = value
            elif key in ['name', 'position', 'nationality']:
                context[key] = str(value).upper() if value else ''
            else:
                context[key] = str(value)

        # Build RichText for working experience with bold headers and bullets
        work_items = structured_data.get('work_experiences', [])
        if work_items:
            rt = RichText()
            for idx, work in enumerate(work_items):
                years = work.get('years', '').strip()
                company = work.get('company', '').strip()
                position = work.get('position', '').strip()

                if years:
                    rt.add(f"Year : {years}", bold=True)
                    rt.add("\n")
                if company:
                    rt.add(f"Company : {company}", bold=True)
                    rt.add("\n")
                if position:
                    rt.add(f"Position : {position}", bold=True)
                    rt.add("\n")

                desc = work.get('description', '').strip()
                if desc:
                    rt.add("\n")
                    rt.add("Job Description:\n")
                    for line in desc.split('\n'):
                        if line.strip():
                            rt.add("• " + line.strip())
                            rt.add("\n")

                if idx < len(work_items) - 1:
                    rt.add("\n")

            # Override the plain string with RichText for the template tag
            context['working_experience_formatted'] = rt
        
        print(f"→ Step 3: Rendering template with extracted data...")
        
        # Render template with data
        template.render(context)
        
        print(f"✓ Template rendered")
        
        # Generate output filename with timestamp to avoid conflicts
        import time
        candidate_name = cv_data.get('name', 'Candidate').lower().replace(' ', '-')
        timestamp = int(time.time()) % 10000
        output_filename = f"KLSB_{candidate_name}_{timestamp}.docx"
        output_path = os.path.join(output_dir, output_filename)
        
        # Save
        print(f"→ Step 4: Saving output...")
        template.save(output_path)
        
        print(f"\n✓ Successfully generated!")
        print(f"✓ Output: {os.path.basename(output_path)}")
        print(f"✓ Location: {os.path.abspath(output_path)}")
        print(f"{'='*70}\n")
        
    except Exception as e:
        print(f"✗ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        print(f"{'='*70}\n")


if __name__ == "__main__":
    # Process Amirun Harraz CV with KLSB template
    PDF_FILE = "app/static/CVS/YashCV_Latest.pdf"
    TEMPLATE_FILE = "KLSB_template_true.docx"
    OUTPUT_DIR = "uploads/cv"
    
    process_cv_with_template(PDF_FILE, TEMPLATE_FILE, OUTPUT_DIR)

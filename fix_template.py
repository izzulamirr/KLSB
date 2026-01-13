"""
Fix KLSB_template_true.docx by consolidating multiple {{working_experience}} tags 
into a single placeholder for the entire working experience section
"""

from docx import Document
from docx.oxml import parse_xml
from docx.shared import Pt, Inches
import re

def consolidate_working_experience_tags():
    """
    Open template, find all {{working_experience}} tags and replace with single tag
    """
    
    doc = Document('KLSB_template_true.docx')
    
    print("Scanning document for template tags...")
    
    # Track if we found working experience section
    found_section = False
    consolidate_done = False
    
    # Process each paragraph
    for para_idx, para in enumerate(doc.paragraphs):
        text = para.text
        
        # Detect WORKING EXPERIENCE section
        if 'WORKING EXPERIENCE' in text:
            found_section = True
            print(f"✓ Found WORKING EXPERIENCE section at paragraph {para_idx}")
            continue
        
        # In working experience section, consolidate tags
        if found_section and '{{working_experience}}' in text:
            if not consolidate_done:
                print(f"  Consolidating tags at paragraph {para_idx}: {text[:50]}...")
                # Replace all {{working_experience}} with single tag
                # We'll replace the line with just the tag
                para.text = ""
                para.add_run("{{working_experience}}")
                consolidate_done = True
                print("  ✓ Consolidated to single tag")
            else:
                # Remove duplicate tags
                print(f"  Removing duplicate tag at paragraph {para_idx}")
                para.clear()
    
    # Also check table cells for tags
    print("\nScanning tables for template tags...")
    for table_idx, table in enumerate(doc.tables):
        for row_idx, row in enumerate(table.rows):
            for cell_idx, cell in enumerate(row.cells):
                if '{{working_experience}}' in cell.text:
                    print(f"  Found in table {table_idx}, row {row_idx}, cell {cell_idx}")
    
    # Save to temp file first, then replace
    doc.save('KLSB_template_true_temp.docx')
    print("\n✓ Template saved to temp file")
    
    # Remove old file and rename
    import os
    if os.path.exists('KLSB_template_true.docx'):
        os.remove('KLSB_template_true.docx')
    os.rename('KLSB_template_true_temp.docx', 'KLSB_template_true.docx')
    print("✓ Template updated and saved!")

if __name__ == "__main__":
    consolidate_working_experience_tags()

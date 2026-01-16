"""
Add KLSB number tag to template header
"""

from docx import Document
import os


def add_klsb_number_to_template():
    """Add {{klsb_number}} tag to template header"""
    
    template_path = "KLSB_template_true.docx"
    
    if not os.path.exists(template_path):
        print(f"❌ Template not found: {template_path}")
        return
    
    print(f"\n{'='*70}")
    print(f"ADDING KLSB NUMBER TO TEMPLATE")
    print(f"{'='*70}\n")
    
    doc = Document(template_path)
    
    # Check if klsb_number already exists
    found_klsb = False
    for para in doc.paragraphs:
        if '{{klsb_number}}' in para.text:
            print(f"✓ Found {{{{klsb_number}}}} in paragraph: {para.text[:80]}")
            found_klsb = True
    
    # Check headers
    for section_idx, section in enumerate(doc.sections):
        header = section.header
        print(f"\n--- Checking Header in Section {section_idx + 1} ---")
        
        for para_idx, para in enumerate(header.paragraphs):
            print(f"Header Para {para_idx}: {para.text[:100] if para.text else '(empty)'}")
            
            if '{{klsb_number}}' in para.text:
                print(f"  ✓ {{{{klsb_number}}}} already exists!")
                found_klsb = True
            
            # Add KLSB number after "PROFESSIONAL RESUME" if found
            if 'PROFESSIONAL RESUME' in para.text and '{{klsb_number}}' not in para.text:
                print(f"  → Found 'PROFESSIONAL RESUME' - adding {{{{klsb_number}}}}")
                
                # Get the current text
                current_text = para.text
                
                # Clear all runs
                for run in para.runs:
                    run.text = ''
                
                # Add KLSB number line after the current content
                if para.runs:
                    para.runs[0].text = current_text + "\nRef: {{klsb_number}}"
                else:
                    para.add_run(current_text + "\nRef: {{klsb_number}}")
                
                print(f"  ✓ Added: {para.text}")
                found_klsb = True
        
        # Check header tables
        for table_idx, table in enumerate(header.tables):
            print(f"\n--- Header Table {table_idx} ---")
            for row_idx, row in enumerate(table.rows):
                for cell_idx, cell in enumerate(row.cells):
                    for para in cell.paragraphs:
                        if para.text.strip():
                            print(f"  Table[{row_idx}][{cell_idx}]: {para.text[:80]}")
                            
                            if '{{klsb_number}}' in para.text:
                                print(f"    ✓ {{{{klsb_number}}}} already exists!")
                                found_klsb = True
                            
                            # Add KLSB number in the right cell (where the name appears)
                            if '{{name}}' in para.text and '{{klsb_number}}' not in para.text:
                                print(f"    → Found {{{{name}}}} - adding {{{{klsb_number}}}} reference")
                                
                                # Add KLSB reference below the name
                                new_para = cell.add_paragraph()
                                new_para.add_run("Ref: {{klsb_number}}")
                                print(f"    ✓ Added KLSB reference paragraph")
                                found_klsb = True
    
    if not found_klsb:
        print("\n⚠️  Could not find suitable location for {{klsb_number}}")
        print("Please manually add {{klsb_number}} to your template where you want it to appear.")
    
    # Create backup
    backup_path = "KLSB_template_true_backup.docx"
    if not os.path.exists(backup_path):
        doc.save(backup_path)
        print(f"\n✓ Backup created: {backup_path}")
    
    # Save
    doc.save(template_path)
    print(f"\n✓ Template saved: {template_path}")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    add_klsb_number_to_template()

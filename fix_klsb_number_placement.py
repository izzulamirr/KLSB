"""
Fix KLSB number placement in template to match desired format
"""

from docx import Document
import os


def fix_klsb_number_placement():
    """Fix {{klsb_number}} placement to be on its own line after {{name}}"""
    
    template_path = "KLSB_template_true.docx"
    
    if not os.path.exists(template_path):
        print(f"❌ Template not found: {template_path}")
        return
    
    print(f"\n{'='*70}")
    print(f"FIXING KLSB NUMBER PLACEMENT")
    print(f"{'='*70}\n")
    
    doc = Document(template_path)
    
    # Fix headers
    for section_idx, section in enumerate(doc.sections):
        header = section.header
        print(f"\n--- Fixing Header in Section {section_idx + 1} ---")
        
        for para_idx, para in enumerate(header.paragraphs):
            current_text = para.text
            print(f"Para {para_idx}: {current_text[:100] if current_text else '(empty)'}")
            
            # Remove "Ref: {{klsb_number}}" from PROFESSIONAL RESUME paragraph
            if 'PROFESSIONAL RESUME' in current_text and 'Ref:' in current_text:
                print(f"  → Removing 'Ref: {{{{klsb_number}}}}' from PROFESSIONAL RESUME")
                # Clean up the text
                new_text = current_text.replace('\nRef: {{klsb_number}}', '').replace('Ref: {{klsb_number}}', '')
                
                # Clear runs and set clean text
                for run in para.runs:
                    run.text = ''
                if para.runs:
                    para.runs[0].text = new_text
                else:
                    para.add_run(new_text)
                print(f"  ✓ Cleaned: {para.text}")
            
            # If this paragraph has just {{klsb_number}}, replace it with KLSB_{{klsb_number}}
            if para.text.strip() == '{{klsb_number}}':
                print(f"  → Formatting as KLSB_{{{{klsb_number}}}}")
                for run in para.runs:
                    run.text = ''
                if para.runs:
                    para.runs[0].text = 'KLSB_{{klsb_number}}'
                else:
                    para.add_run('KLSB_{{klsb_number}}')
                print(f"  ✓ Updated: {para.text}")
        
        # Also check header tables
        for table in header.tables:
            for row in table.rows:
                for cell in row.cells:
                    for para in cell.paragraphs:
                        current_text = para.text
                        
                        # Remove Ref: from any cell
                        if 'Ref:' in current_text and '{{klsb_number}}' in current_text:
                            print(f"  → Cleaning table cell: {current_text[:60]}")
                            new_text = current_text.replace('\nRef: {{klsb_number}}', '').replace('Ref: {{klsb_number}}', '')
                            for run in para.runs:
                                run.text = ''
                            if para.runs:
                                para.runs[0].text = new_text
                            else:
                                para.add_run(new_text)
                            print(f"  ✓ Cleaned: {para.text}")
                        
                        # Format standalone {{klsb_number}}
                        if para.text.strip() == '{{klsb_number}}':
                            print(f"  → Formatting table cell as KLSB_{{{{klsb_number}}}}")
                            for run in para.runs:
                                run.text = ''
                            if para.runs:
                                para.runs[0].text = 'KLSB_{{klsb_number}}'
                            else:
                                para.add_run('KLSB_{{klsb_number}}')
                            print(f"  ✓ Updated: {para.text}")
    
    # Save
    doc.save(template_path)
    print(f"\n✓ Template fixed and saved!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    fix_klsb_number_placement()

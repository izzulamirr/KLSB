"""
Add tab stops to the working_experience_formatted paragraph for proper colon alignment
"""

from docx import Document
from docx.shared import Inches

def align_formatted_section():
    template_path = "KLSB_template_true.docx"
    
    # Load the document
    doc = Document(template_path)
    
    # Find the paragraph with working_experience_formatted tag
    for idx, para in enumerate(doc.paragraphs):
        if '{{working_experience_formatted}}' in para.text:
            print(f"✓ Found working_experience_formatted at paragraph {idx}")
            
            # Clear existing tab stops
            para.paragraph_format.tab_stops.clear_all()
            
            # Add tab stop at 1.2 inches for colon alignment
            para.paragraph_format.tab_stops.add_tab_stop(Inches(1.2))
            
            print(f"  ✓ Added tab stop at 1.2 inches")
            break
    
    # Save the updated template
    doc.save(template_path)
    print(f"\n✓ Template updated successfully!")
    print(f"✓ Changes saved to: {template_path}")

if __name__ == "__main__":
    align_formatted_section()

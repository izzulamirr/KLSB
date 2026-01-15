"""
Remove the Position template tag from WORKING EXPERIENCE section
"""

from docx import Document

def remove_position_tag():
    template_path = "KLSB_template_true.docx"
    
    # Load the document
    doc = Document(template_path)
    
    # Find and remove the Position paragraph
    for idx, para in enumerate(doc.paragraphs):
        if '{{work_position}}' in para.text:
            print(f"✓ Found Position tag at paragraph {idx}: {para.text}")
            p_element = para._element
            p_element.getparent().remove(p_element)
            print(f"  ✓ Removed paragraph")
            break
    
    # Save the updated template
    doc.save(template_path)
    print(f"\n✓ Template updated successfully!")
    print(f"✓ Changes saved to: {template_path}")

if __name__ == "__main__":
    remove_position_tag()

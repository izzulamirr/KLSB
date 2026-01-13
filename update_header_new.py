"""
Update KLSB template to include professional header with KEMUNCAK LANAI branding
Updated version with paragraph-based layout (no table)
"""

from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH

def update_template_with_header(template_path, output_path="KLSB_template.docx"):
    """
    Update template to add professional header with company branding
    Uses paragraph layout (not table) matching the reference design
    """
    
    doc = Document(template_path)
    section = doc.sections[0]
    header = section.header
    
    # Clear existing header
    for paragraph in list(header.paragraphs):
        p = paragraph._element
        p.getparent().remove(p)
    
    # Row 1: Logo on left, Title on right
    para1 = header.add_paragraph()
    para1.paragraph_format.space_after = Pt(0)
    
    # Company name on left
    run_company = para1.add_run("KEMUNCAK LANAI\nSDN BHD")
    run_company.bold = True
    run_company.font.size = Pt(9)
    
    # Tab to right side
    para1.add_run("\t\t\t\t")
    
    # Title on right (italicized)
    run_title = para1.add_run("PROFESSIONAL RESUME")
    run_title.italic = True
    run_title.bold = True
    run_title.font.size = Pt(14)
    
    # Row 2: NAME tag on right
    para2 = header.add_paragraph()
    para2.paragraph_format.space_after = Pt(0)
    para2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    run_name_label = para2.add_run("NAME")
    run_name_label.italic = True
    run_name_label.font.size = Pt(10)
    
    # Row 3: KLSB_0 on right
    para3 = header.add_paragraph()
    para3.paragraph_format.space_after = Pt(0)
    para3.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    run_klsb = para3.add_run("KLSB_0")
    run_klsb.italic = True
    run_klsb.font.size = Pt(10)
    
    # Row 4: Page number on right
    para4 = header.add_paragraph()
    para4.paragraph_format.space_after = Pt(6)
    para4.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    run_page = para4.add_run("Page 1 of 3")
    run_page.font.size = Pt(9)
    
    # Horizontal line separator
    para_sep = header.add_paragraph()
    para_sep.paragraph_format.space_before = Pt(0)
    para_sep.paragraph_format.space_after = Pt(12)
    run_sep = para_sep.add_run("_" * 100)
    run_sep.font.size = Pt(8)
    
    # Save
    doc.save(output_path)
    print(f"✓ Template updated with paragraph-based header: {output_path}")
    
    return output_path


if __name__ == "__main__":
    # Update template
    update_template_with_header("KLSB_template.docx")

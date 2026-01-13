"""
Create a docxtpl template from the current KLSB DOCX format
This script adds template tags to the KLSB_054 file to make it compatible with docxtpl
"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docxtpl import DocxTemplate

def create_template_from_current():
    """
    Create a template DOCX with {{tags}} from the current KLSB format
    """
    
    print("Creating docxtpl template from current KLSB format...")
    
    # Create a new document
    doc = Document()
    
    # Note: Header is now in document header section (added by update_header.py)
    # No need for body header - start directly with personal info
    
    # Personal info table
    doc.add_paragraph()
    info_table = doc.add_table(rows=8, cols=3)
    info_table.autofit = False
    
    for row in info_table.rows:
        row.cells[0].width = Inches(1.5)
        row.cells[1].width = Inches(0.15)
        row.cells[2].width = Inches(4.0)
    
    # Table data with template tags
    info_data = [
        ("NAME", "{{name}}"),
        ("POSITION", "{{position}}"),
        ("DATE OF BIRTH", "{{dob}}"),
        ("NATIONALITY", "{{nationality}}"),
        ("MARITAL STATUS", "{{marital_status}}"),
        ("CONTACT ADDRESS", "{{address}}"),
        ("Tel", "{{phone}}"),
        ("EMAIL", "{{email}}"),
    ]
    
    for idx, (label, tag) in enumerate(info_data):
        row = info_table.rows[idx]
        
        # Label cell
        label_cell = row.cells[0]
        label_para = label_cell.paragraphs[0]
        label_run = label_para.add_run(label)
        label_run.bold = True
        label_run.font.size = Pt(9)
        
        # Colon cell
        colon_cell = row.cells[1]
        colon_para = colon_cell.paragraphs[0]
        colon_run = colon_para.add_run(":")
        colon_run.bold = True
        colon_run.font.size = Pt(9)
        colon_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Value cell with template tag
        value_cell = row.cells[2]
        value_para = value_cell.paragraphs[0]
        value_run = value_para.add_run(tag)
        value_run.font.size = Pt(9)
    
    # Remove table borders
    from docx.oxml import OxmlElement
    def qn(tag):
        return '{http://schemas.openxmlformats.org/wordprocessingml/2006/main}' + tag
    
    for row in info_table.rows:
        for cell in row.cells:
            tcPr = cell._element.get_or_add_tcPr()
            tcBorders = OxmlElement('w:tcBorders')
            for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
                border = OxmlElement(f'w:{border_name}')
                border.set(qn('val'), 'none')
                tcBorders.append(border)
            tcPr.append(tcBorders)
    
    doc.add_paragraph()
    
    # Experience Summary
    heading = doc.add_paragraph()
    heading.paragraph_format.space_before = Pt(6)
    heading.paragraph_format.space_after = Pt(3)
    run = heading.add_run("EXPERIENCE SUMMARY")
    run.bold = False
    run.font.size = Pt(11)
    
    p = doc.add_paragraph("{{experience_summary}}")
    p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    p.paragraph_format.left_indent = Inches(0.25)
    
    # Education
    doc.add_paragraph()
    heading = doc.add_paragraph()
    heading.paragraph_format.space_before = Pt(6)
    heading.paragraph_format.space_after = Pt(3)
    run = heading.add_run("ACADEMIC/TECHNICAL QUALIFICATIONS:")
    run.bold = True
    run.font.size = Pt(11)
    
    p = doc.add_paragraph("{{education}}")
    p.paragraph_format.left_indent = Inches(0.25)
    
    # Working Experience
    doc.add_paragraph()
    heading = doc.add_paragraph()
    heading.paragraph_format.space_before = Pt(6)
    heading.paragraph_format.space_after = Pt(3)
    run = heading.add_run("WORKING EXPERIENCE")
    run.bold = False
    run.font.size = Pt(11)
    
    p = doc.add_paragraph("{{working_experience}}")
    p.paragraph_format.left_indent = Inches(0.25)
    
    # Skills
    doc.add_paragraph()
    heading = doc.add_paragraph()
    heading.paragraph_format.space_before = Pt(6)
    heading.paragraph_format.space_after = Pt(3)
    run = heading.add_run("OTHERS (TRAININGS/SKILLS/etc.)")
    run.bold = True
    run.font.size = Pt(11)
    
    p = doc.add_paragraph("{{skills}}")
    p.paragraph_format.left_indent = Inches(0.25)
    
    # Professional Membership
    doc.add_paragraph()
    heading = doc.add_paragraph()
    heading.paragraph_format.space_before = Pt(6)
    heading.paragraph_format.space_after = Pt(3)
    run = heading.add_run("PROFESSIONAL MEMBERSHIP")
    run.bold = True
    run.font.size = Pt(11)
    
    p = doc.add_paragraph("{{professional_memberships}}")
    p.paragraph_format.left_indent = Inches(0.25)
    
    # Professional Training
    doc.add_paragraph()
    heading = doc.add_paragraph()
    heading.paragraph_format.space_before = Pt(6)
    heading.paragraph_format.space_after = Pt(3)
    run = heading.add_run("PROFESSIONAL TRAINING / COMPETENCY")
    run.bold = True
    run.font.size = Pt(11)
    
    p = doc.add_paragraph("{{professional_training}}")
    p.paragraph_format.left_indent = Inches(0.25)
    
    # Computer Skills
    doc.add_paragraph()
    heading = doc.add_paragraph()
    heading.paragraph_format.space_before = Pt(6)
    heading.paragraph_format.space_after = Pt(3)
    run = heading.add_run("COMPUTER SKILLS")
    run.bold = True
    run.font.size = Pt(11)
    
    p = doc.add_paragraph("{{computer_skills}}")
    p.paragraph_format.left_indent = Inches(0.25)
    
    # Save as template
    doc.save("KLSB_template.docx")
    print("✓ Template created: KLSB_template.docx")
    
    # Verify with docxtpl
    try:
        template = DocxTemplate("KLSB_template.docx")
        print("✓ Template verified with docxtpl")
    except Exception as e:
        print(f"✗ Template verification failed: {e}")


if __name__ == "__main__":
    create_template_from_current()

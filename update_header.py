"""
Update KLSB template to include professional header with KEMUNCAK LANAI logo
"""

from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

def update_template_with_header(template_path, logo_path=None, output_path="KLSB_template.docx"):
    """
    Update template to add professional header with logo and company info
    
    Args:
        template_path: Path to existing template
        logo_path: Path to logo image file (optional)
        output_path: Path to save updated template
    """
    
    doc = Document(template_path)
    
    # Access the header
    section = doc.sections[0]
    header = section.header
    
    # Clear existing header content
    for paragraph in list(header.paragraphs):
        p = paragraph._element
        p.getparent().remove(p)
    
    # Row 1: Logo on left, Title and info on right
    para1 = header.add_paragraph()
    para1.paragraph_format.space_after = Pt(0)
    
    # Add company name on left
    run_company = para1.add_run("KEMUNCAK LANAI\nSDN BHD")
    run_company.bold = True
    run_company.font.size = Pt(9)
    
    # Add tab to move to right side
    para1.add_run("\t\t\t")
    
    # Add title on right (italicized)
    run_title = para1.add_run("PROFESSIONAL RESUME")
    run_title.italic = True
    run_title.bold = True
    run_title.font.size = Pt(14)
    
    # Row 2: Name and KLSB info on right
    para2 = header.add_paragraph()
    para2.paragraph_format.space_after = Pt(0)
    para2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    
    run_name = para2.add_run("NAME")
    run_name.italic = True
    run_name.font.size = Pt(10)
    
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
    
    # Add horizontal line separator
    para_sep = header.add_paragraph()
    para_sep.paragraph_format.space_before = Pt(3)
    para_sep.paragraph_format.space_after = Pt(12)
    run_sep = para_sep.add_run("_" * 100)
    run_sep.font.size = Pt(8)
    
    # Save updated template
    doc.save(output_path)
    print(f"✓ Template updated with header: {output_path}")
    
    return output_path


def add_header_to_docx(doc_path, new_name, logo_path=None):
    """
    Add or update header in existing DOCX file
    
    Args:
        doc_path: Path to DOCX file
        new_name: Name to display in header
        logo_path: Path to logo image (optional)
    """
    
    doc = Document(doc_path)
    section = doc.sections[0]
    header = section.header
    
    # Clear existing header
    for paragraph in list(header.paragraphs):
        p = paragraph._element
        p.getparent().remove(p)
    
    # Create header table (2 rows, 3 columns) with width
    from docx.shared import Inches
    header_table = header.add_table(rows=2, cols=3, width=Inches(6.0))
    header_table.autofit = False
    
    # Set column widths
    for row in header_table.rows:
        row.cells[0].width = Inches(1.2)
        row.cells[1].width = Inches(2.5)
        row.cells[2].width = Inches(1.3)
    
    # ROW 1: Logo/Company, Title, Page
    
    # Left - Logo or Company Name
    left_cell = header_table.rows[0].cells[0]
    left_para = left_cell.paragraphs[0]
    
    if logo_path and os.path.exists(logo_path):
        try:
            run = left_para.add_run()
            run.add_picture(logo_path, width=Inches(1.0))
        except:
            left_run = left_para.add_run("KEMUNCAK LANAI\nSDN BHD")
            left_run.bold = True
            left_run.font.size = Pt(9)
    else:
        left_run = left_para.add_run("KEMUNCAK LANAI\nSDN BHD")
        left_run.bold = True
        left_run.font.size = Pt(9)
    
    left_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Center - Title
    center_cell = header_table.rows[0].cells[1]
    center_para = center_cell.paragraphs[0]
    center_run = center_para.add_run("PROFESSIONAL RESUME")
    center_run.bold = True
    center_run.font.size = Pt(12)
    center_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Right - Page
    right_cell = header_table.rows[0].cells[2]
    right_para = right_cell.paragraphs[0]
    right_run = right_para.add_run("Page 1 of 3")
    right_run.font.size = Pt(9)
    right_para.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # ROW 2: Name label, Name value, KLSB
    
    # Left - Label
    left_cell2 = header_table.rows[1].cells[0]
    left_para2 = left_cell2.paragraphs[0]
    left_run2 = left_para2.add_run("NAME")
    left_run2.bold = True
    left_run2.font.size = Pt(9)
    left_para2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Center - Name value
    center_cell2 = header_table.rows[1].cells[1]
    center_para2 = center_cell2.paragraphs[0]
    center_run2 = center_para2.add_run(new_name.upper())
    center_run2.font.size = Pt(9)
    center_para2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Right - KLSB ID
    right_cell2 = header_table.rows[1].cells[2]
    right_para2 = right_cell2.paragraphs[0]
    right_run2 = right_para2.add_run("KLSB_0")
    right_run2.font.size = Pt(9)
    right_para2.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Add subtle borders
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
    
    def set_cell_border(cell):
        tc = cell._element
        tcPr = tc.get_or_add_tcPr()
        tcBorders = OxmlElement('w:tcBorders')
        
        for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
            edge_element = OxmlElement(f'w:{edge}')
            edge_element.set(qn('w:val'), 'single')
            edge_element.set(qn('w:sz'), '12')
            edge_element.set(qn('w:space'), '0')
            edge_element.set(qn('w:color'), 'CCCCCC')
            tcBorders.append(edge_element)
        
        tcPr.append(tcBorders)
    
    for row in header_table.rows:
        for cell in row.cells:
            set_cell_border(cell)
    
    # Add spacing
    last_para = header.paragraphs[-1]
    if last_para:
        last_para.paragraph_format.space_after = Pt(12)
    
    doc.save(doc_path)
    print(f"✓ Header added to: {doc_path}")


if __name__ == "__main__":
    import os
    
    # Update template with header
    template_path = "KLSB_template.docx"
    logo_path = "logo_kemuncak.png"  # If logo file exists
    
    update_template_with_header(template_path, logo_path=None)  # None to use text fallback

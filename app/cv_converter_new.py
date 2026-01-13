import os
import re
import base64
import json
from pathlib import Path
from typing import Dict, Tuple, Optional

# Optional dependencies
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    from pdf2image import convert_from_path
except Exception:
    convert_from_path = None

# Word document generation
docx_available = True
try:
    from docx import Document
    from docx.shared import Pt, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
except Exception:
    docx_available = False

reportlab_available = True
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
except Exception:
    reportlab_available = False


def slugify_filename(name: str) -> str:
    name = name or "cv"
    name = name.strip().lower()
    name = re.sub(r"[^a-z0-9]+", "-", name)
    return name.strip("-") or "cv"


def _get_next_cv_number(output_dir: str) -> str:
    """Get next CV number in format KLSB_001, KLSB_002, etc."""
    if not os.path.exists(output_dir):
        return "KLSB_001"
    
    existing_files = []
    for filename in os.listdir(output_dir):
        match = re.match(r'KLSB_(\d{3})', filename)
        if match:
            existing_files.append(int(match.group(1)))
    
    if not existing_files:
        return "KLSB_001"
    
    next_num = max(existing_files) + 1
    return f"KLSB_{next_num:03d}"


def _extract_cv_with_chatgpt(path: str, api_key: str = None) -> Dict[str, str]:
    """Extract and parse CV using ChatGPT Vision API in one go.
    
    Returns structured data directly from ChatGPT parsing.
    """
    if not OpenAI:
        raise RuntimeError("OpenAI library not installed. Run: pip install openai")
    
    # Get API key
    if not api_key:
        try:
            from config import BaseConfig
            api_key = BaseConfig.OPENAI_API_KEY
        except:
            pass
    
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OpenAI API key not configured. Set in config.py or OPENAI_API_KEY environment variable.")
    
    client = OpenAI(api_key=api_key)
    
    # Convert PDF pages to images
    if not convert_from_path:
        raise RuntimeError("pdf2image not installed. Run: pip install pdf2image")
    
    try:
        images = convert_from_path(path, dpi=200, first_page=1, last_page=3)
    except Exception as e:
        raise RuntimeError(f"pdf2image/Poppler error: {str(e)}. Install Poppler and add to PATH.")
    
    # Collect all extracted text from all pages
    all_text = ""
    try:
        for img in images:
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                img.save(tmp.name, "PNG")
                tmp_path = tmp.name
            
            try:
                with open(tmp_path, "rb") as img_file:
                    img_data = base64.b64encode(img_file.read()).decode('utf-8')
                
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Extract ALL text from this CV page. Preserve formatting and all content."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/png;base64,{img_data}"}
                                }
                            ]
                        }
                    ],
                    max_tokens=2000
                )
                all_text += response.choices[0].message.content + "\n\n"
            finally:
                try:
                    os.unlink(tmp_path)
                except:
                    pass
    except Exception as e:
        raise RuntimeError(f"ChatGPT OCR failed: {str(e)}")
    
    # Now use ChatGPT to parse the extracted text into structured fields
    try:
        parse_response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": f"""Parse this CV text and extract fields. Return ONLY valid JSON, no other text or markdown.

CV Text:
{all_text}

Return JSON with these exact keys (use empty string "" if not found):
{{"name": "Full name", "position": "Position applied for", "dob": "Date of birth", "nationality": "Nationality (default MALAYSIAN)", "marital_status": "Marital status", "address": "Contact address", "phone": "Phone number", "email": "Email address", "education": "Education section all text", "experience_summary": "Experience summary paragraph", "working_experience": "Working experience section with all roles and duties"}}"""
                }
            ],
            temperature=0.3
        )
        
        response_text = parse_response.choices[0].message.content
        # Extract JSON from response
        json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if json_match:
            parsed = json.loads(json_match.group())
        else:
            parsed = json.loads(response_text)
        
        # Set defaults
        parsed.setdefault("name", "Candidate")
        parsed.setdefault("nationality", "MALAYSIAN")
        
        return parsed
    except Exception as e:
        raise RuntimeError(f"ChatGPT parsing failed: {str(e)}")


def _build_docx_simple(output_path: str, fields: Dict[str, str], logo_path: str = None, cv_number: str = "KLSB_001") -> None:
    """Generate KLSB format Word document using ChatGPT extracted fields.
    
    Simplified version that directly uses ChatGPT-provided content without re-parsing.
    """
    if not docx_available:
        raise RuntimeError("python-docx is required for Word conversion. Please install python-docx==1.1.2")
    
    doc = Document()
    
    # Set margins
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
    
    # Create header table with logo
    if logo_path and os.path.exists(logo_path):
        header_table = doc.add_table(rows=1, cols=2)
        header_table.autofit = False
        header_table.allow_autofit = False
        
        left_cell = header_table.rows[0].cells[0]
        left_cell.width = Inches(2.0)
        logo_para = left_cell.paragraphs[0]
        logo_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
        try:
            logo_run = logo_para.add_run()
            logo_run.add_picture(logo_path, width=Inches(1.9), height=Inches(0.65))
        except:
            pass
        
        right_cell = header_table.rows[0].cells[1]
        right_cell.width = Inches(4.5)
        header_p = right_cell.paragraphs[0]
        header_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Remove cell borders
        from docx.oxml import OxmlElement
        def set_cell_border(cell):
            tc = cell._element
            tcPr = tc.get_or_add_tcPr()
            tcBorders = OxmlElement('w:tcBorders')
            for edge in ('top', 'left', 'bottom', 'right', 'insideH', 'insideV'):
                edge_element = OxmlElement(f'w:{edge}')
                edge_element.set(qn('w:val'), 'none')
                edge_element.set(qn('w:sz'), '0')
                tcBorders.append(edge_element)
            tcPr.append(tcBorders)
        set_cell_border(left_cell)
        set_cell_border(right_cell)
    else:
        header_p = doc.add_paragraph()
        header_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Header section
    run = header_p.add_run("CURRICULUM VITAE")
    run.bold = True
    run.font.size = Pt(14)
    header_p.add_run("\n")
    
    run = header_p.add_run(fields.get("name", "CANDIDATE NAME").upper())
    run.bold = True
    run.font.size = Pt(12)
    
    # Separator
    sep_p = doc.add_paragraph("-" * 100)
    sep_p.paragraph_format.space_before = Pt(3)
    sep_p.paragraph_format.space_after = Pt(6)
    
    # Personal Information
    doc.add_paragraph()
    
    for key, label in [
        ("name", "Name"),
        ("position", "Position Applied"),
        ("dob", "Date of Birth"),
        ("nationality", "Nationality"),
        ("marital_status", "Marital Status"),
        ("address", "Contact Address"),
        ("phone", "Contact Number"),
        ("email", "Email")
    ]:
        if fields.get(key):
            p = doc.add_paragraph()
            p.add_run(f"{label}: {fields.get(key, '')}")
    
    # Add space
    doc.add_paragraph()
    
    # EDUCATION section - direct from ChatGPT
    education = fields.get("education", "").strip()
    if education:
        heading = doc.add_paragraph()
        heading.paragraph_format.space_before = Pt(6)
        heading.paragraph_format.space_after = Pt(3)
        run = heading.add_run("EDUCATION")
        run.bold = True
        run.font.size = Pt(11)
        
        for line in education.split('\n'):
            line = line.strip()
            if line:
                p = doc.add_paragraph(line)
                p.paragraph_format.left_indent = Inches(0.25)
                p.paragraph_format.space_after = Pt(2)
    
    # EXPERIENCE SUMMARY section - direct from ChatGPT
    summary = fields.get("experience_summary", "").strip()
    if summary:
        doc.add_paragraph()
        heading = doc.add_paragraph()
        heading.paragraph_format.space_before = Pt(6)
        heading.paragraph_format.space_after = Pt(3)
        run = heading.add_run("EXPERIENCE SUMMARY")
        run.bold = True
        run.font.size = Pt(11)
        
        p = doc.add_paragraph(summary)
        p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
        p.paragraph_format.space_after = Pt(6)
    
    # WORKING EXPERIENCE section - direct from ChatGPT
    experience = fields.get("working_experience", "").strip()
    if experience:
        doc.add_paragraph()
        heading = doc.add_paragraph()
        heading.paragraph_format.space_before = Pt(6)
        heading.paragraph_format.space_after = Pt(3)
        run = heading.add_run("WORKING EXPERIENCE")
        run.bold = True
        run.font.size = Pt(11)
        
        # Simple formatting: preserve ChatGPT's structure
        for line in experience.split('\n'):
            line = line.strip()
            if not line:
                continue
            
            # Check if it's a bullet point
            if line.startswith(('•', '-', '*')):
                line = re.sub(r'^[•\-\*]\s*', '', line)
                p = doc.add_paragraph(line, style='List Bullet')
                p.paragraph_format.space_after = Pt(2)
            # Check if it looks like a position/year line (has parentheses)
            elif '(' in line and ')' in line:
                p = doc.add_paragraph(line)
                if p.runs:
                    p.runs[0].bold = True
                p.paragraph_format.space_after = Pt(0)
            else:
                p = doc.add_paragraph(line)
                p.paragraph_format.space_after = Pt(2)
    
    doc.save(output_path)


def _build_pdf_simple(output_path: str, fields: Dict[str, str], logo_path: str = None, cv_number: str = "KLSB_001") -> None:
    """Generate KLSB format PDF using ChatGPT extracted fields."""
    if not reportlab_available:
        raise RuntimeError("reportlab is required for CV conversion.")
    
    doc = SimpleDocTemplate(
        output_path, 
        pagesize=letter, 
        topMargin=0.6 * inch, 
        bottomMargin=0.6 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch
    )
    styles = getSampleStyleSheet()
    
    elements = []
    
    # Header with logo
    if logo_path and os.path.exists(logo_path):
        from reportlab.platypus import Image
        logo = Image(logo_path, width=1.9*inch, height=0.65*inch)
        header_table = Table([[logo, Paragraph(f"<b>CURRICULUM VITAE</b><br/><b>{fields.get('name', '').upper()}</b>", ParagraphStyle("Header", parent=styles["Normal"], fontSize=14, fontName="Helvetica-Bold", alignment=TA_CENTER))]], colWidths=[2*inch, 4.7*inch])
        header_table.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "MIDDLE"), ("ALIGN", (1, 0), (1, 0), "CENTER")]))
        elements.append(header_table)
    else:
        elements.append(Paragraph(f"<b>CURRICULUM VITAE</b><br/><b>{fields.get('name', '').upper()}</b>", ParagraphStyle("Header", parent=styles["Normal"], fontSize=14, fontName="Helvetica-Bold", alignment=TA_CENTER)))
    
    elements.append(Spacer(1, 0.2*inch))
    
    # Personal info
    for key, label in [("name", "NAME"), ("position", "POSITION"), ("dob", "DATE OF BIRTH"), ("nationality", "NATIONALITY"), ("marital_status", "MARITAL STATUS"), ("address", "ADDRESS"), ("phone", "PHONE"), ("email", "EMAIL")]:
        if fields.get(key):
            elements.append(Paragraph(f"<b>{label}</b>: {fields.get(key, '')}", ParagraphStyle("Info", parent=styles["Normal"], fontSize=9)))
    
    elements.append(Spacer(1, 0.1*inch))
    
    # Education
    if fields.get("education"):
        elements.append(Paragraph("<b>EDUCATION</b>", ParagraphStyle("SectionHeader", parent=styles["Normal"], fontSize=11, fontName="Helvetica-Bold")))
        for line in fields["education"].split('\n'):
            if line.strip():
                elements.append(Paragraph(line.strip(), ParagraphStyle("Text", parent=styles["Normal"], fontSize=9)))
        elements.append(Spacer(1, 0.1*inch))
    
    # Experience Summary
    if fields.get("experience_summary"):
        elements.append(Paragraph("<b>EXPERIENCE SUMMARY</b>", ParagraphStyle("SectionHeader", parent=styles["Normal"], fontSize=11, fontName="Helvetica-Bold")))
        elements.append(Paragraph(fields["experience_summary"], ParagraphStyle("Text", parent=styles["Normal"], fontSize=9, alignment=TA_JUSTIFY)))
        elements.append(Spacer(1, 0.1*inch))
    
    # Working Experience
    if fields.get("working_experience"):
        elements.append(Paragraph("<b>WORKING EXPERIENCE</b>", ParagraphStyle("SectionHeader", parent=styles["Normal"], fontSize=11, fontName="Helvetica-Bold")))
        for line in fields["working_experience"].split('\n'):
            if line.strip():
                elements.append(Paragraph(line.strip(), ParagraphStyle("Text", parent=styles["Normal"], fontSize=9)))
    
    doc.build(elements)


def convert_cv_to_klsb_ocr(source_path: str, output_dir: str, overrides: Optional[Dict[str, str]] = None, output_format: str = "docx") -> Tuple[str, Dict[str, str]]:
    """Convert a CV into KLSB format using ChatGPT extraction only (no parsing).
    
    Args:
        source_path: Path to source CV file
        output_dir: Directory to save converted file
        overrides: Optional field overrides
        output_format: Output format - "docx" (Word) or "pdf"

    Returns: (output_path, detected_fields)
    """
    import time
    
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source CV not found: {source_path}")

    # Extract and parse with ChatGPT in one call
    fields = _extract_cv_with_chatgpt(source_path)

    # Apply overrides
    overrides = overrides or {}
    for key, val in overrides.items():
        if val:
            fields[key] = val

    os.makedirs(output_dir, exist_ok=True)
    slug = slugify_filename(fields.get("name"))
    cv_number = _get_next_cv_number(output_dir)
    
    # Determine output format
    if output_format.lower() == "docx":
        output_name = f"{cv_number}_{slug}.docx"
        output_path = os.path.join(output_dir, output_name)
        
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except PermissionError:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                output_name = f"{cv_number}_{slug}_{timestamp}.docx"
                output_path = os.path.join(output_dir, output_name)
        
        logo_path = os.path.join(os.path.dirname(__file__), "static", "img", "logo.png")
        _build_docx_simple(output_path, fields, logo_path, cv_number)
    else:
        output_name = f"{cv_number}_{slug}.pdf"
        output_path = os.path.join(output_dir, output_name)
        
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
            except PermissionError:
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                output_name = f"{cv_number}_{slug}_{timestamp}.pdf"
                output_path = os.path.join(output_dir, output_name)
        
        logo_path = os.path.join(os.path.dirname(__file__), "static", "img", "logo.png")
        _build_pdf_simple(output_path, fields, logo_path, cv_number)
    
    return output_path, fields

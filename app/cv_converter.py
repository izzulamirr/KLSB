import os
import re
import base64
from pathlib import Path
from typing import Dict, Tuple, Optional

# Optional dependencies
try:  # Lightweight text extraction for text-based PDFs
    from pypdf import PdfReader
except Exception:  # pragma: no cover - optional
    PdfReader = None

try:  # OpenAI for ChatGPT OCR
    from openai import OpenAI
except Exception:  # pragma: no cover - optional
    OpenAI = None

try:  # OCR fallback (requires poppler + tesseract installed on the system)
    from pdf2image import convert_from_path
    import pytesseract
except Exception:  # pragma: no cover - optional
    convert_from_path = None
    pytesseract = None

# Word document generation
docx_available = True
try:
    from docx import Document
    from docx.shared import Pt, RGBColor, Inches
    from docx.enum.text import WD_ALIGN_PARAGRAPH
    from docx.oxml.ns import qn
    from docx.oxml import OxmlElement
except Exception:
    docx_available = False

reportlab_available = True
try:  # PDF generation
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
except Exception:  # pragma: no cover - optional until conversion is invoked
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
    
    # Find all existing KLSB files
    existing_files = []
    for filename in os.listdir(output_dir):
        match = re.match(r'KLSB_(\d{3})', filename)
        if match:
            existing_files.append(int(match.group(1)))
    
    if not existing_files:
        return "KLSB_001"
    
    # Get the highest number and increment
    next_num = max(existing_files) + 1
    return f"KLSB_{next_num:03d}"


def _extract_text_with_chatgpt(path: str, api_key: str = None) -> str:
    """Extract text from PDF using ChatGPT Vision API."""
    if not OpenAI:
        raise RuntimeError("OpenAI library not installed. Run: pip install openai")
    
    # Get API key from parameter, config, or environment
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
        # Convert first 3 pages to images (requires Poppler to be installed)
        images = convert_from_path(path, dpi=200, first_page=1, last_page=3)
    except Exception as e:
        # pdf2image needs Poppler installed on Windows
        raise RuntimeError(f"pdf2image/Poppler error: {str(e)}. Install Poppler and add to PATH.")
    
    try:
        extracted_texts = []
        for idx, img in enumerate(images):
            # Save image temporarily
            import tempfile
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                img.save(tmp.name, "PNG")
                tmp_path = tmp.name
            
            try:
                # Read image and encode to base64
                with open(tmp_path, "rb") as img_file:
                    img_data = base64.b64encode(img_file.read()).decode('utf-8')
                
                # Call ChatGPT Vision API
                response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Extract ALL text from this CV/resume page. Preserve the exact formatting, section headers (EDUCATION, EXPERIENCE, etc.), bullet points, dates, and line breaks. Return ONLY the extracted text with no additional commentary."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": f"data:image/png;base64,{img_data}"
                                    }
                                }
                            ]
                        }
                    ],
                    max_tokens=2000
                )
                
                page_text = response.choices[0].message.content
                extracted_texts.append(page_text)
            finally:
                # Clean up temp file
                try:
                    os.unlink(tmp_path)
                except:
                    pass
        
        return "\n\n".join(extracted_texts)
    
    except Exception as e:
        raise RuntimeError(f"ChatGPT OCR failed: {str(e)}")


def _extract_text_from_pdf(path: str, use_chatgpt: bool = None) -> str:
    """Extract text from a PDF using pypdf, fallback to OCR when needed.
    
    Args:
        path: Path to PDF file
        use_chatgpt: If True, use ChatGPT OCR. If None, auto-detect based on OPENAI_API_KEY.
    """
    # Auto-detect ChatGPT usage from config or environment
    if use_chatgpt is None:
        api_key = None
        try:
            from config import BaseConfig
            api_key = BaseConfig.OPENAI_API_KEY
        except:
            pass
        api_key = api_key or os.environ.get("OPENAI_API_KEY")
        use_chatgpt = bool(api_key and OpenAI)
    
    # Try ChatGPT OCR first if enabled
    if use_chatgpt:
        try:
            return _extract_text_with_chatgpt(path)
        except Exception as e:
            # Fall back to traditional OCR
            print(f"ChatGPT OCR failed, falling back: {e}")
    
    text = ""

    if PdfReader:
        try:
            reader = PdfReader(path)
            for page in reader.pages:
                page_text = page.extract_text() or ""
                text += page_text + "\n"
        except Exception:
            # Ignore and fall back to OCR
            text = ""

    # If we have little or no text, try OCR on the first couple pages
    if (not text or len(text.strip()) < 50) and convert_from_path and pytesseract:
        try:
            images = convert_from_path(path, dpi=200, first_page=1, last_page=2)
            ocr_chunks = []
            for img in images:
                ocr_chunks.append(pytesseract.image_to_string(img))
            text = "\n".join(ocr_chunks)
        except Exception:
            # If OCR fails, raise a helpful error below
            text = text or ""

    if not text or len(text.strip()) < 10:
        raise RuntimeError(
            "Unable to extract text from CV. Ensure the PDF is text-based or install poppler + tesseract for OCR."
        )

    # Preserve bullet points and line structure
    # Clean up common bullet characters to standardize
    text = re.sub(r'[�▪▫■□●○◆◇]', '•', text)
    
    return text


def _guess_fields(text: str) -> Dict[str, str]:
    """Heuristic extraction of common CV fields matching KLSB_877 format."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    joined = "\n".join(lines)

    # Email detection
    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", joined)
    
    # Phone detection (including Tel: format) - improved to avoid years
    phone_match = re.search(r"(?:Tel|Phone|Mobile|Contact)\s*:?\s*(\+?\d[\d\s().-]{7,})", joined, re.I)
    
    # Name extraction - look for "NAME :" format and clean it
    name = None
    name_match = re.search(r"NAME\s*:\s*([A-Z][A-Z\s]+(?:BIN|BINTI)\s+[A-Z\s]+)", joined, re.I)
    if name_match:
        name = name_match.group(1).strip()
        # Clean up - remove line breaks and extra words
        name = re.sub(r'\s+', ' ', name)
        # Stop at common keywords that shouldn't be in name
        for stop_word in ['POSITION', 'DATE', 'NATIONALITY', 'PROFESSIONAL']:
            if stop_word in name.upper():
                name = name[:name.upper().index(stop_word)].strip()
    
    if not name:
        # Pick the first reasonable name-looking line near the top
        for ln in lines[:8]:
            if re.search(r"\bemail\b", ln, re.I) or re.search(r"@", ln):
                continue
            if re.search(r"^\d", ln):
                continue
            # Look for lines with BIN/BINTI or multiple capitalized words
            if re.search(r'\bBIN\b|\bBINTI\b', ln, re.I) or (len(ln.split()) >= 2 and len(ln) < 60):
                name = ln
                break
    
    # Position extraction - look for "POSITION :" format
    position = None
    position_match = re.search(r"POSITION\s*:\s*([A-Z][A-Z\s/]+?)(?=\n|DATE OF BIRTH|NATIONALITY|$)", joined, re.I)
    if position_match:
        position = position_match.group(1).strip()
        # Clean up multi-line positions
        position = re.sub(r'\s+', ' ', position)
    else:
        for ln in lines[:15]:
            if re.search(r"^(SENIOR|JUNIOR|LEAD|PRINCIPAL|CHIEF).*?(DESIGNER|ENGINEER|MANAGER|DEVELOPER)", ln, re.I):
                position = ln
                break
    
    # Date of Birth extraction
    dob = ""
    dob_match = re.search(r"DATE OF BIRTH\s*:\s*(\d{1,2}\s+[A-Z]+\s+\d{4})", joined, re.I)
    if dob_match:
        dob = dob_match.group(1).strip()
    
    # Nationality extraction
    nationality = "MALAYSIAN"  # Default
    nat_match = re.search(r"NATIONALITY\s*:\s*(\w+)", joined, re.I)
    if nat_match:
        nationality = nat_match.group(1).strip()
    
    # Marital Status extraction
    marital = ""
    marital_match = re.search(r"MARITAL STATUS\s*:\s*(\w+)", joined, re.I)
    if marital_match:
        marital = marital_match.group(1).strip()
    
    # Address extraction - improved to stop at Tel or Email
    address = ""
    addr_match = re.search(r"(?:CONTACT )?ADDRESS\s*:\s*(.+?)(?=\nTel:|Tel:|Email:|NATIONALITY|ACADEMIC|EXPERIENCE|$)", joined, re.I | re.DOTALL)
    if addr_match:
        address = addr_match.group(1).strip()
        # Clean up address - remove excessive line breaks
        address = re.sub(r'\s+', ' ', address)[:200]

    return {
        "name": name or "Candidate",
        "email": email_match.group(0) if email_match else "",
        "phone": phone_match.group(1).strip() if phone_match else "",
        "position": position or "",
        "dob": dob,
        "nationality": nationality,
        "marital_status": marital,
        "address": address,
    }


def _build_docx(output_path: str, fields: Dict[str, str], source_text: str, logo_path: str = None, cv_number: str = "KLSB_001") -> None:
    """Generate KLSB format Word document matching the exact PDF format with highlighting."""
    if not docx_available:
        raise RuntimeError("python-docx is required for Word conversion. Please install python-docx==1.1.2")
    
    doc = Document()
    
    # Set margins to match PDF
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.6)
        section.bottom_margin = Inches(0.6)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
    
    # Create header table with logo on the left and centered header text on the right
    if logo_path and os.path.exists(logo_path):
        header_table = doc.add_table(rows=1, cols=2)
        header_table.autofit = False
        header_table.allow_autofit = False
        
        # Left cell - Larger logo
        left_cell = header_table.rows[0].cells[0]
        left_cell.width = Inches(2.2)
        logo_para = left_cell.paragraphs[0]
        logo_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
        try:
            logo_run = logo_para.add_run()
            logo_run.add_picture(logo_path, width=Inches(1.9))
        except:
            pass
        
        # Right cell - Centered header text
        right_cell = header_table.rows[0].cells[1]
        right_cell.width = Inches(4.8)
        header_p = right_cell.paragraphs[0]
        header_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Remove cell borders for clean layout
        from docx.oxml import OxmlElement
        from docx.oxml.ns import qn
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
        # No logo, just add header text normally
        header_p = doc.add_paragraph()
        header_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    
    # Header section text
    run1 = header_p.add_run("PROFESSIONAL RESUME")
    run1.bold = True
    run1.font.size = Pt(16)
    header_p.add_run("  \n")
    
    run2 = header_p.add_run(fields.get("name", "CANDIDATE NAME").upper())
    run2.bold = True
    run2.font.size = Pt(14)
    header_p.add_run("  \n")
    
    run3 = header_p.add_run(cv_number)
    run3.bold = True
    run3.font.size = Pt(12)
    
    # Add separator line
    sep_p = doc.add_paragraph("_" * 110)
    sep_p.paragraph_format.space_before = Pt(6)
    sep_p.paragraph_format.space_after = Pt(6)
    
    # Personal information block (no table) to match CV header layout
    info_items = [
        ("NAME", fields.get("name", "").upper()),
        ("POSITION", fields.get("position", "").upper()),
        ("DATE OF BIRTH", fields.get("dob", "")),
        ("NATIONALITY", fields.get("nationality", "MALAYSIAN").upper()),
        ("MARITAL STATUS", fields.get("marital_status", "").upper()),
        ("CONTACT ADDRESS", fields.get("address", "")),
        ("", "Tel: " + fields.get("phone", "") if fields.get("phone") else ""),
        ("EMAIL", fields.get("email", "").lower() if fields.get("email") else ""),
    ]

    for label, value in info_items:
        if not label and not value:
            continue
        p = doc.add_paragraph()
        if label:
            lbl_run = p.add_run(label)
            lbl_run.bold = True
        if label:
            p.add_run(" : ")
        p.add_run(value)

    # Add space after info block
    doc.add_paragraph()
    
    # Parse sections
    sections_dict = _parse_cv_sections(source_text)
    
    # Add ACADEMIC/TECHNICAL QUALIFICATIONS with YELLOW highlighting
    if "qualifications" in sections_dict:
        heading = doc.add_paragraph()
        run = heading.add_run("ACADEMIC/TECHNICAL QUALIFICATIONS:")
        run.bold = True
        run.font.size = Pt(12)
        run.font.highlight_color = 6  # Yellow highlight
        heading.paragraph_format.space_before = Pt(12)
        heading.paragraph_format.space_after = Pt(6)
        
        doc.add_paragraph()  # Blank line
        
        # Parse qualification entries
        qual_text = sections_dict["qualifications"]
        qual_lines = [ln.strip() for ln in qual_text.splitlines() if ln.strip()]
        
        for line in qual_lines:
            if line and not line.startswith("Period") and not line.startswith("Description"):
                p = doc.add_paragraph(line)
                for run in p.runs:
                    run.font.highlight_color = 6  # Yellow
                p.paragraph_format.left_indent = Inches(0.5)
    
    # Add EXPERIENCE SUMMARY
    if "experience_summary" in sections_dict:
        doc.add_paragraph()
        heading = doc.add_paragraph()
        run = heading.add_run("EXPERIENCE SUMMARY")
        run.bold = True
        run.font.size = Pt(12)
        heading.paragraph_format.space_before = Pt(12)
        heading.paragraph_format.space_after = Pt(6)
        
        # Format as continuous text, not bullets (like the PDF)
        summary_text = sections_dict["experience_summary"]
        p = doc.add_paragraph(summary_text)
        p.paragraph_format.left_indent = Inches(0)
        p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
    
    # Add WORKING EXPERIENCE with simplified layout
    if "working_experience" in sections_dict:
        doc.add_paragraph()
        heading = doc.add_paragraph()
        run = heading.add_run("WORKING EXPERIENCE")
        run.bold = True
        run.font.size = Pt(12)
        heading.paragraph_format.space_before = Pt(12)
        heading.paragraph_format.space_after = Pt(6)
        
        doc.add_paragraph()  # Blank line
        
        work_blocks = _parse_work_experience_blocks(sections_dict["working_experience"])
        
        for idx, block in enumerate(work_blocks, start=1):
            # Position + Year on first line
            position_line_parts = []
            if "position" in block:
                position_line_parts.append(block["position"])
            if "year" in block:
                position_line_parts.append(f"({block['year']})")
            if position_line_parts:
                p = doc.add_paragraph(" ".join(position_line_parts))
                p.runs[0].bold = True
            
            # Company on its own line with optional highlight
            if "company" in block:
                p = doc.add_paragraph(block["company"])
                # Highlight if contains "Sdn Bhd" or "Bhd"
                if re.search(r'\b(Sdn\.?\s*Bhd|Bhd)\b', block["company"], re.I):
                    p.runs[0].font.highlight_color = 6  # Yellow
            
            # Projects with GREEN highlighting
            if "projects" in block and block["projects"]:
                p = doc.add_paragraph()
                proj_run = p.add_run("Project Involved:")
                proj_run.bold = True
                proj_run.font.highlight_color = 4  # Green highlight
                
                for project in block["projects"]:
                    proj_p = doc.add_paragraph("• " + project)
                    proj_p.paragraph_format.left_indent = Inches(0.5)
                    for run in proj_p.runs:
                        run.font.highlight_color = 4  # Green
            
            # Job Description
            if "description" in block and block["description"]:
                for desc_point in block["description"]:
                    desc_p = doc.add_paragraph("• " + desc_point)
                    desc_p.paragraph_format.left_indent = Inches(0.5)
            
            # Add space between companies
            doc.add_paragraph()
    
    # Save the document
    doc.save(output_path)


def _extract_bullet_points(text: str) -> list:
    """Extract bullet points from text."""
    bullets = []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    
    has_bullets = any(ln.startswith('•') or ln.startswith('-') or ln.startswith('*') for ln in lines)
    
    if has_bullets:
        for line in lines:
            line = re.sub(r'^[•\-\*�▪]\s*', '', line.strip())
            if len(line) > 5:
                bullets.append(line)
    else:
        full_text = ' '.join(lines)
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', full_text)
        for sentence in sentences:
            if len(sentence.strip()) > 10:
                bullets.append(sentence.strip())
    
    return bullets if bullets else [text]


def _parse_work_experience_blocks(text: str) -> list:
    """Parse working experience into structured blocks.
    
    Handles formats like:
    - 2024-Present  Piping Design / Jr Pipe Stress Engineer, Ranhill Worley, Kuala Lumpur
    - Feb 2024-Present  SEATRIUM / PETROBRAS, DED P82 FPSO, Kuala Lumpur
    - Followed by bullets and role summaries
    """
    # Normalize inline bullets to line-based bullets for easier parsing
    text = text.replace(" •", "\n•")
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]

    header_pattern = re.compile(r"^(?P<position>.+?)\s*\((?P<year>[^)]+)\)\s*$")
    year_range_pattern = re.compile(r"^(?:[A-Za-z]{3}\s+)?\d{4}\s*[-–]\s*(?:Present|\d{4}|[A-Za-z]{3}\s*\d{4})", re.I)
    bullet_re = re.compile(r'^[•\-\*�▪]')

    blocks = []
    current_block = None
    current_roles = []
    mode = None  # None | "projects" | "description"

    def push_block():
        nonlocal current_block, mode, current_roles
        if current_block and (current_block.get("year") or current_block.get("company") or current_block.get("position")):
            # Store accumulated roles as position if we collected any
            if current_roles and not current_block.get("position"):
                current_block["position"] = " | ".join(r for r in current_roles if r)
            # Remove empty description/projects lists
            if not current_block.get("description"):
                current_block.pop("description", None)
            if not current_block.get("projects"):
                current_block.pop("projects", None)
            blocks.append(current_block)
        current_block = {"description": [], "projects": []}
        current_roles = []
        mode = None

    idx = 0
    while idx < len(lines):
        line = lines[idx]

        # Strip leading 'EXPERIENCE' label if present on the line
        if line.upper().startswith("EXPERIENCE"):
            line = line[len("EXPERIENCE"):].strip()

        if not line:
            idx += 1
            continue

        # Labeled fields (Year/Company/Position)
        if line.startswith("Year") and ":" in line:
            push_block()
            current_block["year"] = line.split(":", 1)[1].strip()
            idx += 1
            continue
        if line.startswith("Company") and ":" in line:
            if current_block is None:
                push_block()
            current_block["company"] = line.split(":", 1)[1].strip()
            idx += 1
            continue
        if line.startswith("Position") and ":" in line:
            if current_block is None:
                push_block()
            pos = line.split(":", 1)[1].strip()
            if pos:
                current_roles.append(pos)
            idx += 1
            continue

        # Header style: Position (Date Range)
        header_match = header_pattern.match(line)
        if header_match:
            push_block()
            current_block["position"] = header_match.group("position").strip()
            current_block["year"] = header_match.group("year").strip()
            idx += 1
            continue

        # Year-range line followed by position/company line(s)
        if year_range_pattern.match(line):
            push_block()
            current_block["year"] = line.strip()
            # Look ahead for position/company line
            if idx + 1 < len(lines):
                next_line = lines[idx + 1]
                if not bullet_re.match(next_line) and ":" not in next_line and not year_range_pattern.match(next_line):
                    # Parse "Position/Role, Company, Location" format
                    parts = next_line.split(",", 1)
                    if len(parts) >= 1:
                        pos_part = parts[0].strip()
                        company_part = parts[1].strip() if len(parts) > 1 else ""
                        
                        # Split position on "/" to handle "Role1 / Role2" format
                        roles = [r.strip() for r in pos_part.split("/") if r.strip()]
                        for role in roles:
                            if role:
                                current_roles.append(role)
                        
                        if company_part:
                            current_block["company"] = company_part
                    
                    idx += 2
                    continue
            idx += 1
            continue

        # Section headers or role titles without bullets (e.g., "Jr Pipe Stress Engineer" as standalone)
        if line and not bullet_re.match(line) and ":" not in line and not year_range_pattern.match(line) and current_block and current_block.get("year"):
            # If we have a year but haven't hit bullets yet, this might be a role or company line
            if not current_block.get("company") and line:
                # Could be company name
                current_block["company"] = line
            elif line and not line.startswith("•"):
                # Could be another role/title
                if len(line) < 100:  # Avoid adding long descriptive text as role
                    current_roles.append(line)
            idx += 1
            continue

        lower_line = line.lower()
        if lower_line.startswith("project involved"):
            if current_block is None:
                push_block()
            mode = "projects"
            idx += 1
            continue
        if lower_line.startswith("job description") or lower_line.startswith("scope of work"):
            if current_block is None:
                push_block()
            mode = "description"
            idx += 1
            continue

        # Bullet/indented content
        if bullet_re.match(line):
            if current_block is None:
                push_block()
            clean = re.sub(r'^[•\-\*�▪]\s*', '', line).strip()
            target = "projects" if mode == "projects" else "description"
            current_block.setdefault(target, []).append(clean)
            idx += 1
            continue

        # Fallback: description line
        if current_block is None:
            push_block()
        if line and len(line.strip()) > 0:
            current_block.setdefault("description", []).append(line)
        idx += 1

    # Push final block
    push_block()

    return blocks


def _build_pdf(output_path: str, fields: Dict[str, str], source_text: str, logo_path: str = None, cv_number: str = "KLSB_001") -> None:
    """Generate a branded KLSB-style PDF using ReportLab matching the official format EXACTLY."""
    if not reportlab_available:
        raise RuntimeError("reportlab is required for CV conversion. Please install reportlab==4.2.0 or newer.")
    
    from reportlab.platypus import PageBreak, KeepTogether, Image, Frame, PageTemplate
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
    from reportlab.pdfgen import canvas as pdfcanvas
    import os
    
    # Use provided logo_path or try to find it
    if not logo_path:
        possible_paths = [
            os.path.join(os.path.dirname(output_path), "..", "..", "app", "static", "img", "logo.png"),
            os.path.join(os.path.dirname(__file__), "static", "img", "logo.png"),
        ]
        for p in possible_paths:
            if os.path.exists(p):
                logo_path = os.path.abspath(p)
                break
    
    doc = SimpleDocTemplate(
        output_path, 
        pagesize=letter, 
        topMargin=0.6 * inch, 
        bottomMargin=0.6 * inch,
        leftMargin=0.75 * inch,
        rightMargin=0.75 * inch
    )
    styles = getSampleStyleSheet()

    # Header styles matching KLSB_877 format EXACTLY
    header_style = ParagraphStyle(
        "HeaderStyle",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
        spaceAfter=1,
    )
    
    name_style = ParagraphStyle(
        "NameStyle",
        parent=styles["Normal"],
        fontSize=10,
        fontName="Helvetica-Bold",
        alignment=TA_LEFT,
        spaceAfter=1,
    )
    
    klsb_page_style = ParagraphStyle(
        "KLSBPage",
        parent=styles["Normal"],
        fontSize=9,
        fontName="Helvetica",
        alignment=TA_LEFT,
        spaceAfter=6,
    )
    
    section_title_style = ParagraphStyle(
        "SectionTitle",
        parent=styles["Normal"],
        fontSize=11,
        fontName="Helvetica-Bold",
        textColor=colors.black,
        alignment=TA_LEFT,
        spaceAfter=8,
        spaceBefore=12,
    )
    
    label_style = ParagraphStyle(
        "Label", 
        parent=styles["Normal"], 
        fontSize=9, 
        fontName="Helvetica-Bold",
        leading=13,
        alignment=TA_LEFT,
    )
    
    text_style = ParagraphStyle(
        "Text", 
        parent=styles["Normal"], 
        fontSize=9, 
        leading=13,
        alignment=TA_LEFT,
    )
    
    bullet_style = ParagraphStyle(
        "Bullet", 
        parent=styles["Normal"], 
        fontSize=9, 
        leading=13,
        alignment=TA_LEFT,
        leftIndent=0,
        bulletIndent=0,
    )

    elements = []
    
    # Header: larger logo on left, centered title on right
    header_cells = []
    # Logo cell
    logo_flow = []
    if logo_path and os.path.exists(logo_path):
        try:
            logo_flow.append(Image(logo_path, width=1.9*inch, height=0.65*inch))
        except Exception:
            pass
    header_cells.append([logo_flow])

    # Text cell (centered)
    header_text = [
        Paragraph("PROFESSIONAL RESUME", ParagraphStyle("H1", parent=styles["Normal"], fontSize=16, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=2)),
        Paragraph(fields.get("name", "CANDIDATE NAME").upper(), ParagraphStyle("H2", parent=styles["Normal"], fontSize=14, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=2)),
        Paragraph(cv_number, ParagraphStyle("H3", parent=styles["Normal"], fontSize=12, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=4)),
    ]
    header_cells.append([header_text])

    main_header = Table([header_cells], colWidths=[2.2*inch, 4.8*inch])
    main_header.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("ALIGN", (1, 0), (1, 0), "CENTER"),
        ("ALIGN", (0, 0), (0, 0), "LEFT"),
        ("VALIGN", (0, 0), (0, 0), "MIDDLE"),
    ]))

    elements.append(main_header)
    elements.append(Spacer(1, 0.08 * inch))

    # Personal info as simple lines (no table)
    info_items = [
        ("NAME", fields.get("name", "").upper()),
        ("POSITION", fields.get("position", "").upper()),
        ("DATE OF BIRTH", fields.get("dob", "")),
        ("NATIONALITY", fields.get("nationality", "MALAYSIAN").upper()),
        ("MARITAL STATUS", fields.get("marital_status", "").upper()),
        ("CONTACT ADDRESS", fields.get("address", "")),
        ("", "Tel: " + fields.get("phone", "") if fields.get("phone") else ""),
        ("EMAIL", fields.get("email", "")),
    ]

    for label, value in info_items:
        if not label and not value:
            continue
        line_parts = []
        if label:
            line_parts.append(f"<b>{label}</b>")
            line_parts.append(" : ")
        line_parts.append(value or "")
        elements.append(Paragraph("".join(line_parts), text_style))

    elements.append(Spacer(1, 0.12 * inch))
    
    # Add horizontal separator line like in original
    separator_line = Table([[""]], colWidths=[6.7*inch])
    separator_line.setStyle(TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 0.5, colors.black),
    ]))
    elements.append(separator_line)
    elements.append(Spacer(1, 0.15 * inch))
    
    # Parse and add content sections    # Horizontal line separator
    elements.append(Table([[""]], colWidths=[6.7 * inch], style=TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 1, colors.black),
    ])))
    elements.append(Spacer(1, 0.15 * inch))

    # Parse and add content sections with bullet points
    sections = _parse_cv_sections(source_text)
    
    # Add ACADEMIC/TECHNICAL QUALIFICATIONS if found
    if "qualifications" in sections:
        elements.append(Paragraph("ACADEMIC/TECHNICAL QUALIFICATIONS:", section_title_style))
        elements.append(Spacer(1, 0.05 * inch))
        qual_content = _format_as_bullets(sections["qualifications"])
        for item in qual_content:
            elements.append(item)
        elements.append(Spacer(1, 0.1 * inch))
    
    # Add EXPERIENCE SUMMARY if found
    if "experience_summary" in sections:
        elements.append(Paragraph("EXPERIENCE SUMMARY", section_title_style))
        elements.append(Spacer(1, 0.05 * inch))
        summary_content = _format_summary(sections["experience_summary"], text_style)
        for item in summary_content:
            elements.append(item)
        elements.append(Spacer(1, 0.1 * inch))
    
    # Add WORKING EXPERIENCE if found
    if "working_experience" in sections:
        elements.append(Paragraph("WORKING EXPERIENCE", section_title_style))
        elements.append(Spacer(1, 0.05 * inch))
        work_content = _format_working_experience(sections["working_experience"], bullet_style, text_style)
        for item in work_content:
            elements.append(item)
    
    # Add any remaining content
    if "other" in sections and sections["other"].strip():
        elements.append(Spacer(1, 0.1 * inch))
        elements.append(Paragraph(sections["other"], text_style))

    doc.build(elements)


def _format_as_bullets(text: str) -> list:
    """Format text as bullet points or table format."""
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    
    if not text or not isinstance(text, str):
        return []
    
    styles = getSampleStyleSheet()
    text_style = ParagraphStyle(
        "QualText", 
        parent=styles["Normal"], 
        fontSize=9, 
        leading=13,
    )
    
    elements = []
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    
    # Try to detect table format (Period/Duration and Description)
    if any("Period" in ln or "Duration" in ln for ln in lines[:3]):
        # Format as table
        table_data = []
        i = 0
        while i < len(lines):
            line = lines[i]
            if "Period" in line or "Duration" in line or "Description" in line:
                i += 1
                continue
            # Look for year patterns
            if re.search(r'\d{4}', line):
                period = line
                description = []
                i += 1
                # Collect description lines until next period
                while i < len(lines) and not re.search(r'\d{4}', lines[i]):
                    description.append(lines[i])
                    i += 1
                desc_text = " ".join(description)
                table_data.append([
                    Paragraph(period, text_style),
                    Paragraph(desc_text, text_style)
                ])
            else:
                i += 1
        
        if table_data:
            from reportlab.platypus import Table, TableStyle
            from reportlab.lib import colors
            table = Table(table_data, colWidths=[1.5*inch, 5*inch])
            table.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            elements.append(table)
    else:
        # Format as simple paragraph preserving line breaks
        joined = "<br/>".join(lines) if lines else text
        elements.append(Paragraph(joined, text_style))
    
    return elements


def _format_summary(text: str, text_style) -> list:
    """Format experience summary as plain paragraph (no bullets)."""
    from reportlab.platypus import Paragraph

    if not text or not isinstance(text, str):
        return []

    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return [Paragraph(text, text_style)]

    merged = " ".join(lines)
    return [Paragraph(merged, text_style)]


def _format_working_experience(text: str, bullet_style, text_style) -> list:
    """Format working experience with company entries followed by bullet duties."""
    from reportlab.platypus import Paragraph, Spacer
    from reportlab.lib.units import inch
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    
    if not text or not isinstance(text, str):
        return []
    
    styles = getSampleStyleSheet()
    bold_style = ParagraphStyle(
        "BoldText", 
        parent=styles["Normal"], 
        fontSize=9, 
        fontName="Helvetica-Bold",
        leading=13,
    )
    
    company_style = ParagraphStyle(
        "CompanyStyle", 
        parent=styles["Normal"], 
        fontSize=9, 
        fontName="Helvetica-Bold",
        leading=13,
        spaceAfter=2,
    )
    
    bullet_style_local = ParagraphStyle(
        "BulletLocal", 
        parent=styles["Normal"], 
        fontSize=9, 
        leading=13,
        leftIndent=15,
        bulletIndent=5,
    )
    
    elements = []
    
    # Split by company entries (look for "Year :" patterns)
    company_blocks = []
    current_block = []
    
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    
    for line in lines:
        if line.startswith("Year") and ":" in line:
            if current_block:
                company_blocks.append(current_block)
            current_block = [line]
        else:
            current_block.append(line)
    
    if current_block:
        company_blocks.append(current_block)
    
    # Format each company block (no numbering)
    for block in company_blocks:
        if not block:
            continue

        year_text = None
        company_name = None
        position_text = None
        block_elements = []
        
        i = 0
        while i < len(block):
            line = block[i]
            
            # Check for Year/Company/Position headers
            if line.startswith("Year") and ":" in line:
                year_text = line.split(':', 1)[1].strip() if ':' in line else line
                i += 1
                continue
            if line.startswith("Company") and ":" in line:
                company_name = line.split(':', 1)[1].strip()
                i += 1
                continue
            if line.startswith("Position") and ":" in line:
                position_text = line.split(':', 1)[1].strip()
                i += 1
                continue
            elif line.startswith("Project Involved"):
                block_elements.append(Paragraph("<b>Project Involved:</b>", text_style))
                i += 1
                # Next lines are project names until Job Description or Scope of Work
                while i < len(block) and not block[i].startswith("Job Description") and not block[i].startswith("Scope of Work"):
                    if block[i].strip():
                        block_elements.append(Paragraph(f"• {block[i]}", bullet_style_local))
                    i += 1
            elif line.startswith("Job Description") or line.startswith("Scope of Work"):
                block_elements.append(Paragraph(f"<b>{line}</b>", text_style))
                i += 1
                # Collect all job description lines
                job_desc_lines = []
                while i < len(block):
                    job_desc_lines.append(block[i])
                    i += 1
                
                # Parse job description lines into bullet points
                for desc_line in job_desc_lines:
                    desc_line = desc_line.strip()
                    if not desc_line:
                        continue
                    
                    # Check if line already has bullet
                    if desc_line.startswith('•') or desc_line.startswith('-') or desc_line.startswith('*') or desc_line.startswith('�'):
                        # Remove existing bullet and add our own
                        desc_line = re.sub(r'^[•\-\*�▪]\s*', '', desc_line)
                        block_elements.append(Paragraph(f"• {desc_line}", bullet_style_local))
                    elif len(desc_line) > 5:
                        # Check if it's a continuation of previous point or new point
                        # If starts with lowercase or common continuation words, might be continuation
                        if desc_line[0].islower() or desc_line.startswith(('and ', 'or ', 'with ', 'for ', 'to ')):
                            # Could be continuation, but safer to make it a new bullet
                            block_elements.append(Paragraph(f"• {desc_line}", bullet_style_local))
                        else:
                            # New bullet point
                            block_elements.append(Paragraph(f"• {desc_line}", bullet_style_local))
            else:
                # Regular line
                if line.strip():
                    block_elements.append(Paragraph(line, text_style))
                i += 1

        # Header lines first: Position + Year, then Company
        if position_text or year_text:
            heading_parts = []
            if position_text:
                heading_parts.append(position_text)
            if year_text:
                heading_parts.append(f"({year_text})")
            elements.append(Paragraph(" ".join(heading_parts), company_style))
        if company_name:
            elements.append(Paragraph(company_name, text_style))

        # Then details/bullets
        elements.extend(block_elements)

        # Add spacing between companies
        elements.append(Spacer(1, 0.15 * inch))
    
    return elements


def _parse_cv_sections(text: str) -> Dict[str, str]:
    """Parse CV text into standard sections.
    
    Captures all content and intelligently assigns sections based on headers:
    - EDUCATION/QUALIFICATIONS → qualifications
    - EXPERIENCE SUMMARY → experience_summary
    - EXPERIENCE (with dates/companies) → working_experience
    - EXPERIENCE (descriptive only) → experience_summary
    """
    if not text or not isinstance(text, str):
        return {"other": ""}
    
    sections = {}
    text_upper = text.upper()
    
    # Find all section headers with their positions
    section_markers = []
    
    # Education/Qualifications markers
    for pattern in [r'\bEDUCATION\b', r'\bACADEMIC\s+QUALIFICATIONS?\b', r'\bQUALIFICATIONS?\b', r'\bEDUCATION\s+AND\s+QUALIFICATIONS?\b']:
        for match in re.finditer(pattern, text_upper):
            section_markers.append((match.start(), 'qualifications', match.group()))
    
    # Experience Summary markers (must check before generic EXPERIENCE)
    for pattern in [r'\bEXPERIENCE\s+SUMMARY\b', r'\bPROFESSIONAL\s+SUMMARY\b', r'\bSUMMARY\b']:
        for match in re.finditer(pattern, text_upper):
            section_markers.append((match.start(), 'experience_summary', match.group()))
    
    # Working Experience markers
    for pattern in [r'\bWORKING\s+EXPERIENCE\b', r'\bWORK\s+EXPERIENCE\b', r'\bEMPLOYMENT\s+HISTORY\b', r'\bPROFESSIONAL\s+EXPERIENCE\b']:
        for match in re.finditer(pattern, text_upper):
            section_markers.append((match.start(), 'working_experience', match.group()))
    
    # Generic EXPERIENCE marker (will be analyzed later)
    for match in re.finditer(r'\bEXPERIENCE\b', text_upper):
        # Skip if already marked as a specific experience type
        if not any(marker[0] == match.start() for marker in section_markers):
            section_markers.append((match.start(), 'experience_generic', match.group()))
    
    # Other section markers (Skills, References, etc.)
    for pattern in [r'\bSKILLS?\b', r'\bREFERENCES?\b', r'\bMEMBERSHIPS?\b', r'\bAFFILIATIONS?\b', r'\bTECHNICAL\s+COURSES?\b', r'\bCERTIFICATIONS?\b']:
        for match in re.finditer(pattern, text_upper):
            section_markers.append((match.start(), 'other', match.group()))
    
    # Sort markers by position
    section_markers.sort(key=lambda x: x[0])
    
    # If we have explicit section markers, use them
    if section_markers:
        for i, (start_pos, section_type, header) in enumerate(section_markers):
            try:
                # Find end position (start of next section or end of text)
                end_pos = section_markers[i + 1][0] if i + 1 < len(section_markers) else len(text)
                
                # Extract content (skip the header itself)
                content_start = start_pos + len(header)
                content = text[content_start:end_pos].strip()
                
                if not content:
                    continue
                
                # Handle generic EXPERIENCE - analyze content to determine type
                if section_type == 'experience_generic':
                    # Check if content contains structured work experience entries
                    has_dates = bool(re.search(r'\d{4}\s*[-–]', content))
                    has_company = bool(re.search(r'\b(Sdn\.?\s*Bhd|Ltd\.?|Inc\.?|Corp\.?|Company|Engineer|Manager|Officer|Technician|Analyst|Developer)\b', content, re.I))
                    
                    if has_dates and has_company:
                        section_type = 'working_experience'
                    else:
                        section_type = 'experience_summary'
                
                # Merge content if section already exists, otherwise set it
                if section_type in sections and section_type != 'other':
                    sections[section_type] += "\n\n" + content
                elif section_type == 'other':
                    # Accumulate "other" content
                    sections.setdefault('other', '')
                    sections['other'] += "\n\n" + content if sections['other'] else content
                else:
                    sections[section_type] = content
            except Exception:
                # Skip problematic sections but continue processing
                continue
    else:
        # No explicit headers - classify all content intelligently
        sections = _classify_unlabeled_content(text)
    
    # If no sections found, put everything in "other"
    if not sections:
        sections["other"] = text
    
    return sections


def _classify_unlabeled_content(text: str) -> Dict[str, str]:
    """Classify content without explicit section headers based on keywords and patterns."""
    sections = {
        "qualifications": "",
        "experience_summary": "",
        "working_experience": "",
        "other": ""
    }
    
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    
    # Education keywords
    education_keywords = r'\b(University|Universiti|College|Diploma|Bachelor|Master|Degree|PhD|GPA|Cumulative|Coursework|Institute|School|Certificate)\b'
    
    # Work experience indicators (dates with companies/positions)
    work_indicators = r'\d{4}\s*[-–]\s*(?:Present|\d{4})'
    
    # Summary indicators (skills description without dates)
    summary_indicators = r'\b(Skilled|Proficient|Bringing|Holds|Experienced)\b'
    
    current_section = None
    current_block = []
    
    for line in lines:
        line_has_date = bool(re.search(r'\d{4}\s*[-–]', line))
        
        # Check for education content
        if re.search(education_keywords, line, re.I) and not line_has_date:
            if current_block and current_section:
                sections[current_section] += "\n".join(current_block) + "\n\n"
            current_section = "qualifications"
            current_block = [line]
        # Check for work experience (dates + roles/companies)
        elif line_has_date:
            if current_block and current_section:
                sections[current_section] += "\n".join(current_block) + "\n\n"
            current_section = "working_experience"
            current_block = [line]
        # Check for summary content (descriptive without dates)
        elif re.search(summary_indicators, line, re.I) and not current_section:
            if current_block and current_section:
                sections[current_section] += "\n".join(current_block) + "\n\n"
            current_section = "experience_summary"
            current_block = [line]
        # Continuation of current section
        elif current_section:
            current_block.append(line)
        # Default to other
        else:
            if current_block and current_section:
                sections[current_section] += "\n".join(current_block) + "\n\n"
            current_section = "other"
            current_block = [line]
    
    # Add final block
    if current_block and current_section:
        sections[current_section] += "\n".join(current_block)
    
    # Clean up empty sections
    return {k: v.strip() for k, v in sections.items() if v.strip()}


def convert_cv_to_klsb_ocr(source_path: str, output_dir: str, overrides: Optional[Dict[str, str]] = None, output_format: str = "docx") -> Tuple[str, Dict[str, str]]:
    """Convert a CV into KLSB_877 format using text extraction + OCR fallback.
    
    Args:
        source_path: Path to source CV file
        output_dir: Directory to save converted file
        overrides: Optional field overrides
        output_format: Output format - "docx" (Word) or "pdf" (default: docx)

    Returns: (output_path, detected_fields)
    """
    import time
    
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source CV not found: {source_path}")

    text = _extract_text_from_pdf(source_path)
    fields = _guess_fields(text)

    overrides = overrides or {}
    for key, val in overrides.items():
        if val:
            fields[key] = val

    os.makedirs(output_dir, exist_ok=True)
    slug = slugify_filename(fields.get("name"))
    
    # Get next CV number
    cv_number = _get_next_cv_number(output_dir)
    
    # Determine output format
    if output_format.lower() == "docx":
        output_name = f"{cv_number}_{slug}.docx"
        output_path = os.path.join(output_dir, output_name)
        
        # Check if file is locked and try alternative name
        if os.path.exists(output_path):
            try:
                # Try to delete existing file
                os.remove(output_path)
            except PermissionError:
                # File is locked (open in Word/viewer), use timestamped name
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                output_name = f"{cv_number}_{slug}_{timestamp}.docx"
                output_path = os.path.join(output_dir, output_name)
        
        # Get logo path - use the main logo.png file
        logo_path = os.path.join(os.path.dirname(__file__), "static", "img", "logo.png")
        _build_docx(output_path, fields, text, logo_path, cv_number)
    else:
        output_name = f"{cv_number}_{slug}.pdf"
        output_path = os.path.join(output_dir, output_name)
        
        # Check if file is locked and try alternative name
        if os.path.exists(output_path):
            try:
                # Try to delete existing file
                os.remove(output_path)
            except PermissionError:
                # File is locked (open in PDF viewer), use timestamped name
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                output_name = f"{cv_number}_{slug}_{timestamp}.pdf"
                output_path = os.path.join(output_dir, output_name)
        
        logo_path = os.path.join(os.path.dirname(__file__), "static", "img", "logo.png")
        _build_pdf(output_path, fields, text, logo_path, cv_number)
    
    return output_path, fields

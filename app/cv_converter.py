import os
import re
from pathlib import Path
from typing import Dict, Tuple, Optional

# Optional dependencies
try:  # Lightweight text extraction for text-based PDFs
    from pypdf import PdfReader
except Exception:  # pragma: no cover - optional
    PdfReader = None

try:  # OCR fallback (requires poppler + tesseract installed on the system)
    from pdf2image import convert_from_path
    import pytesseract
except Exception:  # pragma: no cover - optional
    convert_from_path = None
    pytesseract = None

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


def _extract_text_from_pdf(path: str) -> str:
    """Extract text from a PDF using pypdf, fallback to OCR when needed."""
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


def _build_pdf(output_path: str, fields: Dict[str, str], source_text: str) -> None:
    """Generate a branded KLSB_877-style PDF using ReportLab matching the official format EXACTLY."""
    if not reportlab_available:
        raise RuntimeError("reportlab is required for CV conversion. Please install reportlab==4.2.0 or newer.")
    
    from reportlab.platypus import PageBreak, KeepTogether, Image, Frame, PageTemplate
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY, TA_RIGHT
    from reportlab.pdfgen import canvas as pdfcanvas
    import os
    
    # Try to find logo
    logo_path = None
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
        fontSize=9,
        fontName="Helvetica-Bold",
        textColor=colors.black,
        alignment=TA_LEFT,
        spaceAfter=6,
        spaceBefore=10,
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
    
    # Page header with logo on left, info on right
    header_data = []
    
    # Left side - Logo and title
    left_content = []
    if logo_path and os.path.exists(logo_path):
        try:
            img = Image(logo_path, width=1.2*inch, height=0.4*inch)
            left_content.append(img)
        except:
            pass
    left_content.append(Paragraph("PROFESSIONAL RESUME", header_style))
    left_content.append(Paragraph(fields.get("name", "CANDIDATE NAME").upper(), name_style))
    left_content.append(Paragraph("KLSB_877", klsb_page_style))
    
    # Create a nested table for left content
    left_table = Table([[item] for item in left_content], colWidths=[3*inch])
    left_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    
    # Right side - Personal info box
    info_data = [
        [Paragraph("<b>NAME</b>", label_style), Paragraph(": " + fields.get("name", "").upper(), text_style)],
        [Paragraph("", label_style), Paragraph("", text_style)],  # spacing
        [Paragraph("<b>POSITION</b>", label_style), Paragraph(": " + fields.get("position", "").upper(), text_style)],
        [Paragraph("", label_style), Paragraph("", text_style)],
        [Paragraph("<b>DATE OF BIRTH</b>", label_style), Paragraph(": " + fields.get("dob", ""), text_style)],
        [Paragraph("", label_style), Paragraph("", text_style)],
        [Paragraph("<b>NATIONALITY</b>", label_style), Paragraph(": " + fields.get("nationality", "MALAYSIAN").upper(), text_style)],
        [Paragraph("", label_style), Paragraph("", text_style)],
        [Paragraph("<b>MARITAL STATUS</b>", label_style), Paragraph(": " + fields.get("marital_status", "").upper(), text_style)],
        [Paragraph("", label_style), Paragraph("", text_style)],
        [Paragraph("<b>CONTACT ADDRESS</b>", label_style), Paragraph(": " + fields.get("address", ""), text_style)],
    ]
    
    # Add phone and email if available
    if fields.get("phone"):
        info_data.append([Paragraph("", label_style), Paragraph("Tel: " + fields.get("phone", ""), text_style)])
    if fields.get("email"):
        info_data.append([Paragraph("", label_style), Paragraph("Email: " + fields.get("email", ""), text_style)])
    
    info_table = Table(info_data, colWidths=[1.5 * inch, 2.2 * inch])
    info_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ("TOPPADDING", (0, 0), (-1, -1), 1),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
    ]))
    
    # Combine left and right in header table
    header_table = Table([[left_table, info_table]], colWidths=[3*inch, 3.7*inch])
    header_table.setStyle(TableStyle([
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 0),
        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
    ]))
    
    elements.append(header_table)
    elements.append(Spacer(1, 0.15 * inch))
    
    # Horizontal line separator
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
        # Format as simple paragraph
        elements.append(Paragraph(text, text_style))
    
    return elements


def _format_summary(text: str, text_style) -> list:
    """Format experience summary as bullet points for easier reading."""
    from reportlab.platypus import Paragraph
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    
    styles = getSampleStyleSheet()
    bullet_style = ParagraphStyle(
        "SummaryBullet", 
        parent=styles["Normal"], 
        fontSize=9, 
        leading=13,
        leftIndent=15,
        bulletIndent=5,
    )
    
    elements = []
    
    # Clean up text - preserve line breaks and bullets
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    
    # Check if text already has bullets
    has_bullets = any(ln.startswith('•') or ln.startswith('-') or ln.startswith('*') for ln in lines)
    
    if has_bullets:
        # Extract existing bullet points
        for line in lines:
            line = line.strip()
            if not line:
                continue
            # Remove existing bullet markers
            line = re.sub(r'^[•\-\*�▪]\s*', '', line)
            if len(line) > 5:  # Skip very short lines
                elements.append(Paragraph(f"• {line}", bullet_style))
    else:
        # Try to intelligently break into bullet points
        full_text = ' '.join(lines)
        
        # Split by sentence patterns
        sentences = re.split(r'(?<=[.!?])\s+(?=[A-Z])', full_text)
        
        # Also try to split by common transition words
        key_phrases = [
            'Having substantial knowledge',
            'Involve in', 'Involved in',
            'Which involved', 
            'Responsible for',
            'Proficient in',
            'Experience in',
            'Skilled in',
            'Expertise in'
        ]
        
        bullet_points = []
        
        # Check if we have clear sentence structure
        if len(sentences) >= 2:
            for sentence in sentences:
                sentence = sentence.strip()
                if sentence and len(sentence) > 15:
                    # Check if sentence contains multiple ideas that should be split
                    for phrase in key_phrases:
                        if phrase.lower() in sentence.lower():
                            # Split at this phrase
                            parts = re.split(f'({phrase})', sentence, flags=re.IGNORECASE, maxsplit=1)
                            if len(parts) == 3:
                                if parts[0].strip() and len(parts[0].strip()) > 15:
                                    bullet_points.append(parts[0].strip())
                                combined = parts[1] + parts[2]
                                if combined.strip() and len(combined.strip()) > 15:
                                    bullet_points.append(combined.strip())
                                sentence = ''
                                break
                    
                    if sentence:  # Still have content
                        bullet_points.append(sentence)
        else:
            # Single long paragraph - split by key phrases
            remaining = full_text
            for phrase in key_phrases:
                pattern = f'({phrase}[^.!?]*[.!?])'
                matches = re.findall(pattern, remaining, flags=re.IGNORECASE)
                for match in matches:
                    if len(match.strip()) > 15:
                        bullet_points.append(match.strip())
                        remaining = remaining.replace(match, '', 1)
            
            # Add any remaining text
            if remaining.strip() and len(remaining.strip()) > 15:
                bullet_points.append(remaining.strip())
        
        # Format as bullets
        for point in bullet_points:
            point = point.strip()
            if point and len(point) > 10:
                # Ensure first letter is capitalized
                point = point[0].upper() + point[1:] if len(point) > 1 else point.upper()
                # Remove trailing punctuation if needed, then ensure it ends properly
                point = point.rstrip()
                if not point[-1] in '.!?':
                    point += '.'
                elements.append(Paragraph(f"• {point}", bullet_style))
    
    # If we couldn't extract any bullets, use the original text as single paragraph
    if not elements:
        clean_text = re.sub(r'\s+', ' ', text.strip())
        elements.append(Paragraph(clean_text, text_style))
    
    return elements


def _format_working_experience(text: str, bullet_style, text_style) -> list:
    """Format working experience with numbered companies and bullet points."""
    from reportlab.platypus import Paragraph, Spacer
    from reportlab.lib.units import inch
    from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
    
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
        spaceAfter=3,
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
    
    # Format each company block with numbering
    for idx, block in enumerate(company_blocks, start=1):
        if not block:
            continue
            
        # Add company number
        elements.append(Paragraph(f"<b>{idx}.</b>", company_style))
        
        i = 0
        while i < len(block):
            line = block[i]
            
            # Check for Year/Company/Position headers
            if line.startswith("Year") and ":" in line:
                year_text = line.split(':', 1)[1].strip() if ':' in line else line
                elements.append(Paragraph(f"<b>Year:</b> {year_text}", text_style))
                i += 1
            elif line.startswith("Company") and ":" in line:
                company_name = line.split(':', 1)[1].strip()
                elements.append(Paragraph(f"<b>Company:</b> {company_name}", text_style))
                i += 1
            elif line.startswith("Position") and ":" in line:
                position_name = line.split(':', 1)[1].strip()
                elements.append(Paragraph(f"<b>Position:</b> {position_name}", text_style))
                elements.append(Spacer(1, 0.05 * inch))
                i += 1
            elif line.startswith("Project Involved"):
                elements.append(Paragraph("<b>Project Involved:</b>", text_style))
                i += 1
                # Next lines are project names until Job Description or Scope of Work
                while i < len(block) and not block[i].startswith("Job Description") and not block[i].startswith("Scope of Work"):
                    if block[i].strip():
                        elements.append(Paragraph(f"• {block[i]}", bullet_style_local))
                    i += 1
            elif line.startswith("Job Description") or line.startswith("Scope of Work"):
                elements.append(Paragraph(f"<b>{line}</b>", text_style))
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
                        elements.append(Paragraph(f"• {desc_line}", bullet_style_local))
                    elif len(desc_line) > 5:
                        # Check if it's a continuation of previous point or new point
                        # If starts with lowercase or common continuation words, might be continuation
                        if desc_line[0].islower() or desc_line.startswith(('and ', 'or ', 'with ', 'for ', 'to ')):
                            # Could be continuation, but safer to make it a new bullet
                            elements.append(Paragraph(f"• {desc_line}", bullet_style_local))
                        else:
                            # New bullet point
                            elements.append(Paragraph(f"• {desc_line}", bullet_style_local))
            else:
                # Regular line
                if line.strip():
                    elements.append(Paragraph(line, text_style))
                i += 1
        
        # Add spacing between companies
        elements.append(Spacer(1, 0.15 * inch))
    
    return elements


def _parse_cv_sections(text: str) -> Dict[str, str]:
    """Parse CV text into standard sections."""
    sections = {}
    
    # Try to find qualifications section
    qual_patterns = [
        r"ACADEMIC.*?QUALIFICATIONS?:?\s*(.*?)(?=EXPERIENCE|WORKING|EMPLOYMENT|$)",
        r"EDUCATION:?\s*(.*?)(?=EXPERIENCE|WORKING|EMPLOYMENT|$)",
        r"QUALIFICATIONS?:?\s*(.*?)(?=EXPERIENCE|WORKING|EMPLOYMENT|$)",
    ]
    
    for pattern in qual_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            sections["qualifications"] = match.group(1).strip()
            break
    
    # Try to find experience summary
    summary_patterns = [
        r"EXPERIENCE\s+SUMMARY:?\s*(.*?)(?=WORKING EXPERIENCE|EMPLOYMENT HISTORY|ACADEMIC|$)",
        r"PROFESSIONAL\s+SUMMARY:?\s*(.*?)(?=WORKING EXPERIENCE|EMPLOYMENT HISTORY|ACADEMIC|$)",
        r"SUMMARY:?\s*(.*?)(?=WORKING EXPERIENCE|EMPLOYMENT HISTORY|ACADEMIC|$)",
    ]
    
    for pattern in summary_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            sections["experience_summary"] = match.group(1).strip()
            break
    
    # Try to find working experience
    work_patterns = [
        r"WORKING EXPERIENCE:?\s*(.*?)(?=SKILLS|REFERENCES|$)",
        r"EMPLOYMENT HISTORY:?\s*(.*?)(?=SKILLS|REFERENCES|$)",
        r"PROFESSIONAL EXPERIENCE:?\s*(.*?)(?=SKILLS|REFERENCES|$)",
    ]
    
    for pattern in work_patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            sections["working_experience"] = match.group(1).strip()
            break
    
    # If no sections found, put everything in "other"
    if not sections:
        sections["other"] = text
    
    return sections


def convert_cv_to_klsb_ocr(source_path: str, output_dir: str, overrides: Optional[Dict[str, str]] = None) -> Tuple[str, Dict[str, str]]:
    """Convert a CV into KLSB_877 format using text extraction + OCR fallback.

    Returns: (output_path, detected_fields)
    """
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
    output_name = f"KLSB_877_{slug}.pdf"
    output_path = os.path.join(output_dir, output_name)

    _build_pdf(output_path, fields, text)
    return output_path, fields

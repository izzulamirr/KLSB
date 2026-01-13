import os
import re
import base64
from pathlib import Path
from typing import Dict, Tuple, Optional

# Optional imports for external libraries
try:
    from openai import OpenAI
except Exception:
    OpenAI = None

try:
    from pdf2image import convert_from_path
except Exception:
    convert_from_path = None

# Optional availability flags
docx_available = True
reportlab_available = True

try:
    from docx import Document
    from docx.shared import Pt, Inches
    from docx.oxml.ns import qn
    from docx.enum.text import WD_ALIGN_PARAGRAPH
except Exception:
    docx_available = False

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
except Exception:
    reportlab_available = False


def slugify_filename(name: str) -> str:
    """Convert CV name to slug format for filenames."""
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



def _get_poppler_path() -> Optional[str]:
    """Return poppler_path for pdf2image, auto-detecting common Windows locations."""
    # Check environment variable first
    env_path = os.environ.get("POPPLER_PATH")
    if env_path and os.path.exists(env_path):
        return env_path
    
    # Common Windows installation paths
    common_paths = [
        r"C:\poppler\poppler-24.08.0\Library\bin",
        r"C:\Program Files\poppler\Library\bin",
        r"C:\Program Files (x86)\poppler\Library\bin",
        r"C:\ProgramData\chocolatey\lib\poppler\tools\Library\bin",
        r"C:\tools\poppler\Library\bin",
    ]
    
    # Also check for versioned directories
    if os.path.exists(r"C:\Program Files"):
        import glob
        for pattern in [r"C:\Program Files\poppler-*\Library\bin", r"C:\ProgramData\chocolatey\lib\poppler\tools\poppler-*\Library\bin"]:
            matches = glob.glob(pattern)
            if matches:
                common_paths.extend(matches)
    
    for path in common_paths:
        if os.path.exists(path) and os.path.exists(os.path.join(path, "pdftoppm.exe")):
            return path
    
    return None


def _extract_text_with_chatgpt(path: str, api_key: str = None) -> str:
    """Extract text from PDF using ChatGPT Vision API and return structured CV data."""
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
        images = convert_from_path(path, dpi=200, first_page=1, last_page=3, poppler_path=_get_poppler_path())
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
                    model="gpt-4.1",
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


def _extract_cv_with_chatgpt(path: str, api_key: str = None) -> Dict[str, str]:
    """Extract and parse a CV using ChatGPT Vision in one pass, returning structured fields."""
    if not OpenAI:
        raise RuntimeError("OpenAI library not installed. Run: pip install openai")

    # Resolve API key
    if not api_key:
        try:
            from config import BaseConfig
            api_key = BaseConfig.OPENAI_API_KEY
        except Exception:
            pass
    api_key = api_key or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OpenAI API key not configured. Set in config.py or OPENAI_API_KEY env var.")

    if not convert_from_path:
        raise RuntimeError("pdf2image not installed. Run: pip install pdf2image")

    client = OpenAI(api_key=api_key)

    # Track token usage
    total_input_tokens = 0
    total_output_tokens = 0

    # Render first pages to images for Vision
    poppler_path = _get_poppler_path()
    try:
        images = convert_from_path(path, dpi=200, first_page=1, last_page=3, poppler_path=poppler_path)
    except Exception as e:
        error_msg = f"pdf2image/Poppler error: {str(e)}."
        if not poppler_path:
            error_msg += " Poppler not found. Install with: choco install poppler (admin PowerShell), then restart Flask."
        raise RuntimeError(error_msg)

    # Extract raw text from images
    all_text = []
    for img in images:
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
            img.save(tmp.name, "PNG")
            tmp_path = tmp.name
        try:
            with open(tmp_path, "rb") as img_file:
                img_data = base64.b64encode(img_file.read()).decode("utf-8")

            resp = client.chat.completions.create(
                model="gpt-4.1",
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": "Extract the text from this CV page. Return ONLY the raw text content without any markdown formatting, without bold markers (**), without explanations or commentary. Preserve section headers, bullet points, dates, and line breaks."},
                            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_data}"}},
                        ],
                    }
                ],
                max_tokens=500,
            )
            # Track token usage
            if hasattr(resp, 'usage'):
                total_input_tokens += resp.usage.prompt_tokens
                total_output_tokens += resp.usage.completion_tokens
            # Clean up the extracted text
            extracted = resp.choices[0].message.content
            # Remove markdown bold markers
            extracted = re.sub(r'\*\*([^*]+)\*\*', r'\1', extracted)
            # Remove any conversational phrases
            extracted = re.sub(r'Certainly!.*?shown:', '', extracted, flags=re.DOTALL | re.IGNORECASE)
            extracted = re.sub(r'Here is .*?:', '', extracted, flags=re.IGNORECASE)
            all_text.append(extracted.strip())
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

    combined_text = "\n\n".join(all_text)
    
    # Additional cleanup of combined text
    combined_text = re.sub(r'\*\*([^*]+)\*\*', r'\1', combined_text)  # Remove ** markers
    combined_text = re.sub(r'--+', '', combined_text)  # Remove separator lines
    combined_text = re.sub(r'Certainly!.*?shown:', '', combined_text, flags=re.DOTALL | re.IGNORECASE)

    # Ask ChatGPT to extract raw data (Python will format it locally)
    try:
        parse_resp = client.chat.completions.create(
            model="gpt-4.1",
            messages=[
                {
                    "role": "user",
                    "content": f"""Extract data from this CV. Return ONLY valid JSON (no markdown, no backticks, no code blocks).

Extract these fields:
- name: Full name
- position: Current or desired job title
- dob: Date of birth
- nationality: Nationality
- marital_status: Marital status
- address: Full address
- phone: Phone number
- email: Email address
- linkedin: LinkedIn URL if present
- experience_summary: Professional summary/profile text (paragraph form)
- education: List of education entries (each object: {{year_from, year_to, degree, institution}})
- work_history: List of work experience (each object: {{year_from, year_to, company, position, projects: [list], responsibilities: [list]}})
- skills: List of technical skills
- professional_training: List of professional trainings/certifications
- computer_skills: List of computer skills
- professional_memberships: List of memberships (each: {{organization: "name", membership_level: "level"}}, e.g. BEM, MBOT)
- involvements: List of activities/organizations
- references: Reference information

Return ONLY this JSON structure:
{{
  "name": "...",
  "position": "...",
  "dob": "...",
  "nationality": "...",
  "marital_status": "...",
  "address": "...",
  "phone": "...",
  "email": "...",
  "linkedin": "...",
  "experience_summary": "...",
  "education": [
    {{"year_from": "2020", "year_to": "2024", "degree": "Bachelor of Engineering", "institution": "University"}}
  ],
  "work_history": [
    {{
      "year_from": "2023",
      "year_to": "Present",
      "company": "Company Name",
      "position": "Job Title",
      "projects": ["Project 1", "Project 2"],
      "responsibilities": ["Task 1", "Task 2"]
    }}
  ],
  "skills": ["Skill 1", "Skill 2"],
  "professional_training": ["Training 1", "Certification 1"],
  "computer_skills": ["AutoCAD", "Excel"],
  "professional_memberships": [
    {{"organization": "BEM", "membership_level": "Member"}},
    {{"organization": "MBOT", "membership_level": "Technologist"}}
  ],
  "involvements": ["Activity 1", "Activity 2"],
  "references": "Reference details"
}}

CV TEXT:
{combined_text}
""",
                }
            ],
            temperature=0.1,
            max_tokens=2500,
            response_format={"type": "json_object"}
        )

        # Track token usage
        if hasattr(parse_resp, 'usage'):
            total_input_tokens += parse_resp.usage.prompt_tokens
            total_output_tokens += parse_resp.usage.completion_tokens

        response_text = parse_resp.choices[0].message.content or "{}"
        
        import json
        
        def aggressive_json_fix(text):
            """Aggressively fix JSON by escaping all internal newlines and problematic characters."""
            # Extract JSON object
            start = text.find('{')
            end = text.rfind('}')
            if start < 0 or end <= start:
                return text
            
            json_str = text[start:end+1]
            
            # Split by field boundaries
            result = []
            in_string = False
            escape_next = False
            
            for char in json_str:
                if escape_next:
                    result.append(char)
                    escape_next = False
                elif char == '\\':
                    result.append(char)
                    escape_next = True
                elif char == '"':
                    result.append(char)
                    in_string = not in_string
                elif in_string and char in '\n\r':
                    # Escape newlines in strings
                    if char == '\n':
                        result.append('\\n')
                    elif char == '\r':
                        result.append('\\r')
                else:
                    result.append(char)
            
            return ''.join(result)
        
        try:
            # Try direct parsing
            data = json.loads(response_text)
        except json.JSONDecodeError:
            # Apply aggressive fix
            fixed = aggressive_json_fix(response_text)
            try:
                data = json.loads(fixed)
            except json.JSONDecodeError as e:
                # Last resort: extract just the JSON fields manually
                try:
                    import ast
                    # Try to evaluate as Python dict if all else fails
                    fixed2 = fixed.replace('true', 'True').replace('false', 'False').replace('null', 'None')
                    data = ast.literal_eval(fixed2)
                    # Convert back from Python to JSON-safe dict
                    data = {k: (v if not isinstance(v, bool) else v) for k, v in data.items()}
                except:
                    raise RuntimeError(f"Unable to parse ChatGPT response: {str(e)}")
        
        data.setdefault("name", "Candidate")
        data.setdefault("nationality", "MALAYSIAN")
        # Include the full extracted text so downstream consumers can use all content
        data["full_text"] = combined_text
        
        # === LOCAL PYTHON PARSING: Format raw data into KLSB structure ===
        
        # Format education from list to KLSB string
        if 'education' in data and isinstance(data['education'], list):
            data['education'] = _format_education_klsb(data['education'])
        
        # Format work_history from list to KLSB string
        if 'work_history' in data and isinstance(data['work_history'], list):
            data['working_experience'] = _format_work_experience_klsb(data['work_history'])
            # Remove work_history key, keep working_experience for template
            data.pop('work_history', None)
        
        # Format skills from list to KLSB string with bullets
        if 'skills' in data and isinstance(data['skills'], list):
            data['skills'] = _format_skills_klsb(data['skills'])
        
        # Format new fields with bullets
        if 'professional_training' in data and isinstance(data['professional_training'], list):
            data['professional_training'] = _format_list_klsb(data['professional_training'])
        
        if 'computer_skills' in data and isinstance(data['computer_skills'], list):
            data['computer_skills'] = _format_list_klsb(data['computer_skills'])
        
        if 'professional_memberships' in data:
            if isinstance(data['professional_memberships'], list):
                data['professional_memberships'] = _format_professional_memberships_klsb(data['professional_memberships'])
        
        # Format involvements from list to KLSB string with bullets
        if 'involvements' in data and isinstance(data['involvements'], list):
            data['involvements'] = _format_involvements_klsb(data['involvements'])
        
        # Ensure name is uppercase
        if 'name' in data:
            data['name'] = str(data['name']).upper()
        
        # Ensure position is uppercase
        if 'position' in data:
            data['position'] = str(data['position']).upper()
        
        # Add token usage to data
        data['_token_usage'] = {
            'input_tokens': total_input_tokens,
            'output_tokens': total_output_tokens,
            'total_tokens': total_input_tokens + total_output_tokens
        }
        
        return data
    except Exception as e:
        raise RuntimeError(f"ChatGPT parsing failed: {str(e)}")


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
            images = convert_from_path(path, dpi=200, first_page=1, last_page=2, poppler_path=_get_poppler_path())
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


def _format_education_klsb(education_list):
    """Format education list into KLSB structure."""
    if not education_list:
        return ""
    
    formatted = []
    for edu in education_list:
        if isinstance(edu, dict):
            # Handle both 'year' and 'year_from'/'year_to' formats
            year = edu.get('year', '')
            if not year:
                year_from = edu.get('year_from', '')
                year_to = edu.get('year_to', '')
                if year_from and year_to:
                    year = f"{year_from} – {year_to}"
                elif year_from:
                    year = year_from
                elif year_to:
                    year = year_to
            
            degree = edu.get('degree', '')
            institution = edu.get('institution', '')
            
            # Format: Year – Year\nDegree\nInstitution
            parts = []
            if year:
                parts.append(year.replace('-', ' – '))
            if degree:
                parts.append(degree)
            if institution:
                parts.append(institution)
            
            if parts:
                formatted.append('\n'.join(parts))
        elif isinstance(edu, str):
            formatted.append(edu)
    
    return '\n'.join(formatted)


def _format_work_experience_klsb(work_history):
    """Format work history into KLSB structure."""
    if not work_history:
        return ""
    
    formatted = []
    for job in work_history:
        if not isinstance(job, dict):
            continue
        
        job_parts = []
        
        # Year : value (handle both 'year' and 'year_from'/'year_to')
        year_str = ""
        if job.get('year'):
            year_str = job['year']
        elif job.get('year_from') or job.get('year_to'):
            year_from = job.get('year_from', '')
            year_to = job.get('year_to', '')
            if year_from and year_to:
                year_str = f"{year_from} - {year_to}"
            elif year_from:
                year_str = year_from
            elif year_to:
                year_str = year_to
        
        if year_str:
            job_parts.append(f"Year : {year_str}")
        
        # Company : value
        if job.get('company'):
            job_parts.append(f"Company : {job['company']}")
        
        # Position : value
        if job.get('position'):
            job_parts.append(f"Position : {job['position']}")
        
        # Project Involved:
        projects = job.get('projects', [])
        if projects:
            job_parts.append("")
            job_parts.append("Project Involved:")
            for proj in projects:
                job_parts.append(f"• {proj}")
        
        # Job Description:
        responsibilities = job.get('responsibilities', [])
        if responsibilities:
            job_parts.append("")
            job_parts.append("Job Description:")
            for resp in responsibilities:
                job_parts.append(f"• {resp}")
        
        if job_parts:
            formatted.append('\n'.join(job_parts))
    
    return '\n\n'.join(formatted)


def _format_skills_klsb(skills_list):
    """Format skills list into KLSB structure with bullets."""
    if not skills_list:
        return ""
    
    formatted = []
    for skill in skills_list:
        skill_str = str(skill).strip()
        if skill_str:
            # Remove existing bullets if any
            skill_str = re.sub(r'^[•\-\*]\s*', '', skill_str)
            formatted.append(f"• {skill_str}")
    
    return '\n'.join(formatted)


def _format_involvements_klsb(involvements_list):
    """Format involvements list into KLSB structure with bullets."""
    if not involvements_list:
        return ""
    
    formatted = []
    for item in involvements_list:
        item_str = str(item).strip()
        if item_str:
            # Add bullet if not present
            if not item_str.startswith('•'):
                item_str = f"• {item_str}"
            formatted.append(item_str)
    
    return '\n'.join(formatted)


def _format_professional_memberships_klsb(memberships_list):
    """Format professional memberships into KLSB structure."""
    if not memberships_list:
        return ""
    
    formatted = []
    for item in memberships_list:
        if isinstance(item, dict):
            org = item.get('organization', '')
            level = item.get('membership_level', '')
            if org:
                text = f"• {org}"
                if level:
                    text += f": {level}"
                formatted.append(text)
        elif isinstance(item, str):
            item_str = str(item).strip()
            if item_str:
                if not item_str.startswith('•'):
                    item_str = f"• {item_str}"
                formatted.append(item_str)
    
    return '\n'.join(formatted)


def _format_list_klsb(items_list):
    """Format generic list with bullets."""
    if not items_list:
        return ""
    
    formatted = []
    for item in items_list:
        item_str = str(item).strip()
        if item_str:
            if not item_str.startswith('•'):
                item_str = f"• {item_str}"
            formatted.append(item_str)
    
    return '\n'.join(formatted)


def _guess_fields(text: str) -> Dict[str, str]:
    """Heuristic extraction of common CV fields matching KLSB_877 format."""
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    joined = "\n".join(lines)

    # Email detection
    email_match = re.search(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", joined)

    # LinkedIn detection
    linkedin = ""
    ln_match = re.search(r"LinkedIn\s*:\s*(.+)|https?://(?:www\.)?linkedin\.com/\S+", joined, re.I)
    if ln_match:
        # If matched with label, take the captured group; else take full match
        val = ln_match.group(1) if ln_match.lastindex else ln_match.group(0)
        linkedin = val.strip()
    
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
        # Try the line immediately following the detected name
        if name:
            try:
                idx = lines.index(name)
                if idx + 1 < len(lines):
                    next_ln = lines[idx + 1]
                    if re.search(r"engineer|designer|manager|developer", next_ln, re.I):
                        position = next_ln.strip()
            except ValueError:
                pass
        # Fallback: look near the top for job titles
        if not position:
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
    
    # Address extraction - improved to stop at Tel or Email and handle 'Address:' prefix
    address = ""
    addr_match = re.search(r"(?:CONTACT )?ADDRESS\s*:\s*(.+?)(?=\nTel:|\nPhone:|\nEmail:|NATIONALITY|ACADEMIC|EXPERIENCE|$)", joined, re.I | re.DOTALL)
    if not addr_match:
        addr_match = re.search(r"Address\s*:\s*(.+?)(?=\nPhone:|\nEmail:|$)", joined, re.I | re.DOTALL)
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
        "linkedin": linkedin,
    }


def _parse_cv_sections(text: str) -> Dict[str, str]:
    """Extract all sections from CV text for traditional OCR path.
    
    Combines basic field extraction with education/experience sections.
    Returns dict matching ChatGPT output format for consistency.
    """
    # Get basic fields
    fields = _guess_fields(text)
    
    # Extract education section - more flexible lookahead
    education = ""
    edu_match = re.search(
        r"(?:ACADEMIC QUALIFICATIONS?|EDUCATION|QUALIFICATION)\s*:?\s*(.+?)(?=\n(?:EXPERIENCE SUMMARY|PROFESSIONAL SUMMARY|SUMMARY|EMPLOYMENT|PROFESSIONAL EXPERIENCE|WORKING EXPERIENCE|WORKING|SKILLS|LANGUAGE|REFERENCES?|UNIVERSITY PROJECTS|INVOLVEMENTS|OTHERS|$))",
        text,
        re.I | re.DOTALL
    )
    if edu_match:
        education = edu_match.group(1).strip()
    
    # Extract experience summary/professional summary
    experience_summary = ""
    exp_sum_match = re.search(
        r"(?:PROFESSIONAL SUMMARY|EXPERIENCE SUMMARY|PROFILE SUMMARY|SUMMARY)\s*:?\s*(.+?)(?=\n(?:EDUCATION|EMPLOYMENT|WORKING|EXPERIENCE|SKILLS|$))",
        text,
        re.I | re.DOTALL
    )
    if exp_sum_match:
        experience_summary = exp_sum_match.group(1).strip()
    
    # Extract working experience/employment history - scan entire text for all entries
    working_experience = ""

    # Known next-section headers to bound the EXPERIENCE capture.
    section_boundary_re = r"(?:ACADEMIC QUALIFICATIONS?|EDUCATION|QUALIFICATION|EXPERIENCE SUMMARY|PROFESSIONAL SUMMARY|PROFILE SUMMARY|SUMMARY|SKILLS|TECHNICAL SKILLS|COMPUTER SKILLS|CORE COMPETENCIES|COMPETENCIES|TOOLS|UNIVERSITY PROJECTS|ACADEMIC PROJECTS|INVOLVEMENTS|REFERENCES?|OTHERS)"

    # Strategy 1: Look for an explicit EXPERIENCE section and capture until next known section header.
    work_match = re.search(
        rf"(?:WORKING EXPERIENCE|EMPLOYMENT HISTORY|PROFESSIONAL EXPERIENCE|EXPERIENCE)\s*:?\s*\n(?P<body>.+?)(?=\n\s*{section_boundary_re}\b|\Z)",
        text,
        re.I | re.DOTALL,
    )
    if work_match:
        working_experience = work_match.group("body").strip()
    
    # Strategy 2: If no section found, scan entire text for position-with-date patterns
    if not working_experience:
        # Find all lines with a trailing (duration) parentheses containing a year.
        # Supports multi-parentheses job titles like: "Enumerator (Part Time) (Feb 2024 – Aug 2024)"
        position_pattern = re.compile(
            r"^(?P<pos>.*)\((?P<dur>[^()]*(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Present|\d{4})[^()]*)\)\s*$",
            re.M | re.I,
        )
        matches = list(position_pattern.finditer(text))
        
        if matches:
            # Extract content from first match to before EDUCATION/SKILLS section
            start_pos = matches[0].start()
            end_match = re.search(rf"\n\s*{section_boundary_re}\b", text[start_pos:], re.I)
            if end_match:
                working_experience = text[start_pos:start_pos + end_match.start()].strip()
            else:
                working_experience = text[start_pos:].strip()
    
    # Strategy 3: Fallback to simple pattern (bounded by next known section header)
    if not working_experience:
        work_match = re.search(
            rf"(?:WORKING EXPERIENCE|EMPLOYMENT HISTORY|PROFESSIONAL EXPERIENCE|EXPERIENCE)\s*:?\s*(?P<body>.+?)(?=\n\s*{section_boundary_re}\b|\Z)",
            text,
            re.I | re.DOTALL
        )
        if work_match:
            working_experience = work_match.group("body").strip()
    
    # UNIVERSITY PROJECTS
    university_projects = ""
    uni_match = re.search(
        r"(?:UNIVERSITY PROJECTS|ACADEMIC PROJECTS)\s*:?\s*(.+?)(?=\n(?:EXPERIENCE SUMMARY|EXPERIENCE|WORKING EXPERIENCE|SKILLS|INVOLVEMENTS|REFERENCES|$))",
        text,
        re.I | re.DOTALL
    )
    if uni_match:
        university_projects = uni_match.group(1).strip()

    # SKILLS - includes TECHNICAL SKILLS, COMPUTER SKILLS, etc.
    skills = ""
    skills_match = re.search(
        r"(?:SKILLS|TECHNICAL SKILLS|COMPUTER SKILLS|CORE COMPETENCIES|COMPETENCIES|TOOLS)\s*:?\s*(.+?)(?=\n(?:INVOLVEMENTS|EXPERIENCE|WORKING EXPERIENCE|REFERENCES|UNIVERSITY PROJECTS|CERTIFICATIONS|OTHERS|$))",
        text,
        re.I | re.DOTALL
    )
    if skills_match:
        skills = skills_match.group(1).strip()

    # INVOLVEMENTS
    involvements = ""
    inv_match = re.search(
        r"INVOLVEMENTS\s*:?\s*(.+?)(?=\n(?:REFERENCES|SKILLS|EXPERIENCE|WORKING EXPERIENCE|$))",
        text,
        re.I | re.DOTALL
    )
    if inv_match:
        involvements = inv_match.group(1).strip()

    # REFERENCES
    references = ""
    ref_match = re.search(
        r"REFERENCES?\s*:?\s*(.+)$",
        text,
        re.I | re.DOTALL
    )
    if ref_match:
        references = ref_match.group(1).strip()

    # Add sections to fields dict
    fields["education"] = education
    fields["experience_summary"] = experience_summary
    fields["working_experience"] = working_experience
    fields["university_projects"] = university_projects
    fields["skills"] = skills
    fields["involvements"] = involvements
    fields["references"] = references
    
    return fields


def _extract_work_experience_from_full_text(text: str) -> str:
    """Extract a best-effort WORKING EXPERIENCE chunk directly from full extracted text.

    This is intentionally tolerant of OCR noise and missing section headers.
    """
    if not text:
        return ""

    # Normalize some common OCR bullet placeholders
    normalized = re.sub(r'[�▪▫■□●○◆◇]', '•', text)
    lines = [ln.rstrip() for ln in normalized.splitlines()]

    section_boundary_re = re.compile(
        r"^\s*(?:ACADEMIC QUALIFICATIONS?|EDUCATION|QUALIFICATION|EXPERIENCE SUMMARY|PROFESSIONAL SUMMARY|PROFILE SUMMARY|SUMMARY|SKILLS|TECHNICAL SKILLS|COMPUTER SKILLS|CORE COMPETENCIES|COMPETENCIES|TOOLS|UNIVERSITY PROJECTS|ACADEMIC PROJECTS|INVOLVEMENTS|REFERENCES?|OTHERS)\b",
        re.I,
    )

    # 1) Prefer explicit experience header if it exists
    start_idx = None
    for i, ln in enumerate(lines):
        if re.match(r"^\s*(?:WORKING EXPERIENCE|EMPLOYMENT HISTORY|PROFESSIONAL EXPERIENCE|EXPERIENCE)\b", ln, re.I):
            start_idx = i + 1
            break

    # 2) Otherwise locate first role header line
    def looks_like_duration(value: str) -> bool:
        if not value:
            return False
        if not re.search(r"\d{4}", value):
            return False
        if "-" in value or "–" in value:
            return True
        if re.search(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Present)\b", value, re.I):
            return True
        return False

    if start_idx is None:
        for i, ln in enumerate(lines):
            m1 = re.match(r"^(?P<pos>.+?)\s*\((?P<dur>[^)]+)\)\s*$", ln.strip())
            if m1 and looks_like_duration(m1.group("dur")):
                start_idx = i
                break
            m2 = re.match(r"^(?P<pos>.*)\((?P<dur>[^()]*(?:\d{4})[^()]*)\)\s*$", ln.strip())
            if m2 and looks_like_duration(m2.group("dur")):
                start_idx = i
                break

    if start_idx is None:
        return ""

    end_idx = len(lines)
    for j in range(start_idx + 1, len(lines)):
        if section_boundary_re.match(lines[j]):
            end_idx = j
            break

    chunk = "\n".join(ln.strip() for ln in lines[start_idx:end_idx] if ln.strip())
    return chunk.strip()


def _build_docx(output_path: str, fields: Dict[str, str], source_text: str, logo_path: str = None, cv_number: str = "KLSB_001") -> None:
    """Generate KLSB format Word document perfectly matching KLSB_877_MWAK.pdf template.
    Uses ChatGPT-extracted text and converts to company CV format.
    """
    if not docx_available:
        raise RuntimeError("python-docx is required for Word conversion. Please install python-docx==1.1.2")
    
    doc = Document()
    
    # Set margins to match KLSB template
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.5)
        section.bottom_margin = Inches(0.5)
        section.left_margin = Inches(0.75)
        section.right_margin = Inches(0.75)
    
    # Create header table with logo on the left and centered header text on the right
    if logo_path and os.path.exists(logo_path):
        header_table = doc.add_table(rows=1, cols=2)
        header_table.autofit = False
        header_table.allow_autofit = False
        
        # Left cell - Logo (1.9" x 0.65")
        left_cell = header_table.rows[0].cells[0]
        left_cell.width = Inches(2.0)
        logo_para = left_cell.paragraphs[0]
        logo_para.alignment = WD_ALIGN_PARAGRAPH.LEFT
        try:
            logo_run = logo_para.add_run()
            logo_run.add_picture(logo_path, width=Inches(1.9), height=Inches(0.65))
        except:
            pass
        
        # Right cell - Centered header text
        right_cell = header_table.rows[0].cells[1]
        right_cell.width = Inches(4.5)
        header_p = right_cell.paragraphs[0]
        header_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        # Remove cell borders for clean layout
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
    
    # Header section - matches KLSB_877 format
    run = header_p.add_run("PROFESSIONAL RESUME")
    run.bold = True
    run.font.size = Pt(16)
    header_p.add_run("\n")
    
    run = header_p.add_run(fields.get("name", "CANDIDATE NAME").upper())
    run.bold = True
    run.font.size = Pt(12)
    header_p.add_run("\n")
    
    run = header_p.add_run(cv_number)
    run.bold = True
    run.font.size = Pt(9)
    
    # Add separator
    sep_p = doc.add_paragraph("-" * 100)
    sep_p.paragraph_format.space_before = Pt(3)
    sep_p.paragraph_format.space_after = Pt(6)
    
    # Personal Information - 3-column table (Label, colon, Value) to match KLSB format
    doc.add_paragraph()
    
    # Create personal info table
    info_table = doc.add_table(rows=8, cols=3)
    info_table.autofit = False
    info_table.allow_autofit = False
    
    # Set column widths
    for row in info_table.rows:
        row.cells[0].width = Inches(1.5)  # Label column
        row.cells[1].width = Inches(0.15) # Colon column
        row.cells[2].width = Inches(4.0)  # Value column
    
    # Fill table data
    info_data = [
        ("NAME", fields.get('name', '').upper()),
        ("POSITION", fields.get('position', '').upper()),
        ("DATE OF BIRTH", fields.get('dob', '')),
        ("NATIONALITY", fields.get('nationality', 'MALAYSIAN').upper()),
        ("MARITAL STATUS", fields.get('marital_status', '').upper()),
        ("CONTACT ADDRESS", fields.get('address', '')),
        ("Tel", fields.get('phone', '')),
        ("EMAIL", fields.get('email', '').lower()),
    ]
    
    for idx, (label, value) in enumerate(info_data):
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
        
        # Value cell
        value_cell = row.cells[2]
        value_para = value_cell.paragraphs[0]
        value_run = value_para.add_run(value or "")
        value_run.font.size = Pt(9)
    
    # Remove table borders
    for row in info_table.rows:
        for cell in row.cells:
            tcPr = cell._element.get_or_add_tcPr()
            tcBorders = OxmlElement('w:tcBorders')
            for border_name in ['top', 'left', 'bottom', 'right', 'insideH', 'insideV']:
                border = OxmlElement(f'w:{border_name}')
                border.set(qn('w:val'), 'none')
                tcBorders.append(border)
            tcPr.append(tcBorders)
    
    # Add space
    doc.add_paragraph()
    
    # Use ChatGPT's formatted output directly (no Python parsing needed)
    # Helper to convert any list fields to strings
    def ensure_string(value):
        if isinstance(value, list):
            return "\n".join(str(item) for item in value)
        return str(value) if value else ""

    # Helper to strip any accidental section titles ChatGPT might include
    def strip_titles(s: str) -> str:
        if not s:
            return s
        titles = {
            "EXPERIENCE SUMMARY",
            "ACADEMIC/TECHNICAL QUALIFICATIONS:",
            "ACADEMIC/TECHNICAL QUALIFICATIONS",
            "WORKING EXPERIENCE",
            "OTHERS (TRAININGS/SKILLS/etc.)",
            "INVOLVEMENTS",
            "REFERENCES",
        }
        lines = []
        for ln in s.splitlines():
            val = ln.strip()
            if val in titles:
                continue
            lines.append(ln)
        return "\n".join(lines).strip()

    # Helper to strip any accidental section titles ChatGPT might include
    def strip_titles(s: str) -> str:
        if not s:
            return s
        titles = {
            "EXPERIENCE SUMMARY",
            "ACADEMIC/TECHNICAL QUALIFICATIONS:",
            "ACADEMIC/TECHNICAL QUALIFICATIONS",
            "WORKING EXPERIENCE",
            "OTHERS (TRAININGS/SKILLS/etc.)",
            "INVOLVEMENTS",
            "REFERENCES",
        }
        lines = []
        for ln in s.splitlines():
            val = ln.strip()
            if val in titles:
                continue
            lines.append(ln)
        return "\n".join(lines).strip()
    
    # EXPERIENCE SUMMARY (comes FIRST) - ChatGPT already formatted this
    exp_summary = strip_titles(ensure_string(fields.get("experience_summary", "")).strip())
    if exp_summary:
        heading = doc.add_paragraph()
        heading.paragraph_format.space_before = Pt(6)
        heading.paragraph_format.space_after = Pt(3)
        run = heading.add_run("EXPERIENCE SUMMARY")
        run.bold = False  # NOT bold in template
        run.font.size = Pt(11)
        
        # Split into paragraphs if ChatGPT provided multiple paragraphs
        for para_text in exp_summary.split('\n\n'):
            if para_text.strip():
                p = doc.add_paragraph(para_text.strip())
                p.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                p.paragraph_format.left_indent = Inches(0.25)
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(6)
    
    # ACADEMIC/TECHNICAL QUALIFICATIONS (comes SECOND) - ChatGPT already formatted this
    edu_text = strip_titles(ensure_string(fields.get("education", "")).strip())
    
    if edu_text:
        doc.add_paragraph()
        heading = doc.add_paragraph()
        heading.paragraph_format.space_before = Pt(6)
        heading.paragraph_format.space_after = Pt(3)
        run = heading.add_run("ACADEMIC/TECHNICAL QUALIFICATIONS:")
        run.bold = True
        run.font.size = Pt(11)
        
        # ChatGPT formatted as: "Year1 – Year2\nDegree\nInstitution"
        # Just render directly with proper spacing
        for line in edu_text.split('\n'):
            if line.strip():
                p = doc.add_paragraph(line.strip())
                p.paragraph_format.left_indent = Inches(0.25)
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(2)
    
    # WORKING EXPERIENCE (comes THIRD) - ChatGPT already formatted this with Year, Company, Position, Projects, Job Description
    work_text = strip_titles(ensure_string(fields.get("working_experience", "")).strip())
    
    # Check for work-related involvements to append to working experience
    involvements_text = strip_titles(ensure_string(fields.get("involvements", "")).strip())
    def is_work_related(text: str) -> bool:
        """Check if involvement text is work-related."""
        work_keywords = [
            'led', 'managed', 'developed', 'implemented', 'project', 'team',
            'coordinated', 'organized', 'directed', 'oversaw', 'supervised', 'spearheaded',
            'facilitated', 'contributed', 'worked on', 'responsible', 'duties',
            'position', 'role', 'chairman', 'president', 'vice', 'secretary',
            'treasurer', 'head', 'lead', 'engineer', 'consultant', 'advisor'
        ]
        lower_text = text.lower()
        return any(keyword in lower_text for keyword in work_keywords)
    
    # Extract and append work-related involvements
    if involvements_text:
        work_involvement_items = []
        for line in involvements_text.split('\n'):
            clean_line = re.sub(r'^[•\-\*]\s*', '', line.strip())
            if clean_line and is_work_related(clean_line):
                work_involvement_items.append(clean_line)
        
        # Append to work text if found
        if work_involvement_items:
            work_text += "\n\nADDITIONAL INVOLVEMENTS:\n"
            for item in work_involvement_items:
                work_text += f"• {item}\n"
    
    if work_text:
        doc.add_paragraph()
        heading = doc.add_paragraph()
        heading.paragraph_format.space_before = Pt(6)
        heading.paragraph_format.space_after = Pt(3)
        run = heading.add_run("WORKING EXPERIENCE")
        run.bold = False  # NOT bold in template
        run.font.size = Pt(11)
        
        # Render ChatGPT's formatted work experience directly
        lines = work_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts with bullet point
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                clean_line = re.sub(r'^[•\-\*]\s*', '', line).strip()
                p = doc.add_paragraph(clean_line, style='List Bullet')
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(2)
                p.paragraph_format.left_indent = Inches(0.5)
            # Check if line contains Year/Company/Position/Project/Job Description labels
            elif any(label in line for label in ['Year', 'Company', 'Position', 'Client', 'Duration', 'Project', 'ADDITIONAL INVOLVEMENTS']):
                p = doc.add_paragraph(line)
                # Bold the label part
                if ':' in line:
                    p.clear()
                    label, value = line.split(':', 1)
                    r = p.add_run(label + ': ')
                    r.bold = True
                    p.add_run(value.strip())
                else:
                    # For "ADDITIONAL INVOLVEMENTS:" or similar
                    p.clear()
                    r = p.add_run(line)
                    r.bold = True
                p.paragraph_format.space_before = Pt(2)
                p.paragraph_format.space_after = Pt(1)
                p.paragraph_format.left_indent = Inches(0.25)
            else:
                # Regular line
                p = doc.add_paragraph(line)
                p.paragraph_format.space_before = Pt(1)
                p.paragraph_format.space_after = Pt(1)
                p.paragraph_format.left_indent = Inches(0.25)

    
    # OTHERS (TRAININGS/SKILLS/etc.) - ChatGPT already formatted this
    skills_text = strip_titles(ensure_string(fields.get("skills", "")).strip())
    if skills_text:
        doc.add_paragraph()
        heading = doc.add_paragraph()
        heading.paragraph_format.space_before = Pt(6)
        heading.paragraph_format.space_after = Pt(3)
        run = heading.add_run("OTHERS (TRAININGS/SKILLS/etc.)")
        run.bold = True
        run.font.size = Pt(11)
        
        # Render skills directly as bullet points
        for line in skills_text.split('\n'):
            if line.strip():
                clean_line = re.sub(r'^[•\-\*]\s*', '', line.strip())
                p = doc.add_paragraph(clean_line, style='List Bullet')
                p.paragraph_format.left_indent = Inches(0.5)
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(2)

    # PROFESSIONAL MEMBERSHIP - ChatGPT already formatted this
    prof_members_text = strip_titles(ensure_string(fields.get("professional_memberships", "")).strip())
    if prof_members_text:
        doc.add_paragraph()
        heading = doc.add_paragraph()
        heading.paragraph_format.space_before = Pt(6)
        heading.paragraph_format.space_after = Pt(3)
        run = heading.add_run("PROFESSIONAL MEMBERSHIP")
        run.bold = True
        run.font.size = Pt(11)
        
        # Render professional memberships as bullet points
        for line in prof_members_text.split('\n'):
            if line.strip():
                clean_line = re.sub(r'^[•\-\*]\s*', '', line.strip())
                p = doc.add_paragraph(clean_line, style='List Bullet')
                p.paragraph_format.left_indent = Inches(0.5)
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(2)

    # PROFESSIONAL TRAINING / COMPETENCY - ChatGPT already formatted this
    prof_training_text = strip_titles(ensure_string(fields.get("professional_training", "")).strip())
    if prof_training_text:
        doc.add_paragraph()
        heading = doc.add_paragraph()
        heading.paragraph_format.space_before = Pt(6)
        heading.paragraph_format.space_after = Pt(3)
        run = heading.add_run("PROFESSIONAL TRAINING / COMPETENCY")
        run.bold = True
        run.font.size = Pt(11)
        
        # Render professional training as bullet points
        for line in prof_training_text.split('\n'):
            if line.strip():
                clean_line = re.sub(r'^[•\-\*]\s*', '', line.strip())
                p = doc.add_paragraph(clean_line, style='List Bullet')
                p.paragraph_format.left_indent = Inches(0.5)
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(2)

    # COMPUTER SKILLS - ChatGPT already formatted this
    computer_skills_text = strip_titles(ensure_string(fields.get("computer_skills", "")).strip())
    if computer_skills_text:
        doc.add_paragraph()
        heading = doc.add_paragraph()
        heading.paragraph_format.space_before = Pt(6)
        heading.paragraph_format.space_after = Pt(3)
        run = heading.add_run("COMPUTER SKILLS")
        run.bold = True
        run.font.size = Pt(11)
        
        # Render computer skills as bullet points
        for line in computer_skills_text.split('\n'):
            if line.strip():
                clean_line = re.sub(r'^[•\-\*]\s*', '', line.strip())
                p = doc.add_paragraph(clean_line, style='List Bullet')
                p.paragraph_format.left_indent = Inches(0.5)
                p.paragraph_format.space_before = Pt(0)
                p.paragraph_format.space_after = Pt(2)
    
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

    # Matches common single-parens format: "Position (Apr 2025 – Present)"
    header_pattern = re.compile(r"^(?P<position>.+?)\s*\((?P<year>[^)]+)\)\s*$")
    # Matches lines that START with a year range (used in some CVs)
    year_range_pattern = re.compile(r"^(?:[A-Za-z]{3}\s+)?\d{4}\s*[-–]\s*(?:Present|\d{4}|[A-Za-z]{3}\s*\d{4})", re.I)
    # Matches lines where the LAST parentheses contains a year, e.g.:
    # "Enumerator (Part Time) (Feb 2024 – Aug 2024)" -> pos="Enumerator (Part Time)", year="Feb 2024 – Aug 2024"
    trailing_year_parens_pattern = re.compile(r"^(?P<pos>.*)\((?P<year>[^()]*(?:\d{4})[^()]*)\)\s*$")
    bullet_re = re.compile(r'^[•\-\*�▪]')

    def looks_like_duration(value: str) -> bool:
        if not value:
            return False
        if not re.search(r"\d{4}", value):
            return False
        if "-" in value or "–" in value:
            return True
        if re.search(r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec|Present)\b", value, re.I):
            return True
        return False

    blocks = []
    current_block = {"description": [], "projects": []}
    current_roles = []
    mode = None  # None | "projects" | "description"

    def push_block():
        nonlocal current_block, mode, current_roles
        if current_block and (current_block.get("year") or current_block.get("company") or current_block.get("position") or current_roles):
            # Store accumulated roles as position if we collected any
            if current_roles and not current_block.get("position"):
                current_block["position"] = " | ".join(r for r in current_roles if r)
            # Remove empty description/projects lists
            if not current_block.get("description"):
                current_block.pop("description", None)
            if not current_block.get("projects"):
                current_block.pop("projects", None)
            # Clean up temp fields
            current_block.pop("_temp_address", None)
            blocks.append(current_block)
        # Reset for next block
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

        lower_line = line.lower()
        if lower_line.startswith("project involved") or lower_line.startswith("client:") or lower_line.startswith("duration:"):
            mode = "projects"
            idx += 1
            continue
        if lower_line.startswith("job description") or lower_line.startswith("scope of work") or lower_line.startswith("responsibilities"):
            mode = "description"
            idx += 1
            continue

        # Bullet/indented content (must be handled before header detection; bullets can contain parentheses)
        if bullet_re.match(line):
            clean = re.sub(r'^[•\-\*�▪]\s*', '', line).strip()
            target = "projects" if mode == "projects" else "description"
            current_block.setdefault(target, []).append(clean)
            idx += 1
            continue

        # Labeled fields (Year/Company/Position)
        if line.startswith("Year") and ":" in line:
            push_block()
            current_block["year"] = line.split(":", 1)[1].strip()
            idx += 1
            continue
        if line.startswith("Company") and ":" in line:
            company_value = line.split(":", 1)[1].strip()
            # Detect if this looks like an address (contains street indicators)
            if any(indicator in company_value.lower() for indicator in ["jalan", "street", "level", "menara", "floor", "avenue", "road", "no.", "lot"]):
                # This is likely an address, store temporarily
                current_block["_temp_address"] = company_value
            else:
                current_block["company"] = company_value
            idx += 1
            continue
        if line.startswith("Position") and ":" in line:
            pos_value = line.split(":", 1)[1].strip()
            # Check if we stored an address in company field
            if "_temp_address" in current_block:
                # Position field actually contains the company name, swap them
                current_block["company"] = pos_value
                # Discard the address, we don't use it
                current_block.pop("_temp_address", None)
            else:
                # Normal case: position is position
                if pos_value:
                    current_roles.append(pos_value)
            idx += 1
            continue

        # Header style: Position (Date Range) - extract both
        header_match = header_pattern.match(line)
        if header_match:
            year_part = header_match.group("year").strip()
            if looks_like_duration(year_part):
                push_block()
                current_block["position"] = header_match.group("position").strip()
                current_block["year"] = year_part
                idx += 1
                continue

        # Multi-parentheses header style: take LAST parens containing a year
        trailing_match = trailing_year_parens_pattern.match(line)
        if trailing_match:
            pos_part = (trailing_match.group("pos") or "").strip()
            year_part = (trailing_match.group("year") or "").strip()
            # Only accept if it looks like a real duration (has a year AND dash/Present/month)
            if pos_part and looks_like_duration(year_part):
                push_block()
                current_block["position"] = pos_part
                current_block["year"] = year_part
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

        # Fallback: description line
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

    # Text cell (centered) — follow KLSB header
    header_text = [
        Paragraph("PROFESSIONAL RESUME", ParagraphStyle("H1", parent=styles["Normal"], fontSize=16, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=2)),
        Paragraph(fields.get("name", "CANDIDATE NAME").upper(), ParagraphStyle("H2", parent=styles["Normal"], fontSize=12, fontName="Helvetica-Bold", alignment=TA_CENTER, spaceAfter=2)),
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

    # Helper to convert any list fields to strings
    def ensure_string(value):
        if isinstance(value, list):
            return "\n".join(str(item) for item in value)
        return str(value) if value else ""

    # Personal info block - 3-column table with labels, colons, and values
    info_items = [
        ("NAME", fields.get("name", "").upper()),
        ("POSITION", fields.get("position", "").upper()),
        ("DATE OF BIRTH", fields.get("dob", "")),
        ("NATIONALITY", fields.get("nationality", "MALAYSIAN").upper()),
        ("MARITAL STATUS", (fields.get("marital_status", "") or "").upper()),
        ("CONTACT ADDRESS", fields.get("address", "")),
        ("Tel", fields.get("phone", "")),
        ("EMAIL", fields.get("email", "")),
    ]

    left_rows = []
    for label, value in info_items:
        if not label and not value:
            continue
        left_rows.append([
            Paragraph(f"<b>{label}</b>", text_style),
            Paragraph("<b>:</b>", text_style),
            Paragraph(value or "", text_style),
        ])

    left_table = Table(left_rows, colWidths=[1.5*inch, 0.15*inch, 3.95*inch])
    left_table.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 3),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 2),
        ("ALIGN", (0,0), (0,-1), "LEFT"),
        ("ALIGN", (1,0), (1,-1), "CENTER"),
        ("ALIGN", (2,0), (2,-1), "LEFT"),
    ]))

    # Photo column (placeholder if none)
    photo_cell = []
    try:
        if fields.get("photo_path") and os.path.exists(fields["photo_path"]):
            photo_cell.append(Image(fields["photo_path"], width=1.7*inch, height=2.2*inch))
        else:
            photo_cell.append(Spacer(1, 2.2*inch))
    except Exception:
        photo_cell.append(Spacer(1, 2.2*inch))

    info_row = Table([[left_table, photo_cell]], colWidths=[5.6*inch, 1.75*inch])
    info_row.setStyle(TableStyle([
        ("VALIGN", (0,0), (-1,-1), "TOP"),
        ("LEFTPADDING", (0,0), (-1,-1), 0),
        ("RIGHTPADDING", (0,0), (-1,-1), 0),
        ("TOPPADDING", (0,0), (-1,-1), 0),
        ("BOTTOMPADDING", (0,0), (-1,-1), 0),
    ]))
    elements.append(info_row)
    elements.append(Spacer(1, 0.12 * inch))

    # Horizontal line separator (single rule)
    elements.append(Table([[""]], colWidths=[6.7 * inch], style=TableStyle([
        ("LINEBELOW", (0, 0), (-1, -1), 1, colors.black),
    ])))
    elements.append(Spacer(1, 0.15 * inch))

    # Helper to convert any list fields to strings
    def ensure_string(value):
        if isinstance(value, list):
            return "\n".join(str(item) for item in value)
        return str(value) if value else ""

    # Helper to strip any accidental section titles ChatGPT might include
    def strip_titles(s: str) -> str:
        if not s:
            return s
        titles = {
            "EXPERIENCE SUMMARY",
            "ACADEMIC/TECHNICAL QUALIFICATIONS:",
            "ACADEMIC/TECHNICAL QUALIFICATIONS",
            "WORKING EXPERIENCE",
            "OTHERS (TRAININGS/SKILLS/etc.)",
            "INVOLVEMENTS",
            "REFERENCES",
        }
        lines = []
        for ln in s.splitlines():
            val = ln.strip()
            if val in titles:
                continue
            lines.append(ln)
        return "\n".join(lines).strip()

    # EXPERIENCE SUMMARY (comes FIRST) - ChatGPT already formatted
    exp_summary = strip_titles(ensure_string(fields.get("experience_summary", "")).strip())
    
    if exp_summary:
        elements.append(Paragraph("EXPERIENCE SUMMARY", section_title_style))
        elements.append(Spacer(1, 0.05 * inch))
        # Render paragraphs directly
        for para in exp_summary.split('\n\n'):
            if para.strip():
                elements.append(Paragraph(para.strip(), text_style))
        elements.append(Spacer(1, 0.1 * inch))
    
    # ACADEMIC/TECHNICAL QUALIFICATIONS (comes SECOND) - ChatGPT already formatted
    edu_text = strip_titles(ensure_string(fields.get("education", "")).strip())
    if edu_text:
        elements.append(Paragraph("ACADEMIC/TECHNICAL QUALIFICATIONS:", section_title_style))
        elements.append(Spacer(1, 0.05 * inch))
        
        # Render education directly - ChatGPT formatted as:
        # Year – Year
        # Degree
        # Institution
        for line in edu_text.split('\n'):
            if line.strip():
                elements.append(Paragraph(line.strip(), text_style))
        elements.append(Spacer(1, 0.1 * inch))
    
    # WORKING EXPERIENCE (comes THIRD) - ChatGPT already formatted
    work_text = strip_titles(ensure_string(fields.get("working_experience", "")).strip())

    if work_text:
        elements.append(Paragraph("WORKING EXPERIENCE", section_title_style))
        elements.append(Spacer(1, 0.05 * inch))
        
        # Render ChatGPT's formatted work experience directly - Match DOCX format
        lines = work_text.split('\n')
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Check if line starts with bullet point
            if line.startswith('•') or line.startswith('-') or line.startswith('*'):
                clean_line = re.sub(r'^[•\-\*]\s*', '', line).strip()
                p_text = f"• {clean_line}"
                elements.append(Paragraph(p_text, text_style))
            # Check if line contains Year/Company/Position/Project/Job Description labels
            elif any(label in line for label in ['Year', 'Company', 'Position', 'Client', 'Duration', 'Project', 'Job Description']):
                # Bold the label part if there's a colon
                if ':' in line:
                    label, value = line.split(':', 1)
                    p_text = f"<b>{label}:</b> {value.strip()}"
                else:
                    p_text = line
                elements.append(Paragraph(p_text, text_style))
            else:
                # Regular line
                elements.append(Paragraph(line, text_style))
        
        elements.append(Spacer(1, 0.1 * inch))
    
    # OTHERS (TRAININGS/SKILLS/etc.) - ChatGPT already formatted
    skills_text = strip_titles(ensure_string(fields.get("skills", "")).strip())
    if skills_text:
        elements.append(Paragraph("OTHERS (TRAININGS/SKILLS/etc.)", section_title_style))
        elements.append(Spacer(1, 0.05 * inch))
        
        for line in skills_text.split('\n'):
            if line.strip():
                clean_line = re.sub(r'^[•\-\*]\s*', '', line.strip())
                elements.append(Paragraph(f"• {clean_line}", bullet_style))
        elements.append(Spacer(1, 0.1 * inch))

    # INVOLVEMENTS - ChatGPT already formatted
    involvements_text = strip_titles(ensure_string(fields.get("involvements", "")).strip())
    if involvements_text:
        elements.append(Paragraph("INVOLVEMENTS", section_title_style))
        elements.append(Spacer(1, 0.05 * inch))
        
        for line in involvements_text.split('\n'):
            if line.strip():
                elements.append(Paragraph(line.strip(), text_style))
        elements.append(Spacer(1, 0.1 * inch))

    # REFERENCES - ChatGPT already formatted
    refs_text = strip_titles(ensure_string(fields.get("references", "")).strip())
    if refs_text:
        elements.append(Paragraph("REFERENCES", section_title_style))
        elements.append(Spacer(1, 0.05 * inch))
        
        for line in refs_text.split('\n'):
            if line.strip():
                elements.append(Paragraph(line.strip(), text_style))
        elements.append(Spacer(1, 0.1 * inch))
    
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
    - EDUCATION/QUALIFICATIONS -> qualifications
    - EXPERIENCE SUMMARY -> experience_summary
    - EXPERIENCE (with dates/companies) -> working_experience
    - EXPERIENCE (descriptive only) -> experience_summary
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


def convert_cv_to_klsb_ocr(source_path: str, output_dir: str, overrides: Optional[Dict[str, str]] = None, output_format: str = "docx", use_chatgpt: bool = False) -> Tuple[str, Dict[str, str]]:
    """Convert a CV into KLSB format using ChatGPT or traditional OCR.
    
    Args:
        source_path: Path to source CV file
        output_dir: Directory to save converted file
        overrides: Optional field overrides
        output_format: Output format - "docx" (Word) or "pdf" (default: docx)
        use_chatgpt: If True, use ChatGPT Vision API; if False, use traditional tesseract OCR

    Returns: (output_path, detected_fields)
    """
    import time
    
    if not os.path.exists(source_path):
        raise FileNotFoundError(f"Source CV not found: {source_path}")

    # Extract text and parse based on selected method
    if use_chatgpt:
        # Use ChatGPT Vision API for extraction and parsing (no fallback)
        fields = _extract_cv_with_chatgpt(source_path)
        full_text = fields.get("full_text", "")
    else:
        # Use traditional OCR (tesseract)
        raw_text = _extract_text_from_pdf(source_path, use_chatgpt=False)
        fields = _parse_cv_sections(raw_text)
        full_text = raw_text
        # Keep parity with ChatGPT path: include full extracted text in fields
        fields["full_text"] = full_text

    # Fill any missing personal fields from full text heuristics
    guess = _guess_fields(full_text)
    for k in ["name","position","dob","nationality","marital_status","address","phone","email","linkedin"]:
        if not fields.get(k):
            fields[k] = guess.get(k, fields.get(k, ""))

    overrides = overrides or {}
    for key, val in overrides.items():
        if val:
            fields[key] = val

    # Use the full extracted text for builders to enable full-content parsing
    text = full_text or ""

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

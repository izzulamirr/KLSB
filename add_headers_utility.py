"""
Utility to add KEMUNCAK LANAI headers to DOCX files
Can be used to update existing CVs or batch add headers
"""

import os
from docx import Document
from docx.shared import Pt, Inches
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.oxml import OxmlElement


def add_header_to_docx(doc_path, candidate_name=None, output_path=None):
    """
    Add professional header with KEMUNCAK LANAI branding to a DOCX file
    
    Args:
        doc_path: Path to existing DOCX file
        candidate_name: Name to display (extracted from file if None)
        output_path: Save location (overwrites original if None)
    """
    
    doc = Document(doc_path)
    section = doc.sections[0]
    header = section.header
    
    # Extract name from file if not provided
    if not candidate_name:
        # Try to extract from document body
        for para in doc.paragraphs:
            if "JOHN SMITH" in para.text.upper():
                candidate_name = "JOHN SMITH"
                break
            elif "AHMAD HASSAN" in para.text.upper():
                candidate_name = "AHMAD HASSAN"
                break
            elif "SARAH JOHNSON" in para.text.upper():
                candidate_name = "SARAH JOHNSON"
                break
        
        if not candidate_name:
            candidate_name = "PROFESSIONAL CV"
    
    # Clear existing header
    for paragraph in list(header.paragraphs):
        p = paragraph._element
        p.getparent().remove(p)
    
    # Para 1: PROFESSIONAL RESUME (right-aligned)
    para1 = header.add_paragraph()
    para1.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    para1.paragraph_format.space_after = Pt(0)
    run1 = para1.add_run("PROFESSIONAL RESUME")
    run1.italic = True
    run1.bold = True
    run1.font.size = Pt(14)
    
    # Para 2: Candidate name (right-aligned)
    para2 = header.add_paragraph()
    para2.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    para2.paragraph_format.space_after = Pt(0)
    run2 = para2.add_run(candidate_name.upper() if candidate_name else "NAME")
    run2.italic = True
    run2.font.size = Pt(10)
    
    # Para 3: KLSB_0 (right-aligned)
    para3 = header.add_paragraph()
    para3.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    para3.paragraph_format.space_after = Pt(0)
    run3 = para3.add_run("KLSB_0")
    run3.italic = True
    run3.font.size = Pt(10)
    
    # Para 4: Page number (right-aligned)
    para4 = header.add_paragraph()
    para4.alignment = WD_ALIGN_PARAGRAPH.RIGHT
    para4.paragraph_format.space_after = Pt(6)
    run4 = para4.add_run("Page 1 of 3")
    run4.font.size = Pt(9)
    
    # Para 5: Horizontal separator
    para_sep = header.add_paragraph()
    para_sep.paragraph_format.space_before = Pt(0)
    para_sep.paragraph_format.space_after = Pt(12)
    run_sep = para_sep.add_run("_" * 100)
    run_sep.font.size = Pt(8)
    
    # Save document
    output_file = output_path or doc_path
    doc.save(output_file)
    
    return output_file


def batch_add_headers_to_folder(folder_path, pattern="KLSB_*.docx", overwrite=True):
    """
    Add headers to all DOCX files matching pattern in a folder
    
    Args:
        folder_path: Folder to process
        pattern: Glob pattern for files to update
        overwrite: Whether to overwrite original files
    """
    
    from pathlib import Path
    import glob
    
    folder = Path(folder_path)
    if not folder.exists():
        print(f"❌ Folder not found: {folder_path}")
        return
    
    # Find matching files
    files = glob.glob(str(folder / pattern))
    
    if not files:
        print(f"❌ No files matching pattern: {pattern}")
        return
    
    print(f"\n{'='*60}")
    print(f"BATCH ADD HEADERS TO DOCX FILES")
    print(f"{'='*60}")
    print(f"Folder: {folder_path}")
    print(f"Pattern: {pattern}")
    print(f"Files found: {len(files)}")
    print(f"{'='*60}\n")
    
    success_count = 0
    error_count = 0
    
    for file_path in sorted(files):
        try:
            file_name = os.path.basename(file_path)
            add_header_to_docx(file_path, output_path=file_path if overwrite else None)
            success_count += 1
            print(f"✓ {file_name}")
        except Exception as e:
            error_count += 1
            print(f"✗ {file_name}: {str(e)}")
    
    print(f"\n{'='*60}")
    print(f"Batch Header Addition Complete")
    print(f"{'='*60}")
    print(f"✓ Updated: {success_count} files")
    print(f"✗ Errors: {error_count} files")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    # Add headers to all KLSB batch CVs
    batch_add_headers_to_folder(
        folder_path="uploads/cv",
        pattern="KLSB_BATCH_*.docx",
        overwrite=True
    )

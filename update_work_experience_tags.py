"""
Update KLSB_template_true.docx to use individual work experience tags:
- {{work_years}} for Year
- {{work_company}} for Company
- {{work_position}} for Position
- {{working_experience_formatted}} for Job Description bullets only
"""

from docx import Document
import os


def update_work_experience_section():
    """Update work experience section in the template"""
    
    template_path = "KLSB_template_true.docx"
    
    if not os.path.exists(template_path):
        print(f"❌ Template not found: {template_path}")
        print(f"   Please close the file in Word if it's open")
        return
    
    print(f"\n{'='*70}")
    print(f"UPDATING WORK EXPERIENCE TAGS IN TEMPLATE")
    print(f"{'='*70}")
    print(f"Template: {template_path}\n")
    
    try:
        # Load document
        doc = Document(template_path)
        
        changes_made = 0
        
        # Search through all paragraphs
        for para_idx, para in enumerate(doc.paragraphs):
            original_text = para.text
            
            # Look for WORKING EXPERIENCE section
            if 'WORKING EXPERIENCE' in para.text.upper():
                print(f"\n✓ Found WORKING EXPERIENCE section at paragraph {para_idx}")
                
                # Check next few paragraphs for the tags
                for i in range(para_idx + 1, min(para_idx + 10, len(doc.paragraphs))):
                    check_para = doc.paragraphs[i]
                    text = check_para.text.strip()
                    
                    # Update Year line
                    if text.startswith('Year') and ':' in text:
                        print(f"  → Updating Year tag at paragraph {i}")
                        for run in check_para.runs:
                            if '{{' in run.text or 'work' in run.text.lower():
                                run.text = run.text.replace('{{working_experience_formatted}}', '{{work_years}}')
                                run.text = run.text.replace('{{work_years}}', '{{work_years}}')  # Ensure it's set
                                # If it's just the placeholder without the label
                                if run.text.strip().startswith('{{'):
                                    run.text = '{{work_years}}'
                                changes_made += 1
                        if not any('{{' in run.text for run in check_para.runs):
                            # Add the tag if missing
                            check_para.text = 'Year : {{work_years}}'
                            changes_made += 1
                    
                    # Update Company line
                    elif text.startswith('Company') and ':' in text:
                        print(f"  → Updating Company tag at paragraph {i}")
                        for run in check_para.runs:
                            if '{{' in run.text or 'work' in run.text.lower():
                                run.text = run.text.replace('{{working_experience_formatted}}', '{{work_company}}')
                                run.text = run.text.replace('{{work_company}}', '{{work_company}}')
                                if run.text.strip().startswith('{{'):
                                    run.text = '{{work_company}}'
                                changes_made += 1
                        if not any('{{' in run.text for run in check_para.runs):
                            check_para.text = 'Company : {{work_company}}'
                            changes_made += 1
                    
                    # Update Position line
                    elif text.startswith('Position') and ':' in text:
                        print(f"  → Updating Position tag at paragraph {i}")
                        for run in check_para.runs:
                            if '{{' in run.text or 'work' in run.text.lower():
                                run.text = run.text.replace('{{working_experience_formatted}}', '{{work_position}}')
                                run.text = run.text.replace('{{work_position}}', '{{work_position}}')
                                if run.text.strip().startswith('{{'):
                                    run.text = '{{work_position}}'
                                changes_made += 1
                        if not any('{{' in run.text for run in check_para.runs):
                            check_para.text = 'Position : {{work_position}}'
                            changes_made += 1
                    
                    # Update job description placeholder
                    elif '{{working_experience_formatted}}' in text and 'Year' not in text and 'Company' not in text and 'Position' not in text:
                        print(f"  → Found job description placeholder at paragraph {i}")
                        # This one stays as working_experience_formatted (for bullets only)
                        print(f"    (keeping {{{{working_experience_formatted}}}} for job descriptions)")
                
                break  # Found the section, stop searching
        
        # Save updated template
        doc.save(template_path)
        
        print(f"\n✓ Template updated successfully!")
        print(f"  Changes made: {changes_made}")
        print(f"\nNew structure:")
        print(f"  Year : {{{{work_years}}}}")
        print(f"  Company : {{{{work_company}}}}")
        print(f"  Position : {{{{work_position}}}}")
        print(f"  {{{{working_experience_formatted}}}} - Job description bullets only")
        print(f"\n{'='*70}\n")
        
    except PermissionError:
        print(f"\n❌ Permission denied!")
        print(f"   Please close {template_path} in Word and try again.\n")
    except Exception as e:
        print(f"\n❌ Error: {str(e)}\n")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    update_work_experience_section()

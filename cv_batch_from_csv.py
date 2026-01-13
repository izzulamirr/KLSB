"""
Batch CV generation from CSV file using template
Reads candidate data from CSV and generates individual CVs from DOCX template
"""

import csv
import os
from pathlib import Path
from docxtpl import DocxTemplate
from datetime import datetime


def format_working_experience(raw_text):
    """
    Format working experience data from CSV into proper structure.
    Expected format in CSV: lines separated by newlines with Year, Company, Position fields
    Returns formatted text with proper indentation and structure
    """
    if not raw_text or not raw_text.strip():
        return ""
    
    lines = raw_text.strip().split('\n')
    formatted_lines = []
    
    for line in lines:
        line = line.strip()
        if line:
            # Add proper spacing for CSV formatting
            if any(line.startswith(prefix) for prefix in ['Year', 'Company', 'Position', 'Project']):
                formatted_lines.append(line)
            else:
                formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)


def generate_cvs_from_csv(csv_filepath, template_path, output_dir='uploads/cv'):
    """
    Generate CVs from CSV file using a DOCX template.
    
    Args:
        csv_filepath: Path to CSV file with candidate data
        template_path: Path to KLSB template DOCX file
        output_dir: Directory to save generated CVs
    """
    
    # Ensure output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Check if template exists
    if not os.path.exists(template_path):
        print(f"❌ Error: Template file not found: {template_path}")
        return
    
    # Check if CSV exists
    if not os.path.exists(csv_filepath):
        print(f"❌ Error: CSV file not found: {csv_filepath}")
        return
    
    generated_count = 0
    failed_count = 0
    
    print(f"\n{'='*60}")
    print(f"BATCH CV GENERATION FROM CSV")
    print(f"{'='*60}")
    print(f"Template: {template_path}")
    print(f"CSV File: {csv_filepath}")
    print(f"Output Directory: {output_dir}")
    print(f"{'='*60}\n")
    
    try:
        with open(csv_filepath, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            
            # Verify headers exist
            if not reader.fieldnames:
                print("❌ Error: CSV file is empty or has no headers")
                return
            
            print(f"CSV Headers: {', '.join(reader.fieldnames)}\n")
            
            for row_num, row in enumerate(reader, 1):
                try:
                    # Load template fresh for each CV
                    template = DocxTemplate(template_path)
                    
                    # Format working experience data
                    working_exp_raw = row.get('working_experience', '')
                    working_exp_formatted = format_working_experience(working_exp_raw)
                    
                    # Build context dictionary from CSV row
                    context = {
                        'name': row.get('name', '').upper() if row.get('name') else '',
                        'position': row.get('position', '').upper() if row.get('position') else '',
                        'dob': row.get('dob', ''),
                        'nationality': row.get('nationality', 'MALAYSIAN').upper() if row.get('nationality') else 'MALAYSIAN',
                        'marital_status': row.get('marital_status', ''),
                        'address': row.get('address', ''),
                        'phone': row.get('phone', ''),
                        'email': row.get('email', ''),
                        'linkedin': row.get('linkedin', ''),
                        'experience_summary': row.get('experience_summary', ''),
                        'education': row.get('education', ''),
                        'working_experience': working_exp_formatted,
                        'skills': row.get('skills', ''),
                        'professional_training': row.get('professional_training', ''),
                        'computer_skills': row.get('computer_skills', ''),
                        'professional_memberships': row.get('professional_memberships', ''),
                        'involvements': row.get('involvements', ''),
                    }
                    
                    # Render the template with context
                    template.render(context)
                    
                    # Generate output filename
                    candidate_name = row.get('name', f'Candidate_{row_num}').lower().replace(' ', '-')
                    output_filename = f"KLSB_BATCH_{row_num:03d}_{candidate_name}.docx"
                    output_path = os.path.join(output_dir, output_filename)
                    
                    # Save the generated CV
                    template.save(output_path)
                    generated_count += 1
                    
                    print(f"✓ Row {row_num}: {context['name'][:40]} → {output_filename}")
                    
                except Exception as e:
                    failed_count += 1
                    candidate_name = row.get('name', f'Candidate_{row_num}')
                    print(f"✗ Row {row_num}: {candidate_name} - Error: {str(e)}")
        
        # Summary
        print(f"\n{'='*60}")
        print(f"BATCH GENERATION COMPLETE")
        print(f"{'='*60}")
        print(f"✓ Generated: {generated_count} CVs")
        print(f"✗ Failed: {failed_count} CVs")
        print(f"Total processed: {generated_count + failed_count}")
        print(f"Output directory: {os.path.abspath(output_dir)}")
        print(f"{'='*60}\n")
        
        return generated_count, failed_count
        
    except FileNotFoundError as e:
        print(f"❌ File error: {e}")
        return 0, 0
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return 0, 0


if __name__ == "__main__":
    # Configuration
    CSV_FILE = "candidates.csv"
    TEMPLATE_FILE = "KLSB_template_true.docx"
    OUTPUT_DIR = "uploads/cv"
    
    # Generate CVs
    generate_cvs_from_csv(CSV_FILE, TEMPLATE_FILE, OUTPUT_DIR)

"""
Parse CV data into detailed structured fields for template tags
"""

import re
from typing import List, Dict


def parse_work_experience(work_exp_text: str) -> List[Dict[str, str]]:
    """
    Parse work experience text into structured components
    Handles formats like:
    Year : 2023 - Present
    Company : Company Name
    Position : Job Title
    Job Description:
    • Responsibility 1
    • Responsibility 2
    
    Returns list of dicts with: years, company, position, description (as bullets)
    """
    if not work_exp_text or not work_exp_text.strip():
        return []
    
    experiences = []
    lines = work_exp_text.strip().split('\n')
    
    job = None
    i = 0
    
    while i < len(lines):
        line = lines[i].strip()
        i += 1
        
        if not line:
            continue
        
        # Check for Year marker
        if line.lower().startswith('year'):
            # Save previous job if exists
            if job and (job['years'] or job['company'] or job['position']):
                job['description'] = '\n'.join(job['description'])
                experiences.append(job)
            
            # Start new job
            job = {
                'years': '',
                'company': '',
                'position': '',
                'description': []
            }
            
            # Extract year value (after the colon)
            if ':' in line:
                job['years'] = line.split(':', 1)[1].strip()
        
        elif job is not None:
            # We're in a job entry
            if line.lower().startswith('company'):
                if ':' in line:
                    job['company'] = line.split(':', 1)[1].strip()
            elif line.lower().startswith('position'):
                if ':' in line:
                    job['position'] = line.split(':', 1)[1].strip()
            elif line.lower().startswith('job description'):
                # Skip the header, next lines will be bullets
                pass
            elif line.lower().startswith('project involved'):
                # Skip the header
                pass
            elif line.startswith('•') or line.startswith('-') or line.startswith('*'):
                # This is a bullet point description
                job['description'].append(line.lstrip('•-* ').strip())
            elif line and not any(line.lower().startswith(x) for x in ['year', 'company', 'position', 'project', 'job']):
                # Could be a continuation or standalone description
                if job['description'] or (job['company'] and job['position']):
                    job['description'].append(line)
    
    # Don't forget the last job
    if job and (job['years'] or job['company'] or job['position']):
        job['description'] = '\n'.join(job['description'])
        experiences.append(job)
    
    return experiences


def parse_education(education_text: str) -> List[Dict[str, str]]:
    """
    Parse education text into structured components.
    Handles formats like:
    2020 – 2024
    Bachelor of Mechanical Engineering (Hons.)
    Universiti Putra Malaysia (UPM)
    
    Returns list of dicts with: years, university, degree, description
    """
    if not education_text or not education_text.strip():
        return []
    
    educations = []
    lines = education_text.strip().split('\n')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        if not line:
            i += 1
            continue
        
        # Check if this line starts with years
        year_match = re.match(r'(\d{4}\s*[-–]\s*(?:Present|\d{4}))', line)
        
        if year_match:
            edu = {
                'years': year_match.group(1).strip(),
                'degree': '',
                'university': '',
                'description': ''
            }
            
            # Look at next lines for degree and university
            i += 1
            
            # Next line should be degree if it contains common degree keywords
            if i < len(lines):
                next_line = lines[i].strip()
                if any(keyword in next_line.lower() for keyword in ['bachelor', 'master', 'doctor', 'diploma', 'degree', 'certificate', 'of ', 'in ']):
                    edu['degree'] = next_line
                    i += 1
                    # Next line might be university
                    if i < len(lines):
                        next_line = lines[i].strip()
                        if any(keyword in next_line.lower() for keyword in ['university', 'college', 'institute', 'academy', 'school', 'upm', 'uitm', 'utm']):
                            edu['university'] = next_line
                            i += 1
                elif any(keyword in next_line.lower() for keyword in ['university', 'college', 'institute', 'academy', 'school', 'upm', 'uitm', 'utm']):
                    edu['university'] = next_line
                    i += 1
            
            if edu['years'] or edu['degree'] or edu['university']:
                educations.append(edu)
        else:
            i += 1
    
    return educations


def structure_cv_data(cv_data: Dict[str, str]) -> Dict[str, any]:
    """
    Convert flat CV data into structured format with detailed tags.
    Provides both individual tags (for first entry) and formatted all-entries strings.
    """
    structured = cv_data.copy()
    
    # Parse working experience into detailed components
    work_exp_text = cv_data.get('working_experience', '')
    work_experiences = parse_work_experience(work_exp_text)
    structured['work_experiences'] = work_experiences
    
    # Format ALL work experiences as a single formatted string for template
    if work_experiences:
        all_work_formatted = []
        for idx, work in enumerate(work_experiences):
            work_parts = []
            if work.get('years'):
                work_parts.append(f"Year : {work['years']}")
            if work.get('company'):
                work_parts.append(f"Company : {work['company']}")
            if work.get('position'):
                work_parts.append(f"Position : {work['position']}")
            
            desc = work.get('description', '')
            if desc:
                work_parts.append("")
                work_parts.append("Job Description:")
                # Ensure description has bullets
                desc_lines = desc.split('\n')
                for line in desc_lines:
                    if line.strip():
                        if not line.strip().startswith('•'):
                            work_parts.append(f"• {line.strip()}")
                        else:
                            work_parts.append(line.strip())
            
            if work_parts:
                all_work_formatted.append('\n'.join(work_parts))
        
        # Provide as both individual tags (for first) and all entries
        structured['working_experience_formatted'] = '\n\n'.join(all_work_formatted)
        
        # Still provide first entry tags for backward compatibility
        structured['work_years'] = work_experiences[0].get('years', '')
        structured['work_company'] = work_experiences[0].get('company', '')
        structured['work_position'] = work_experiences[0].get('position', '')
        structured['work_description'] = work_experiences[0].get('description', '')
    
    # Parse education into detailed components
    education_text = cv_data.get('education', '')
    educations = parse_education(education_text)
    structured['educations'] = educations
    
    # Format education as simple text (each entry separated by newline for table cells)
    if educations:
        # Simple list format for easy insertion
        edu_periods = []
        edu_descriptions = []
        
        for edu in educations:
            edu_periods.append(edu.get('years', ''))
            
            # Description combines degree and university
            desc_parts = []
            if edu.get('degree'):
                desc_parts.append(edu['degree'])
            if edu.get('university'):
                desc_parts.append(edu['university'])
            edu_descriptions.append('\n'.join(desc_parts))
        
        # Provide single strings with entries separated by double newline
        structured['education_periods'] = '\n\n'.join(edu_periods)
        structured['education_descriptions'] = '\n\n'.join(edu_descriptions)
        
        # Also provide formatted text (backward compatibility)
        all_edu_formatted = []
        for edu in educations:
            edu_parts = []
            if edu.get('years'):
                edu_parts.append(edu['years'])
            if edu.get('degree'):
                edu_parts.append(edu['degree'])
            if edu.get('university'):
                edu_parts.append(edu['university'])
            
            if edu_parts:
                all_edu_formatted.append('\n'.join(edu_parts))
        
        structured['education_formatted'] = '\n\n'.join(all_edu_formatted)
        
        # Still provide first entry tags for backward compatibility
        structured['edu_years'] = educations[0].get('years', '')
        structured['edu_university'] = educations[0].get('university', '')
        structured['edu_degree'] = educations[0].get('degree', '')
        structured['edu_description'] = educations[0].get('description', '')
    
    return structured


if __name__ == "__main__":
    # Test parsing
    test_work = """
    Year: 2020-Present
    Company: Tech Solutions Sdn Bhd
    Position: Senior Developer
    • Led development of microservices architecture
    • Managed team of 3 junior developers
    • Implemented CI/CD pipelines using Jenkins
    """
    
    test_edu = """
    Bachelor of Computer Science
    University of Malaya (UM)
    2016-2020
    Graduated with Honours
    """
    
    print("Work Experience Parsing:")
    work = parse_work_experience(test_work)
    for w in work:
        print(f"  Years: {w['years']}")
        print(f"  Company: {w['company']}")
        print(f"  Position: {w['position']}")
        print(f"  Description: {w['description']}")
    
    print("\nEducation Parsing:")
    edu = parse_education(test_edu)
    for e in edu:
        print(f"  Years: {e['years']}")
        print(f"  University: {e['university']}")
        print(f"  Degree: {e['degree']}")
        print(f"  Description: {e['description']}")

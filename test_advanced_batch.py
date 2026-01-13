import csv
import os
from docxtpl import DocxTemplate

csv_filepath = 'candidates_advanced.csv'
template_path = 'KLSB_template.docx'
output_dir = 'uploads/cv'

os.makedirs(output_dir, exist_ok=True)

print(f'Generating CVs from: {csv_filepath}')
print('=' * 60)

with open(csv_filepath, mode='r', encoding='utf-8') as file:
    reader = csv.DictReader(file)
    
    for row_num, row in enumerate(reader, 1):
        template = DocxTemplate(template_path)
        
        context = {key: row.get(key, '') for key in [
            'name', 'position', 'dob', 'nationality', 'marital_status', 'address', 
            'phone', 'email', 'linkedin', 'experience_summary', 'education', 
            'working_experience', 'skills', 'professional_training', 'computer_skills', 
            'professional_memberships', 'involvements'
        ]}
        
        context['name'] = context['name'].upper() if context['name'] else ''
        context['position'] = context['position'].upper() if context['position'] else ''
        
        template.render(context)
        
        candidate_name = row.get('name', f'Candidate_{row_num}').lower().replace(' ', '-')
        output_filename = f'KLSB_BATCH_{row_num:03d}_{candidate_name}.docx'
        output_path = os.path.join(output_dir, output_filename)
        
        template.save(output_path)
        print(f'✓ Row {row_num}: {context["name"][:40]} → {output_filename}')

print('=' * 60)
print('Advanced batch generation complete!')

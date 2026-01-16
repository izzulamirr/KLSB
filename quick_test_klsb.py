"""
Quick test to verify KLSB counter and template rendering
"""
from docxtpl import DocxTemplate
import os

# Test counter file
counter_file = "app/uploads/cv/klsb_formatted/.klsb_counter.txt"
if os.path.exists(counter_file):
    with open(counter_file, 'r') as f:
        current = f.read().strip()
    print(f"Current counter value: {current}")
else:
    print("Counter file doesn't exist yet")

# Test template rendering with explicit KLSB number
template = DocxTemplate("KLSB_template_true.docx")

context = {
    'name': 'QUICK TEST',
    'klsb_number': '9876',  # Explicit test value
    'position': 'TEST',
    'email': '',
    'phone': '',
    'dob': '',
    'nationality': '',
    'marital_status': '',
    'address': '',
    'work_years': '',
    'work_company': '',
    'work_position': '',
    'working_experience_formatted': '',
    'education_formatted': ''
}

print(f"Rendering with klsb_number: '{context['klsb_number']}'")
template.render(context)
template.save("QUICK_TEST_KLSB.docx")
print("Saved to QUICK_TEST_KLSB.docx - Open it and check if KLSB_9876 appears!")

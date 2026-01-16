"""
Direct test of KLSB number in template
"""

from docxtpl import DocxTemplate
import os


def test_klsb_rendering():
    """Test if klsb_number renders correctly"""
    
    template_path = "KLSB_template_true.docx"
    
    if not os.path.exists(template_path):
        print(f"❌ Template not found: {template_path}")
        return
    
    print(f"\n{'='*70}")
    print(f"TESTING KLSB NUMBER RENDERING")
    print(f"{'='*70}\n")
    
    template = DocxTemplate(template_path)
    
    # Test context with KLSB number
    context = {
        'name': 'TEST USER',
        'klsb_number': '9999',
        'position': 'TEST POSITION',
        'email': 'test@test.com',
        'phone': '123456',
        'dob': '01 JAN 2000',
        'nationality': 'MALAYSIAN',
        'marital_status': 'SINGLE',
        'address': 'Test Address',
        'working_experience_formatted': '',
        'education_formatted': '',
        'work_years': '',
        'work_company': '',
        'work_position': ''
    }
    
    print(f"Context klsb_number: '{context['klsb_number']}'")
    print(f"Type: {type(context['klsb_number'])}")
    
    # Render
    template.render(context)
    
    # Save
    output = "test_klsb_direct.docx"
    template.save(output)
    
    print(f"\n✓ Saved to: {output}")
    print(f"Open this file and check if KLSB_9999 appears in the header!")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    test_klsb_rendering()

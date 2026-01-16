"""Test KLSB template rendering with klsb_number"""

from docxtpl import DocxTemplate
import os

def test_template():
    template_path = "KLSB_template_true.docx"
    
    if not os.path.exists(template_path):
        print(f"❌ Template not found: {template_path}")
        return
    
    print(f"\n{'='*70}")
    print(f"TESTING KLSB TEMPLATE RENDERING")
    print(f"{'='*70}\n")
    
    # Load template
    template = DocxTemplate(template_path)
    
    # Create test context
    context = {
        'name': 'TEST USER',
        'position': 'TEST POSITION',
        'klsb_number': '4130',
        'email': 'test@example.com',
        'phone': '+60123456789',
        'dob': '01 JAN 1990',
        'nationality': 'MALAYSIAN',
        'marital_status': 'SINGLE',
        'address': 'Test Address',
        'education_formatted': 'Test Education',
        'working_experience_formatted': 'Test Experience'
    }
    
    print("Context being passed to template:")
    for key, value in context.items():
        print(f"  {key}: {value}")
    
    # Render template
    print("\nRendering template...")
    template.render(context)
    
    # Save test output
    output_path = "test_klsb_output.docx"
    template.save(output_path)
    
    print(f"\n✅ Template rendered successfully!")
    print(f"Output saved to: {output_path}")
    print(f"\nPlease open {output_path} and check if KLSB_4130 appears in the header.")
    print(f"{'='*70}\n")

if __name__ == "__main__":
    test_template()

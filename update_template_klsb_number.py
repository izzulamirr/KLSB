"""
Script to update KLSB_template_true.docx to replace KLSB_0 with {{klsb_number}}
This allows the template to use dynamic KLSB numbering.
"""
from docx import Document
import sys

def replace_text_in_paragraph(paragraph, old_text, new_text):
    """Replace text in a paragraph, handling text that spans multiple runs."""
    if old_text in paragraph.text:
        # Get the full text
        full_text = paragraph.text
        
        # Replace the text
        new_full_text = full_text.replace(old_text, new_text)
        
        # Clear all runs
        for run in paragraph.runs:
            run.text = ''
        
        # Set the new text in the first run (or create one if needed)
        if paragraph.runs:
            paragraph.runs[0].text = new_full_text
        else:
            paragraph.add_run(new_full_text)
        
        return True
    return False

def update_klsb_template():
    template_path = "KLSB_template_true.docx"
    
    try:
        # Load the document
        doc = Document(template_path)
        
        replacements = 0
        
        # Replace in paragraphs
        for paragraph in doc.paragraphs:
            if replace_text_in_paragraph(paragraph, 'KLSB_0', '{{klsb_number}}'):
                print(f"✓ Replaced in paragraph: {paragraph.text[:100]}")
                replacements += 1
        
        # Replace in tables
        for table in doc.tables:
            for row in table.rows:
                for cell in row.cells:
                    for paragraph in cell.paragraphs:
                        if replace_text_in_paragraph(paragraph, 'KLSB_0', '{{klsb_number}}'):
                            print(f"✓ Replaced in table cell: {paragraph.text[:100]}")
                            replacements += 1
        
        # Replace in headers
        for section in doc.sections:
            header = section.header
            for paragraph in header.paragraphs:
                if replace_text_in_paragraph(paragraph, 'KLSB_0', '{{klsb_number}}'):
                    print(f"✓ Replaced in header: {paragraph.text[:100]}")
                    replacements += 1
        
        # Replace in footers
        for section in doc.sections:
            footer = section.footer
            for paragraph in footer.paragraphs:
                if replace_text_in_paragraph(paragraph, 'KLSB_0', '{{klsb_number}}'):
                    print(f"✓ Replaced in footer: {paragraph.text[:100]}")
                    replacements += 1
        
        if replacements > 0:
            # Save the updated document
            backup_path = "KLSB_template_true_backup.docx"
            print(f"\nCreating backup: {backup_path}")
            doc.save(backup_path)
            
            print(f"Saving updated template: {template_path}")
            doc.save(template_path)
            
            print(f"\n✅ Success! Made {replacements} replacements.")
            print("KLSB_0 has been replaced with {{klsb_number}}")
        else:
            print("\n⚠️  No instances of 'KLSB_0' found in the template.")
            print("Searching for similar patterns...")
            
            # Search for any KLSB patterns
            for paragraph in doc.paragraphs:
                if 'KLSB' in paragraph.text.upper():
                    print(f"Found KLSB mention: {paragraph.text[:150]}")
        
    except FileNotFoundError:
        print(f"❌ Error: Template file '{template_path}' not found!")
        print("Make sure you're running this script from the KLSB project directory.")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    update_klsb_template()

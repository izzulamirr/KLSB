"""Inspect KLSB template for variable names"""

from docx import Document
from zipfile import ZipFile
import os
import re

def inspect_template():
    template_path = "KLSB_template_true.docx"
    
    if not os.path.exists(template_path):
        print(f"❌ Template not found: {template_path}")
        return
    
    print(f"\n{'='*70}")
    print(f"INSPECTING TEMPLATE VARIABLES")
    print(f"{'='*70}\n")
    
    # Extract and read the document.xml to find all Jinja variables
    with ZipFile(template_path, 'r') as docx:
        # Read header files
        for name in docx.namelist():
            if 'header' in name.lower() and name.endswith('.xml'):
                print(f"\n--- {name} ---")
                content = docx.read(name).decode('utf-8')
                
                # Find all {{...}} patterns
                variables = re.findall(r'\{\{([^}]+)\}\}', content)
                if variables:
                    print("Variables found:")
                    for var in set(variables):
                        print(f"  {{{{ {var.strip()} }}}}")
                        
                # Check for klsb_number specifically
                if 'klsb' in content.lower():
                    print("\nKLSB mentions found in XML:")
                    # Find context around KLSB
                    for match in re.finditer(r'.{0,50}klsb.{0,50}', content, re.IGNORECASE):
                        print(f"  ...{match.group()}...")

if __name__ == "__main__":
    inspect_template()

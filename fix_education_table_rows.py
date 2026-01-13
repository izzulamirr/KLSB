"""
Fix education table to create separate rows for each entry
"""

from docx import Document
import os


def fix_education_table_rows():
    """Fix education table to use proper row iteration"""
    
    template_path = "KLSB_template_true.docx"
    
    if not os.path.exists(template_path):
        print(f"❌ Template not found: {template_path}")
        return
    
    print(f"\n{'='*70}")
    print(f"FIXING EDUCATION TABLE ROW ITERATION")
    print(f"{'='*70}\n")
    
    doc = Document(template_path)
    
    # Find education table (Table 1)
    if len(doc.tables) < 2:
        print(f"❌ Not enough tables in template")
        return
    
    edu_table = doc.tables[1]
    
    print(f"Found education table with {len(edu_table.rows)} rows")
    
    # Find the row with template tags
    tag_row_idx = None
    for idx, row in enumerate(edu_table.rows):
        row_text = ' '.join(cell.text for cell in row.cells)
        if 'education_table' in row_text or '{%' in row_text:
            tag_row_idx = idx
            print(f"  → Found tag row at index {idx}")
            break
    
    if tag_row_idx is None:
        print(f"❌ Could not find template tag row")
        return
    
    # Update the tag row to use {%tr %} for row iteration
    # Both tags must be in the first cell
    tag_row = edu_table.rows[tag_row_idx]
    
    # Clear and update Period cell (contains both tr for and variable)
    period_cell = tag_row.cells[0]
    period_cell.text = ""
    para = period_cell.paragraphs[0]
    para.text = "{%tr for edu in education_table %}{{edu.period}}"
    
    # Clear and update Description cell (contains variable and tr endfor)
    desc_cell = tag_row.cells[1]
    desc_cell.text = ""
    para = desc_cell.paragraphs[0]
    # Add both the variable and the endfor tag
    run1 = para.add_run("{{edu.description}}")
    run2 = para.add_run("{%tr endfor %}")
    
    print(f"  ✓ Updated row iteration tags")
    print(f"    Period cell: {{{{%tr for edu in education_table %}}}}{{{{edu.period}}}}")
    print(f"    Description cell: {{{{edu.description}}}}{{{{%tr endfor %}}}}")
    
    # Save
    doc.save(template_path)
    
    print(f"\n✓ Template updated!")
    print(f"\nEach education entry will now appear on a separate row")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    fix_education_table_rows()

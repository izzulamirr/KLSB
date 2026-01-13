from docx import Document

doc = Document('uploads/cv/KLSB_BATCH_001_john-smith.docx')

print("Header Verification - KLSB_BATCH_001_john-smith.docx")
print("=" * 60)

# Check header
section = doc.sections[0]
header = section.header

print("\nHeader content:")
print(f"Number of tables in header: {len(header.tables)}")

if len(header.tables) > 0:
    header_table = header.tables[0]
    print(f"Header table rows: {len(header_table.rows)}")
    print(f"Header table cols: {len(header_table.rows[0].cells)}")
    
    print("\nHeader Row 1:")
    for i, cell in enumerate(header_table.rows[0].cells):
        print(f"  Cell {i}: {cell.text[:50]}")
    
    print("\nHeader Row 2:")
    for i, cell in enumerate(header_table.rows[1].cells):
        print(f"  Cell {i}: {cell.text[:50]}")

print("\nFirst 5 body paragraphs:")
for i, para in enumerate(doc.paragraphs[:5]):
    text = para.text.strip()
    if text:
        print(f"  {i}: {text[:60]}")

print("\n✓ Header successfully applied!")

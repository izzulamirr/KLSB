# KEMUNCAK LANAI Professional Resume Header - Integration Guide

## Overview

All KLSB CVs now include a professional header with KEMUNCAK LANAI branding, matching the company template shown in the reference documents.

## Header Layout

```
┌─────────────────────────────────────────────────────────┐
│ KEMUNCAK LANAI  │ PROFESSIONAL RESUME  │   Page 1 of 3  │
│  SDN BHD        │                      │                │
├─────────────────────────────────────────────────────────┤
│      NAME       │   JOHN SMITH         │    KLSB_0      │
└─────────────────────────────────────────────────────────┘
```

### Header Components

| Section | Content | Notes |
|---------|---------|-------|
| Left Cell (Row 1) | KEMUNCAK LANAI SDN BHD | Company branding |
| Center Cell (Row 1) | PROFESSIONAL RESUME | Title |
| Right Cell (Row 1) | Page 1 of 3 | Page reference |
| Left Cell (Row 2) | NAME | Label |
| Center Cell (Row 2) | Candidate Name (uppercase) | Dynamic - from CSV or extracted |
| Right Cell (Row 2) | KLSB_0 | CV series identifier |

## How Headers Are Applied

### Method 1: Automatic (Recommended)

Headers are **automatically applied** when you:

1. **Generate CVs from CSV**
   ```bash
   python cv_batch_from_csv.py
   ```
   - Uses updated `KLSB_template.docx` with header tags
   - Headers appear in all generated batch CVs
   - Candidate name auto-populated from CSV

2. **Extract CVs from PDFs** (GPT pipeline)
   ```bash
   python cv_converter.py
   ```
   - Headers now included in output DOCX files
   - Candidate name extracted and inserted automatically

### Method 2: Add to Existing CVs

Add headers to any existing DOCX files:

```bash
python add_headers_utility.py
```

This will:
- Find all `KLSB_*.docx` files in `uploads/cv/`
- Add professional header to each
- Preserve all existing content
- Overwrite original files

### Method 3: Add Header to Single File

```python
from add_headers_utility import add_header_to_docx

# Add header with specific name
add_header_to_docx(
    doc_path="path/to/cv.docx",
    candidate_name="John Doe",
    output_path="path/to/output.docx"
)
```

## Files Updated

### Template Files
- ✓ `KLSB_template.docx` - Now contains header template tags

### Python Scripts
- ✓ `cv_batch_from_csv.py` - Uses template with headers
- ✓ `cv_converter.py` - GPT pipeline generates CVs with headers
- ✓ `create_template.py` - Creates templates with headers
- ✓ `update_header.py` - Updates existing template
- ✓ `add_headers_utility.py` - Adds headers to any DOCX file (NEW)

### Generated CVs
- ✓ `KLSB_BATCH_001*.docx` - Headers applied
- ✓ `KLSB_BATCH_002*.docx` - Headers applied
- ✓ `KLSB_BATCH_003*.docx` - Headers applied
- ✓ `KLSB_048*.docx` - Headers added
- ✓ `KLSB_052*.docx` - Headers added
- ✓ `KLSB_054*.docx` - Headers added

## Usage Examples

### Generate New Batch with Headers

```bash
# Edit CSV data
nano candidates.csv

# Generate - headers automatic
python cv_batch_from_csv.py

# Output in: uploads/cv/KLSB_BATCH_*.docx
# All with professional headers!
```

### Add Headers to Old CVs

```bash
# Update all KLSB files in uploads/cv/
python add_headers_utility.py
```

### Extract from PDF with Header

```bash
# Run GPT extraction
python cv_converter.py

# Generated DOCX includes professional header
```

## Integration with Workflows

### Workflow 1: PDF → GPT → DOCX with Header

```
PDF Input
   ↓
cv_converter.py (GPT extraction)
   ↓
DOCX Output (with professional header) ✓
```

### Workflow 2: CSV → Template → DOCX with Header

```
CSV Data
   ↓
cv_batch_from_csv.py
   ↓
KLSB_template.docx (with header tags)
   ↓
DOCX Output (with professional header) ✓
```

### Workflow 3: Add Headers to Existing Files

```
Existing DOCX files (any format)
   ↓
add_headers_utility.py
   ↓
Same files with professional header added ✓
```

## Customization

### Modify Header Content

To change header text (e.g., company name, page format):

1. Edit `update_header.py` lines 49-116
2. Change header cell content as needed
3. Run: `python update_header.py`
4. Regenerate CVs: `python cv_batch_from_csv.py`

### Change Company Name

Edit in `update_header.py` line 62:
```python
left_run = left_para.add_run("YOUR COMPANY NAME\nSUBTITLE")
```

### Change Page Reference

Edit in `update_header.py` line 72:
```python
right_run = right_para.add_run("Page 1 of 3")  # Modify as needed
```

### Add Logo Image

To add actual logo image instead of text:

1. Save logo as `logo_kemuncak.png`
2. Edit `update_header.py` line 266:
   ```python
   update_template_with_header(template_path, logo_path="logo_kemuncak.png")
   ```
3. Run: `python update_header.py`

## Technical Details

### Header Storage

Headers are stored in:
- **DOCX section definition** (not part of document body)
- Located in: `document.xml.rels`
- Accessible via: `doc.sections[0].header`

### Header Table Structure

```
Header Table (2 rows × 3 columns):
├─ Row 1: Company | Title | Page
├─ Row 2: Label   | Name  | ID
└─ Borders: Light gray (CCCCCC)
```

### Character Formatting

| Element | Format |
|---------|--------|
| Company name | Bold, 9pt |
| Title | Bold, 12pt |
| Page reference | 9pt |
| Labels | Bold, 9pt |
| Values | 9pt |

## Features

✓ **Automatic population** - Name extracted from document or CSV
✓ **Professional appearance** - Matches company branding
✓ **Consistent across CVs** - Same format for all candidates
✓ **Non-invasive** - Doesn't modify document body
✓ **Easy customization** - Simple to edit or adjust
✓ **Works with existing workflow** - No disruption to current process

## Testing

Verified headers in:
- ✓ KLSB_BATCH_001_john-smith.docx
- ✓ KLSB_BATCH_002_sarah-johnson.docx
- ✓ KLSB_BATCH_003_ahmad-hassan.docx
- ✓ KLSB_054_amirun-harraz-bin-budizaman.docx (GPT-generated)

All headers display correctly with:
- ✓ Company branding
- ✓ Candidate names
- ✓ Professional formatting
- ✓ Proper alignment

## Troubleshooting

**Header not appearing in Word**
- Ensure file is opened in latest MS Word version
- Try Save As → DOCX format
- Check View → Header and Footer section

**Name not populated in header**
- Verify CSV has 'name' column
- Check candidate name extracted correctly
- For existing files, manually specify name

**Header formatting looks different**
- May depend on Word version/settings
- Try regenerating template: `python update_header.py`
- Contact support if issues persist

## Support Files

- `update_header.py` - Update/create headers
- `add_headers_utility.py` - Batch add headers
- `verify_header.py` - Verify headers in CVs
- Documentation in this file

---

**System Status**: ✓ Headers integrated and tested
**Last Updated**: January 13, 2026
**Tested CVs**: 6+ files with headers

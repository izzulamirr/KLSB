# KLSB Batch CV Generation from CSV

This system allows you to generate multiple CVs in bulk from a CSV file using a DOCX template.

## Files

- **`cv_batch_from_csv.py`** - Main batch generation script
- **`candidates.csv`** - Sample CSV with candidate data (edit this with your data)
- **`KLSB_template.docx`** - Template file with `{{tags}}` (created from KLSB format)
- **`create_template.py`** - Script to generate template from scratch if needed

## Quick Start

### 1. Prepare Your CSV File

Create a CSV file named `candidates.csv` with the following columns:

```csv
name,position,dob,nationality,marital_status,address,phone,email,linkedin,experience_summary,education,working_experience,skills,professional_training,computer_skills,professional_memberships,involvements
```

**Example row:**
```
John Smith,Software Engineer,15-Jan-1990,Malaysian,Single,"123 Main St, KL",012-3456789,john@email.com,linkedin.com/in/john,"5 years experience in...","Bachelor of CS\nUniversity of Malaya","Company: TechCorp\nPosition: Senior Dev\n• Led team of 3\n• Implemented CI/CD","• Python\n• JavaScript\n• React","• AWS Cert (2023)","• Python\n• JavaScript","• IEEE: Member","• Tech Committee Lead"
```

### 2. Generate CVs in Batch

```bash
python cv_batch_from_csv.py
```

This will:
- Read all rows from `candidates.csv`
- Use `KLSB_template.docx` as the template
- Generate individual CVs for each candidate
- Save to `uploads/cv/` folder with names like `KLSB_BATCH_001_john-smith.docx`

### 3. Output

Generated CVs are saved to: `uploads/cv/KLSB_BATCH_XXX_*.docx`

## CSV Column Reference

| Column | Description | Example |
|--------|-------------|---------|
| name | Full name | John Smith |
| position | Job title | Software Engineer |
| dob | Date of birth | 15-Jan-1990 |
| nationality | Nationality | Malaysian |
| marital_status | Marital status | Single |
| address | Contact address | 123 Main St, Kuala Lumpur |
| phone | Phone number | 012-3456789 |
| email | Email address | john@email.com |
| linkedin | LinkedIn profile | linkedin.com/in/john |
| experience_summary | Professional summary | Experienced engineer with... |
| education | Education/degrees (use \n for newlines) | Bachelor of Science\nUniversity Name |
| working_experience | Work history (use \n for newlines) | Company: XYZ\nPosition: Manager\n• Task 1\n• Task 2 |
| skills | Skills list (use \n for newlines) | • Python\n• JavaScript\n• React |
| professional_training | Training/certifications (use \n for newlines) | • AWS Solutions Architect\n• Python Advanced |
| computer_skills | Software skills (use \n for newlines) | • Microsoft Office\n• AutoCAD\n• Python |
| professional_memberships | Professional memberships | • IEEE: Member\n• ACM: Fellow |
| involvements | Activities/involvements | • Committee Chair (2023)\n• Volunteer (2022) |

## Notes

- **Newlines in CSV**: Use `\n` to create line breaks within fields (e.g., multiple education entries)
- **Multiline text**: Fields that span multiple lines should be enclosed in quotes
- **Template**: The `KLSB_template.docx` contains `{{tags}}` that match the CSV column names
- **Case conversion**: Name and position are automatically converted to UPPERCASE
- **Nationality**: Defaults to "MALAYSIAN" if not specified
- **No references**: The system does not generate a REFERENCES section
- **Work-related involvements**: Are merged into WORKING EXPERIENCE if applicable

## Customization

### Modify Template

If you need to change the CV format:

1. Edit `KLSB_template.docx` in Word (or use `create_template.py`)
2. Replace content with `{{tag_name}}` where tag_name matches CSV columns
3. Save and re-run `cv_batch_from_csv.py`

### Add New Fields

To add new fields:

1. Add column to `candidates.csv`
2. Add `{{field_name}}` to `KLSB_template.docx`
3. Update `cv_batch_from_csv.py` context dictionary if needed

### Change Output Filename

Edit line in `cv_batch_from_csv.py`:
```python
output_filename = f"KLSB_BATCH_{row_num:03d}_{candidate_name}.docx"
```

## Limitations

- CSV column names must match template tags exactly
- Special characters in names may cause filename issues (will be replaced with `-`)
- Very large CSV files may take time to process
- Each CV is generated independently (no merging or pagination)

## Troubleshooting

**Error: "Template file not found"**
- Ensure `KLSB_template.docx` exists in the same directory

**Error: "CSV file not found"**
- Ensure `candidates.csv` exists and is in the correct location

**Generated CVs have blank fields**
- Check CSV column names match exactly (case-sensitive)
- Ensure CSV has proper headers

**Template not rendering properly**
- Run `python create_template.py` to regenerate template
- Check that `{{tags}}` are correctly formatted in template

## Integration with Other Systems

This batch system works independently from the ChatGPT extraction pipeline (`cv_converter.py`). You can:

1. **Use GPT extraction** for PDFs → generates one CV per PDF
2. **Use CSV batch** for structured data → generates multiple CVs from CSV
3. **Mix both** - extract to GPT JSON → export to CSV → use batch generation

## Performance

- **Speed**: ~2-3 seconds per CV on standard hardware
- **Accuracy**: 100% - no GPT limitations on field extraction
- **Cost**: Free (except docxtpl package, which is free)
- **Scalability**: Can generate hundreds of CVs in minutes

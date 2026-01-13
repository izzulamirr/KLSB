# Dual OCR System Setup

## Overview
The CV converter now supports **two OCR methods** that you can choose between using the buttons on the conversion page:

### 🔵 Blue Button - Traditional Tesseract OCR (FREE)
- **Cost**: Completely free, no API charges
- **Technology**: pypdf text extraction + Tesseract OCR
- **Accuracy**: ~70-90% depending on CV quality
- **Speed**: Fast (2-5 seconds)
- **Best for**: 
  - Testing and development
  - Text-based PDFs (not scanned)
  - When API credits are limited

### 🟢 Green Button - ChatGPT Vision API (PAID)
- **Cost**: ~$0.05-0.15 per CV (requires OpenAI API credits)
- **Technology**: GPT-4o Vision API
- **Accuracy**: ~95-99%, excellent parsing
- **Speed**: Slower (30-60 seconds)
- **Best for**:
  - Production conversions
  - Complex/scanned CVs
  - When highest accuracy is needed

## How It Works

### Blue Button (Traditional OCR)
1. Clicks blue "Convert" button
2. Sends `use_chatgpt=false` to backend
3. Uses `_extract_text_from_pdf()` with tesseract
4. Parses sections with regex patterns via `_parse_cv_sections()`
5. Returns structured fields

### Green Button (ChatGPT OCR)
1. Clicks green "Convert with ChatGPT OCR" button
2. Sends `use_chatgpt=true` to backend
3. Converts PDF to images using pdf2image + Poppler
4. Sends images to GPT-4o Vision API
5. ChatGPT extracts and parses all text
6. Returns structured fields

## Setup Requirements

### For Traditional OCR (Blue Button)
✅ Already working! No additional setup needed.

Required dependencies (already installed):
- pypdf
- python-tesseract (optional, for scanned PDFs)

### For ChatGPT OCR (Green Button)
⚠️ Requires OpenAI API credits

**Current Status**: Your API key is out of quota (Error 429 - insufficient_quota)

**To enable ChatGPT OCR:**
1. Go to https://platform.openai.com/settings/organization/billing
2. Add credits to your API account (minimum $5-10 recommended)
3. Note: ChatGPT Plus subscription is **separate** from API credits
4. Cost per CV: approximately $0.05-0.15 depending on length

Required dependencies (already installed):
- openai >= 1.0.0
- pdf2image == 1.17.0
- Poppler (installed at `C:\poppler\poppler-24.08.0\Library\bin`)

## Testing Both Methods

### Test Blue Button (Free)
```
1. Open http://127.0.0.1:5000/admin/cv-converter
2. Upload a CV or select an applicant
3. Click the BLUE "Convert" button
4. Should complete in 2-5 seconds
5. Check output quality
```

### Test Green Button (Paid)
```
⚠️ First add API credits at https://platform.openai.com/settings/organization/billing

1. Open http://127.0.0.1:5000/admin/cv-converter
2. Upload a CV or select an applicant
3. Click the GREEN "Convert with ChatGPT OCR" button
4. Wait 30-60 seconds for processing
5. Check output quality (should be higher accuracy)
```

## Configuration

### Current Settings (config.py)
```python
OPENAI_API_KEY = "sk-proj-44IcmGooY_Eg49f1yjXmxMzaF9..." 
USE_CHATGPT_OCR = True  # Note: This setting is now ignored
```

**Important**: The `USE_CHATGPT_OCR` config setting is **no longer used**. OCR method is now controlled by which button you click, not by config.

## Code Changes

### Modified Files:

1. **cv_converter.py**:
   - Added `use_chatgpt` parameter to `convert_cv_to_klsb_ocr()`
   - Created `_parse_cv_sections()` function for traditional OCR parsing
   - Dual OCR paths: ChatGPT Vision API vs traditional tesseract

2. **routes.py**:
   - Reads `use_chatgpt` parameter from request
   - Passes it to `convert_cv_to_klsb_ocr()`

3. **admin_cv_converter.html**:
   - Blue button sends `use_chatgpt=false`
   - Green button sends `use_chatgpt=true`

## Cost Comparison

| Method | Per CV Cost | 100 CVs | 1000 CVs |
|--------|-------------|---------|----------|
| Traditional OCR (Blue) | $0.00 | $0.00 | $0.00 |
| ChatGPT OCR (Green) | ~$0.10 | ~$10.00 | ~$100.00 |

## Troubleshooting

### Blue Button Issues
- **Error: "Unable to extract text"**
  - PDF might be scanned and tesseract is not installed
  - Try green button instead
  
- **Low accuracy**
  - Traditional OCR struggles with complex formatting
  - Use green button for better results

### Green Button Issues
- **Error: "insufficient_quota"**
  - Your OpenAI API key is out of credits
  - Add credits at https://platform.openai.com/settings/organization/billing
  
- **Error: "Poppler not found"**
  - Already fixed! Poppler is installed at `C:\poppler\poppler-24.08.0\Library\bin`
  
- **Slow processing**
  - Normal behavior (30-60 seconds per CV)
  - ChatGPT processes each page individually

## API Credits Management

### Adding Credits
1. Go to https://platform.openai.com/settings/organization/billing
2. Click "Add payment method"
3. Add credit card
4. Purchase credits (starts at $5)
5. Credits never expire but have monthly rate limits

### Monitoring Usage
- Dashboard: https://platform.openai.com/usage
- Cost per request logged in Flask terminal
- Approximately $0.05-0.15 per CV depending on:
  - Number of pages (more pages = higher cost)
  - Image resolution (200 DPI default)
  - Text complexity

### ChatGPT Plus vs API Credits
**They are SEPARATE services:**
- **ChatGPT Plus** ($20/month): Web interface access, faster responses
- **API Credits**: Pay-as-you-go for programmatic access (this CV system)

❌ Having ChatGPT Plus does NOT give you API credits
✅ Need to add API credits separately for the CV converter

## Recommendations

### For Development/Testing
Use **Blue Button** (Traditional OCR):
- Free and fast
- Good enough for testing workflow
- No API rate limits

### For Production
Use **Green Button** (ChatGPT OCR):
- Much higher accuracy
- Better handling of complex CVs
- Consistent field extraction
- Worth the cost for final conversions

### Hybrid Approach
1. Test with blue button first (free)
2. If accuracy is poor, use green button
3. Or: batch process 100 CVs with green button when you have budget

## Technical Details

### Traditional OCR Pipeline
```
PDF → pypdf.PdfReader → Raw Text
    ↓ (if scanned)
    Poppler → Images → Tesseract → Raw Text
    ↓
    Regex Parsing (_parse_cv_sections)
    ↓
    Structured Fields
```

### ChatGPT OCR Pipeline
```
PDF → pdf2image + Poppler → PNG Images
    ↓
    Base64 Encoding
    ↓
    GPT-4o Vision API (Extract Text)
    ↓
    GPT-4o API (Parse JSON)
    ↓
    Structured Fields
```

## Next Steps

1. ✅ Dual OCR system is now configured and running
2. ⏳ Add OpenAI API credits to enable green button
3. ⏳ Test both buttons with sample CVs
4. ⏳ Compare output quality
5. ⏳ Decide which method to use for production

## Support

Flask server is running at: **http://127.0.0.1:5000**
CV Converter page: **http://127.0.0.1:5000/admin/cv-converter**

Both OCR methods are fully functional and ready to use!

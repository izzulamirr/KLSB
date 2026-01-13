"""Test script to convert a CV using GPT-4.1 to KLSB format."""

import os
import sys

# Add app directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.cv_converter import convert_cv_to_klsb_ocr

def test_conversion():
    """Test CV conversion with GPT-4.1."""
    
    # Input CV file (choose any from app/static/CVS)
    input_cv = r"d:\KLSB\app\static\CVS\Amirun_Harraz_Resume_PNG.pdf"
    
    # Check if file exists
    if not os.path.exists(input_cv):
        print(f"❌ Error: CV file not found at {input_cv}")
        print("\nAvailable CVs:")
        uploads_dir = r"d:\KLSB\uploads"
        for f in os.listdir(uploads_dir):
            if f.endswith('.pdf'):
                print(f"  - {f}")
        return
    
    # Output directory
    output_dir = r"d:\KLSB\uploads\cv"
    os.makedirs(output_dir, exist_ok=True)
    
    # Logo path
    logo_path = r"d:\KLSB\app\static\img\logo.png"
    
    print("=" * 60)
    print("CV CONVERSION TEST - GPT-4.1")
    print("=" * 60)
    print(f"\nInput CV: {os.path.basename(input_cv)}")
    print(f"Output directory: {output_dir}")
    print(f"\nStarting conversion with GPT-4.1...\n")
    
    try:
        # Convert using ChatGPT (green button behavior)
        # Generate DOCX first
        docx_path, fields = convert_cv_to_klsb_ocr(
            source_path=input_cv,
            output_dir=output_dir,
            use_chatgpt=True,  # Use GPT-4.1 extraction
            output_format="docx"
        )
        
        # Generate PDF
        pdf_path, _ = convert_cv_to_klsb_ocr(
            source_path=input_cv,
            output_dir=output_dir,
            use_chatgpt=True,  # Use GPT-4.1 extraction
            output_format="pdf"
        )
        
        result = {
            'pdf_path': pdf_path,
            'docx_path': docx_path,
            'cv_number': os.path.basename(docx_path).split('_')[0],
            'name': fields.get('name', 'N/A')
        }
        
        print("\n" + "=" * 60)
        print("✅ CONVERSION SUCCESSFUL!")
        print("=" * 60)
        print(f"\nGenerated files:")
        print(f"  📄 PDF: {result['pdf_path']}")
        print(f"  📝 DOCX: {result['docx_path']}")
        print(f"\nCV Number: {result['cv_number']}")
        print(f"Candidate: {result.get('name', 'N/A')}")
        
        # Display extracted structured JSON data
        print("\n" + "=" * 60)
        print("STRUCTURED DATA (GPT EXTRACTION)")
        print("=" * 60)
        import json
        display_fields = {k: v for k, v in fields.items() if k != '_token_usage' and k != 'full_text'}
        print(json.dumps(display_fields, indent=2, ensure_ascii=False))
        
        # Display actual token usage if available
        if fields and '_token_usage' in fields:
            usage = fields['_token_usage']
            input_tokens = usage['input_tokens']
            output_tokens = usage['output_tokens']
            total_tokens = usage['total_tokens']
            
            # Calculate actual costs (GPT-4.1 pricing)
            input_cost = (input_tokens / 1_000_000) * 2.00
            output_cost = (output_tokens / 1_000_000) * 8.00
            total_cost_usd = input_cost + output_cost
            total_cost_rm = total_cost_usd * 4.35  # Approximate USD to RM conversion
            
            print("\n" + "=" * 60)
            print("ACTUAL TOKEN USAGE (GPT-4.1)")
            print("=" * 60)
            print(f"Input tokens:  {input_tokens:,}")
            print(f"Output tokens: {output_tokens:,}")
            print(f"Total tokens:  {total_tokens:,}")
            print("\nCost breakdown:")
            print(f"  Input:  {input_tokens:,} × $2.00/1M = ${input_cost:.6f}")
            print(f"  Output: {output_tokens:,} × $8.00/1M = ${output_cost:.6f}")
            print(f"  Total: ${total_cost_usd:.6f} (≈RM {total_cost_rm:.4f})")
            print(f"\nWith RM 500 budget: ~{int(500 / total_cost_rm):,} CVs capacity")
        else:
            print("\n" + "=" * 60)
            print("COST ESTIMATE (GPT-4.1) - CHATGPT DOES ALL FORMATTING")
            print("=" * 60)
            print("Estimated tokens used:")
            print("  Vision extraction (3 pages × 500): ~1,500 tokens input")
            print("  JSON parsing input: ~1,500 tokens")
            print("  JSON parsing output (formatted): ~3,000 tokens")
            print("  Total input: ~3,000 tokens")
            print("  Total output: ~3,000 tokens")
            print("\nCost breakdown:")
            print("  Input:  3,000 × $2.00/1M = $0.006")
            print("  Output: 3,000 × $8.00/1M = $0.024")
            print("  Total: ~$0.030 per CV (≈RM 0.13)")
            print("\nWith RM 500 budget: ~3,850 CVs capacity")
            print("(ChatGPT now handles all formatting - simpler code!)")
        
    except Exception as e:
        print("\n" + "=" * 60)
        print("❌ CONVERSION FAILED")
        print("=" * 60)
        print(f"\nError: {str(e)}")
        import traceback
        print("\nFull traceback:")
        traceback.print_exc()

if __name__ == "__main__":
    test_conversion()

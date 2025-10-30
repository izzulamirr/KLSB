from app import create_app, db
from app.models import Applicant

app = create_app()

with app.app_context():
    try:
        # Try to query applicants
        applicants = Applicant.query.order_by(Applicant.created_at.desc()).all()
        
        print(f"✅ Successfully queried {len(applicants)} applicants!")
        print()
        
        for i, applicant in enumerate(applicants, 1):
            print(f"Applicant #{i}:")
            print(f"  ID: {applicant.id}")
            print(f"  Name: {applicant.full_name}")
            print(f"  Email: {applicant.email}")
            print(f"  Position: {applicant.position}")
            print(f"  Availability: {applicant.availability}")
            print(f"  Filename: {applicant.filename}")
            print(f"  File Path: {applicant.file_path}")
            print(f"  Created: {applicant.created_at}")
            print()
            
    except Exception as e:
        print(f"❌ Error querying applicants: {e}")
        import traceback
        traceback.print_exc()

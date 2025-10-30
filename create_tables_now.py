import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import JobListing

app = create_app()

with app.app_context():
    try:
        # Create job_listings table
        db.create_all()
        print("✅ Database tables created successfully!")
        
        # Verify table exists
        from sqlalchemy import inspect
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        print(f"\n📊 Tables in database: {', '.join(tables)}")
        
        if 'job_listings' in tables:
            print("\n✅ job_listings table exists!")
            
            # Check if there are any jobs
            count = JobListing.query.count()
            print(f"📋 Total job listings: {count}")
            
            if count > 0:
                jobs = JobListing.query.all()
                print("\nExisting jobs:")
                for job in jobs:
                    print(f"  - {job.title} ({job.department}) - Active: {job.is_active}")
        else:
            print("\n❌ job_listings table NOT created!")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

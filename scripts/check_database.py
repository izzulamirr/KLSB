import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import Applicant, Proposal, JobListing

app = create_app()

with app.app_context():
    try:
        # Test database connection
        db.session.execute(db.text("SELECT 1"))
        print("✅ Database connection successful!")
        
        # Check if tables exist
        tables = db.session.execute(db.text("SHOW TABLES")).fetchall()
        print(f"\n📊 Tables in database '{app.config['DB_NAME']}':")
        if tables:
            for table in tables:
                print(f"  - {table[0]}")
        else:
            print("  (No tables found)")
        
        # Check Applicants table
        try:
            applicant_count = Applicant.query.count()
            print(f"\n👥 Applicants table: {applicant_count} records")
            if applicant_count > 0:
                all_applicants = Applicant.query.all()
                for app in all_applicants:
                    print(f"  - {app.full_name} | {app.position} | {app.email}")
            else:
                print("  ⚠️ No applicants in database")
        except Exception as e:
            print(f"\n❌ Applicants table error: {e}")
        
        # Check Proposals table
        try:
            proposal_count = Proposal.query.count()
            print(f"\n📋 Proposals (dproposal) table: {proposal_count} records")
            if proposal_count > 0:
                all_proposals = Proposal.query.all()
                for prop in all_proposals:
                    print(f"  - {prop.company_name} | {prop.service} | {prop.client_email}")
            else:
                print("  ⚠️ No proposals in database")
        except Exception as e:
            print(f"\n❌ Proposals table error: {e}")
        
        # Check Job Listings table
        try:
            job_count = JobListing.query.count()
            print(f"\n💼 Job Listings table: {job_count} records")
            if job_count > 0:
                all_jobs = JobListing.query.all()
                for job in all_jobs:
                    print(f"  - {job.title} | {job.department} | Active: {job.is_active}")
            else:
                print("  ⚠️ No job listings in database")
        except Exception as e:
            print(f"\n❌ Job Listings table error: {e}")
            
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        print("\nMake sure:")
        print("  1. MySQL server is running (XAMPP/Laragon)")
        print("  2. Database 'klsb test' exists")
        print("  3. config.py has correct database credentials")
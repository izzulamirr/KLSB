import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from app.models import JobListing

app = create_app()

with app.app_context():
    try:
        print("Testing job creation from form data...")
        
        # Simulate form data
        title = "Software Engineer"
        department = "Information Technology"
        job_type = "Full-time"
        location = "Kuala Lumpur"
        summary = "We are looking for a talented software engineer."
        points = "• Bachelor's degree in Computer Science\n• 3+ years experience\n• Proficient in Python"
        posted_date = "2 days ago"
        is_active = True
        
        # Create job listing
        new_job = JobListing(
            title=title,
            department=department,
            type=job_type,
            location=location,
            summary=summary,
            points=points,
            posted_date=posted_date or "Recently posted",
            is_active=is_active
        )
        
        print(f"Created job object: {new_job.title}")
        
        # Add to database
        db.session.add(new_job)
        db.session.commit()
        
        print(f"✅ Job listing '{title}' added successfully!")
        print(f"Job ID: {new_job.id}")
        
        # Verify it was added
        job_count = JobListing.query.count()
        print(f"\nTotal job listings in database: {job_count}")
        
        # Show all jobs
        all_jobs = JobListing.query.all()
        print("\nAll job listings:")
        for job in all_jobs:
            print(f"  - ID:{job.id} | {job.title} | {job.department} | Active: {job.is_active}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

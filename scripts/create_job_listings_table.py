"""
Migration script to create job_listings table.
Run this script once to add the table to your database.
"""
from app import create_app, db
from app.models import JobListing

def create_job_listings_table():
    """Create the job_listings table in the database."""
    app = create_app()
    
    with app.app_context():
        # Create the table
        db.create_all()
        print("✅ job_listings table created successfully!")
        
        # Optional: Add sample data
        add_sample = input("Would you like to add sample job listings? (y/n): ").strip().lower()
        if add_sample == 'y':
            sample_jobs = [
                JobListing(
                    title="Senior Piping Designer (E3D)",
                    department="Engineering",
                    job_type="Contract",
                    location="Kuala Lumpur, MY",
                    description="We are looking for an experienced Senior Piping Designer with E3D expertise to join our engineering team.",
                    is_active=True
                ),
                JobListing(
                    title="Process Engineer",
                    department="Engineering",
                    job_type="Full-time",
                    location="Kuala Lumpur, MY",
                    description="Seeking a Process Engineer to support our oil & gas projects.",
                    is_active=True
                ),
                JobListing(
                    title="E3D / AVEVA Admin",
                    department="Digital",
                    job_type="Contract",
                    location="Remote / Hybrid",
                    description="AVEVA Everything3D administrator to manage our 3D design platform.",
                    is_active=True
                ),
                JobListing(
                    title="HSE Officer",
                    department="Manpower",
                    job_type="Project-based",
                    location="Johor, MY",
                    description="Health, Safety & Environment Officer for project site management.",
                    is_active=True
                ),
                JobListing(
                    title="Instrumentation & Control Engineer",
                    department="Engineering",
                    job_type="Full-time",
                    location="Kuala Lumpur, MY",
                    description="I&C Engineer to design and implement control systems for industrial projects.",
                    is_active=True
                ),
            ]
            
            db.session.bulk_save_objects(sample_jobs)
            db.session.commit()
            print(f"✅ Added {len(sample_jobs)} sample job listings!")
        
        print("\n🎉 Migration completed successfully!")
        print("You can now access the admin panel at: /admin/jobs")

if __name__ == "__main__":
    create_job_listings_table()

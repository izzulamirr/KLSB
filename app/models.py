from datetime import datetime
from . import db

# Robust timezone helper: prefer Asia/Kuala_Lumpur if available, else fallback safely
try:
    from zoneinfo import ZoneInfo  # Python 3.9+

    def kl_now():
        try:
            return datetime.now(ZoneInfo("Asia/Kuala_Lumpur"))
        except Exception:
            # Fallback when tz database is missing (common on Windows without tzdata)
            return datetime.now()

except Exception:
    # zoneinfo not available (older Python) – safe fallback
    def kl_now():
        return datetime.now()

class Applicant(db.Model):
    """Model for storing CV/job applicant data."""
    __tablename__ = "applicants"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    position = db.Column(db.String(255), nullable=False)
    availability = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=True)
    file_path = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=kl_now, nullable=False)

    def __repr__(self):
        return f"<Applicant {self.id} {self.full_name} - {self.position}>"


class Proposal(db.Model):
    """Model for storing proposal/quotation requests."""
    __tablename__ = "dproposal"

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(255), nullable=False)
    client_email = db.Column(db.String(200), nullable=False)
    proposal_details = db.Column(db.Text, nullable=False)
    service = db.Column(db.String(150), nullable=False)
    contact_number = db.Column(db.String(20), nullable=True)
    created_at = db.Column(db.DateTime, default=kl_now, nullable=False)

    def __repr__(self):
        return f"<Proposal {self.id} {self.company_name} - {self.service}>"


class JobListing(db.Model):
    """Model for storing job vacancy listings."""
    __tablename__ = "job_listings"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    department = db.Column(db.String(100), nullable=False)
    location = db.Column(db.String(255), nullable=False)
    type = db.Column(db.String(100), nullable=False)  # Changed from job_type to type
    summary = db.Column(db.Text, nullable=True)  # Added
    points = db.Column(db.Text, nullable=True)  # Added
    posted_date = db.Column(db.String(50), nullable=True)  # Added
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=kl_now, nullable=False)
    updated_at = db.Column(db.DateTime, default=kl_now, onupdate=kl_now, nullable=False)

    def __repr__(self):
        return f"<JobListing {self.id} {self.title} - {self.department}>"
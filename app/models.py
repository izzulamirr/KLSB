try:
    from zoneinfo import ZoneInfo
except ImportError:
    from backports.zoneinfo import ZoneInfo  # pip install backports.zoneinfo

from datetime import datetime
from . import db

def kl_now(naive=True):
    """
    Return Malaysia local time (UTC+8).
    - By default (naive=True) returns a naive datetime (tzinfo stripped) because
      MySQL DATETIME doesn't store tzinfo.
    - If you want to keep timezone info and any transitions, call kl_now(naive=False).
    """
    aware = datetime.now(ZoneInfo("Asia/Kuala_Lumpur"))
    return aware.replace(tzinfo=None) if naive else aware

class Applicant(db.Model):
    """Simple model to store CV submissions.

    Fields mirror the CV form and store the saved filename + path.
    """

    __tablename__ = "applicants"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    position = db.Column(db.String(255), nullable=False)
    availability = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=True)
    file_path = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=kl_now, nullable=False)

    def __init__(self, **kwargs):
        cols = set(self.__table__.columns.keys())
        for k, v in kwargs.items():
            if k in cols:
                setattr(self, k, v)

    def __repr__(self):
        return f"<Applicant {self.id} {self.full_name} - {self.position}>"
    
    
class Proposal(db.Model):
    """Model for storing client project proposals."""
    __tablename__ = "dproposal"

    id = db.Column(db.Integer, primary_key=True)
    company_name = db.Column(db.String(255), nullable=False)
    client_email = db.Column(db.String(200), nullable=False)
    proposal_details = db.Column(db.Text, nullable=False)
    service = db.Column(db.String(150), nullable=False)
    created_at = db.Column(db.DateTime, default=kl_now, nullable=False)

    def __repr__(self):
        return f"<Proposal {self.id} {self.company_name} - {self.service}>"
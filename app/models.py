from datetime import datetime
from zoneinfo import ZoneInfo
from . import db
from . import db

def kl_now():
    """
    Return Malaysia local time (UTC+8) as a *naive* datetime.
    MySQL DATETIME doesn't store tzinfo, so we strip it.
    """
    return datetime.now(ZoneInfo("Asia/Kuala_Lumpur")).replace(tzinfo=None)

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
    # Filename and path are optional: we store uploaded files on disk and
    # don't require the DB row to include them.
    filename = db.Column(db.String(255), nullable=True)
    file_path = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=kl_now, nullable=False)

    def __init__(self, **kwargs):
        """Flexible constructor: accept kwargs and only set attributes
        that correspond to mapped columns. This prevents SQLAlchemy's
        default declarative constructor from raising TypeError when
        older code or external callers pass unexpected keywords.
        """
        # Only assign known column names (protect against unexpected kwargs)
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


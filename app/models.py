from datetime import datetime
from . import db


class Applicant(db.Model):
    """Simple model to store CV submissions.

    Fields mirror the CV form and store the saved filename + path.
    """

    __tablename__ = "applicants"

    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(255), nullable=False)
    position = db.Column(db.String(255), nullable=False)
    availability = db.Column(db.String(255), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(512), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Applicant {self.id} {self.full_name} - {self.position}>"

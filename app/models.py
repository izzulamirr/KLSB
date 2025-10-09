from datetime import datetime
from . import db


class Applicant(db.Model):
    __tablename__ = 'applicants'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    email = db.Column(db.String(200), nullable=False)
    position = db.Column(db.String(200), nullable=False)
    availability = db.Column(db.Date, nullable=True)
    filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Applicant {self.id} {self.full_name}>"

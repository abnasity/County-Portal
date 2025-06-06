from app.extensions import db
from datetime import datetime

class County(db.Model):
    __tablename__ = 'counties'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    code = db.Column(db.String(10), unique=True, nullable=False)
    description = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    users = db.relationship('User', backref='county', lazy='dynamic')
    departments = db.relationship('Department', backref='county', lazy='dynamic')

    def __repr__(self):
        return f'<County {self.name}>'

    @property
    def active_departments(self):
        """Get active departments for this county"""
        return self.departments.filter_by(active=True).all()

class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    county_id = db.Column(db.Integer, db.ForeignKey('counties.id'), nullable=False)
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    officers = db.relationship('User', backref='department', lazy='dynamic')
    permit_types = db.relationship('PermitType', backref='department', lazy='dynamic')

    def __repr__(self):
        return f'Department {self.name} - {self.county.name}'
from app.models.user import db
from datetime import datetime
import json

class PermitType(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    required_documents = db.Column(db.Text)  # JSON list
    processing_fee = db.Column(db.Decimal(10, 2))
    
    department = db.relationship('Department', backref='permit_types')

class PermitApplication(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    application_number = db.Column(db.String(50), unique=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    permit_type_id = db.Column(db.Integer, db.ForeignKey('permit_type.id'))
    department_id = db.Column(db.Integer, db.ForeignKey('department.id'))
    county_id = db.Column(db.Integer, db.ForeignKey('county.id'))
    
    # Application details
    business_name = db.Column(db.String(200))
    application_data = db.Column(db.Text)  # JSON for flexible form data
    
    # Status tracking
    status = db.Column(db.String(50), default='Submitted')
    assigned_officer_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    approved_at = db.Column(db.DateTime)
    
    # Audit trail
    status_history = db.Column(db.Text)  # JSON log of status changes
    comments = db.Column(db.Text)
    
    # Relationships
    permit_type = db.relationship('PermitType', backref='applications')
    department = db.relationship('Department', backref='permit_applications')
    county = db.relationship('County', backref='permit_applications')
    assigned_officer = db.relationship('User', foreign_keys=[assigned_officer_id], backref='assigned_permits')
    
    def add_status_change(self, new_status, user_id, comment=None):
        """Add status change to history"""
        history = json.loads(self.status_history) if self.status_history else []
        history.append({
            'status': new_status,
            'changed_by': user_id,
            'changed_at': datetime.utcnow().isoformat(),
            'comment': comment
        })
        self.status_history = json.dumps(history)
        self.status = new_status
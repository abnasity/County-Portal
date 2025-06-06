from app.extensions import db
from datetime import datetime
import json
import uuid


class PermitType(db.Model):
    """Define different types of permits available in each department"""
    __tablename__ = 'permit_types'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)

    # Department relationship - links to your existing department structure
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)

    # Permit processing details
    processing_fee = db.Column(db.Numeric(10, 2), default=0.00)
    processing_days = db.Column(db.Integer, default=14)  # Expected processing time
    required_documents = db.Column(db.Text)  # JSON list of required documents

    # Form configuration for dynamic forms
    form_fields = db.Column(db.Text)  # JSON configuration for custom fields

    # Status and metadata
    active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    applications = db.relationship('PermitApplication', backref='permit_type', lazy='dynamic')

    def __repr__(self):
        return f'<PermitType {self.name} - {self.department.name}>'

    @property
    def required_documents_list(self):
        """Get required documents as a Python list"""
        if self.required_documents:
            return json.loads(self.required_documents)
        return []

    @property
    def total_applications(self):
        """Count total applications for this permit type"""
        return self.applications.count()

    @property
    def approved_applications(self):
        """Count approved applications for this permit type"""
        return self.applications.filter_by(status='Approved').count()


class PermitApplication(db.Model):
    """Individual permit applications submitted by citizens"""
    __tablename__ = 'permit_applications'

    id = db.Column(db.Integer, primary_key=True)
    application_number = db.Column(
        db.String(50),
        unique=True,
        nullable=False,
        default=lambda: f"APP{uuid.uuid4().hex[:8].upper()}"
    )

    # Relationships - connects to your existing user and county structure
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    permit_type_id = db.Column(db.Integer, db.ForeignKey('permit_types.id'), nullable=False)
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'), nullable=False)
    county_id = db.Column(db.Integer, db.ForeignKey('counties.id'), nullable=False)
    assigned_officer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Application details
    business_name = db.Column(db.String(200))
    business_address = db.Column(db.Text)
    contact_phone = db.Column(db.String(20))
    application_data = db.Column(db.Text)  # JSON for flexible form data

    # Location information
    location_address = db.Column(db.Text)
    location_coordinates = db.Column(db.String(100))  # lat,lng format

    # Status and tracking
    status = db.Column(db.String(50), default='Submitted')  # Submitted, Under Review, Approved, Rejected
    priority = db.Column(db.String(20), default='Normal')  # Normal, High, Urgent

    # Timestamps
    submitted_at = db.Column(db.DateTime, default=datetime.utcnow)
    reviewed_at = db.Column(db.DateTime)
    approved_at = db.Column(db.DateTime)
    rejected_at = db.Column(db.DateTime)

    # Audit and comments
    status_history = db.Column(db.Text)  # JSON log of status changes
    officer_comments = db.Column(db.Text)
    applicant_comments = db.Column(db.Text)

    # Payment information
    fee_paid = db.Column(db.Numeric(10, 2), default=0.00)
    payment_reference = db.Column(db.String(100))
    payment_date = db.Column(db.DateTime)

    # Relationships
    applicant = db.relationship('User', foreign_keys=[user_id], backref='permit_applications')
    assigned_officer = db.relationship('User', foreign_keys=[assigned_officer_id], backref='assigned_permits')
    county = db.relationship('County', backref='permit_applications')
    department = db.relationship('Department', backref='permit_applications')
    documents = db.relationship(
        'PermitDocument',
        backref='application',
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    def __repr__(self):
        return f'<PermitApplication {self.application_number} - {self.status}>'

    def add_status_change(self, new_status, user_id, comment=None):
        """Add status change to history with audit trail"""
        history = json.loads(self.status_history) if self.status_history else []
        history.append({
            'status': new_status,
            'changed_by': user_id,
            'changed_at': datetime.utcnow().isoformat(),
            'comment': comment
        })
        self.status_history = json.dumps(history)
        self.status = new_status

        # Update timestamp fields based on status
        if new_status == 'Under Review':
            self.reviewed_at = datetime.utcnow()
        elif new_status == 'Approved':
            self.approved_at = datetime.utcnow()
        elif new_status == 'Rejected':
            self.rejected_at = datetime.utcnow()

    @property
    def application_data_dict(self):
        """Get application data as Python dictionary"""
        if self.application_data:
            return json.loads(self.application_data)
        return {}

    @property
    def status_history_list(self):
        """Get status history as Python list"""
        if self.status_history:
            return json.loads(self.status_history)
        return []

    @property
    def days_since_submission(self):
        """Calculate days since application was submitted"""
        return (datetime.utcnow() - self.submitted_at).days

    @property
    def is_overdue(self):
        """Check if application is overdue based on processing time"""
        if self.permit_type.processing_days and self.status not in ['Approved', 'Rejected']:
            return self.days_since_submission > self.permit_type.processing_days
        return False

    @property
    def status_badge_class(self):
        """Get Bootstrap badge class for status"""
        status_classes = {
            'Submitted': 'bg-primary',
            'Under Review': 'bg-warning',
            'Approved': 'bg-success',
            'Rejected': 'bg-danger',
            'Cancelled': 'bg-secondary'
        }
        return status_classes.get(self.status, 'bg-secondary')


class PermitDocument(db.Model):
    """Documents uploaded for permit applications"""
    __tablename__ = 'permit_documents'

    id = db.Column(db.Integer, primary_key=True)
    application_id = db.Column(db.Integer, db.ForeignKey('permit_applications.id'), nullable=False)

    # Document details
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    file_size = db.Column(db.Integer)
    mime_type = db.Column(db.String(100))

    # Document metadata
    document_type = db.Column(db.String(100))  # ID Copy, Business License, etc.
    description = db.Column(db.Text)

    # Upload tracking
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'))

    # Verification status
    verified = db.Column(db.Boolean, default=False)
    verified_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    verified_at = db.Column(db.DateTime)

    def __repr__(self):
        return f'<PermitDocument {self.original_filename}>'

    @property
    def file_size_mb(self):
        """Get file size in MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
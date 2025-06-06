from flask import (
    Blueprint, redirect, url_for, flash, request,
    render_template, current_app
)
from flask_security import login_required, current_user, roles_required

from app.models.county import County, Department
from app.models.user import Role, User
from app.models.permit import PermitType, PermitApplication, PermitDocument
from app.forms import PermitApplicationForm, ApplicationReviewForm
from app.utils.constants import UserRoles
from app.extensions import db

from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json


main_bp = Blueprint('main_bp', __name__)


@main_bp.route('/')
@login_required
def index():
    """Home page - redirect based on authentication status"""
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.dashboard'))
    return render_template('main/index.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    """Role-based dashboard routing"""
    if current_user.has_role(UserRoles.SUPER_ADMIN):
        return redirect(url_for('main_bp.admin_dashboard'))
    elif current_user.has_role(UserRoles.STAFF):
        return redirect(url_for('main_bp.staff_dashboard'))
    elif current_user.has_role(UserRoles.CITIZEN):
        return redirect(url_for('main_bp.citizen_dashboard'))
    else:
        return redirect(url_for('main_bp.guest_dashboard'))


@main_bp.route('/guest-dashboard')
def guest_dashboard():
    return render_template('main/guest_dashboard.html')


@main_bp.route('/admin-dashboard')
@login_required
@roles_required(UserRoles.SUPER_ADMIN)
def admin_dashboard():
    """Super Admin Dashboard"""
    total_users = User.query.count()
    total_counties = County.query.count()
    total_departments = Department.query.count()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()

    role_stats = {
        role.name: len(role.users.all())
        for role in Role.query.all()
    }

    county_stats = [
        {
            'county': county,
            'user_count': county.users.count(),
            'department_count': county.departments.count()
        }
        for county in County.query.all()
    ]

    return render_template(
        'main/admin_dashboard.html',
        total_users=total_users,
        total_counties=total_counties,
        total_departments=total_departments,
        recent_users=recent_users,
        role_stats=role_stats,
        county_stats=county_stats
    )


@main_bp.route('/citizen-dashboard')
@login_required
@roles_required(UserRoles.CITIZEN)
def citizen_dashboard():
    """Citizen Dashboard - for regular citizens"""
    if not current_user.county:
        flash('Your account is not assigned to a county. Please contact an administrator.', 'warning')
        return redirect(url_for('main_bp.index'))

    county = current_user.county
    departments = county.departments.all()

    applications = PermitApplication.query.filter_by(user_id=current_user.id)\
        .order_by(PermitApplication.submitted_at.desc()).all()

    permit_types = []
    if current_user.county_id:
        permit_types = PermitType.query.join(Department)\
            .filter(
                Department.county_id == current_user.county_id,
                PermitType.active == True
            ).limit(6).all()

    stats = {
        'total_applications': len(applications),
        'pending_applications': len([app for app in applications if app.status in ['Submitted', 'Under Review']]),
        'approved_applications': len([app for app in applications if app.status == 'Approved']),
        'rejected_applications': len([app for app in applications if app.status == 'Rejected'])
    }

    return render_template(
        'main/citizen_dashboard.html',
        county=county,
        departments=departments,
        stats=stats
    )


@main_bp.route('/staff-dashboard')
@login_required
@roles_required(UserRoles.STAFF)
def staff_dashboard():
    """Staff Dashboard - for county staff members"""
    if not current_user.county:
        flash('Your account is not assigned to a county. Please contact an administrator.', 'warning')
        return redirect(url_for('main_bp.index'))

    county = current_user.county
    county_users = county.users.filter(User.id != current_user.id).all()
    departments = county.departments.all()

    applications = []
    if current_user.department_id:
        applications = PermitApplication.query.filter_by(
            department_id=current_user.department_id,
            county_id=current_user.county_id
        ).order_by(PermitApplication.submitted_at.desc()).all()

        # Calculate statistics
        stats = {
            'total_applications': len(applications),
            'pending_review': len([app for app in applications if app.status == 'Submitted']),
            'under_review': len([app for app in applications if app.status == 'Under Review']),
            'completed': len([app for app in applications if app.status in ['Approved', 'Rejected']]),
            'citizens': county.users.filter(User.roles.any(Role.name == UserRoles.CITIZEN)).count()
        }

        # Get recent applications (last 10)
        recent_applications = applications[:10]
    else:
        stats = {
            'pending_applications': 0,
            'in_review': 0,
            'completed': 0,
            'citizens': county.users.filter(User.roles.any(Role.name == UserRoles.CITIZEN)).count()
        }
        recent_applications = []

    return render_template(
        'main/staff_dashboard.html',
        county=county,
        county_users=county_users,
        departments=departments,
        stats=stats,
        recent_applications=recent_applications
    )

    
    


@main_bp.route('/about')
def about():
    """About page"""
    return render_template('main/about.html')


@main_bp.route('/apply', methods=['GET', 'POST'])
@login_required
def apply_permit():
    """Citizen permit application form"""
    if not current_user.has_role('citizen'):
        flash('Only citizens can apply for permits.', 'error')
        return redirect(url_for('main_bp.dashboard'))

    if not current_user.county_id:
        flash('You must be assigned to a county to apply for permits.', 'error')
        return redirect(url_for('main_bp.dashboard'))

    form = PermitApplicationForm()
    form.populate_permit_types(current_user.county_id)

    if form.validate_on_submit():
        permit_type = PermitType.query.get(form.permit_type_id.data)
        if not permit_type:
            flash('Invalid permit type selected.', 'error')
            return redirect(url_for('main_bp.apply_permit'))

        application = PermitApplication(
            user_id=current_user.id,
            permit_type_id=permit_type.id,
            department_id=permit_type.department_id,
            county_id=current_user.county_id,
            business_name=form.business_name.data,
            business_address=form.business_address.data,
            contact_phone=form.contact_phone.data,
            location_address=form.location_address.data,
            application_data=json.dumps({
                'description': form.description.data,
            })
        )

        db.session.add(application)
        db.session.flush()

        if form.documents.data:
            file = form.documents.data
            if file.filename:
                filename = secure_filename(file.filename)
                upload_dir = os.path.join(current_app.instance_path, 'uploads', 'permits')
                os.makedirs(upload_dir, exist_ok=True)

                unique_filename = f"{application.application_number}_{filename}"
                file_path = os.path.join(upload_dir, unique_filename)
                file.save(file_path)

                document = PermitDocument(
                    application_id=application.id,
                    filename=unique_filename,
                    original_filename=filename,
                    file_path=file_path,
                    file_size=os.path.getsize(file_path),
                    mime_type=file.content_type,
                    uploaded_by=current_user.id
                )
                db.session.add(document)

        application.add_status_change('Submitted', current_user.id, 'Application submitted by citizen')
        db.session.commit()

        flash(f'Application submitted successfully! Application number: {application.application_number}', 'success')
        return redirect(url_for('main_bp.citizen_dashboard'))

    return render_template('main/apply_permit.html', form=form)


@main_bp.route('/permit/<int:permit_id>')
@login_required
def permit_detail(permit_id):
    """View permit application details"""
    application = PermitApplication.query.get_or_404(permit_id)

    if not can_access_permit(application):
        flash('Access denied.', 'error')
        return redirect(url_for('main_bp.dashboard'))

    return render_template('main/permit_detail.html', application=application)


@main_bp.route('/permit/<int:permit_id>/review', methods=['GET', 'POST'])
@login_required
def review_permit(permit_id):
    """Staff review permit application"""
    if not current_user.has_role('staff'):
        flash('Access denied.', 'error')
        return redirect(url_for('main_bp.dashboard'))

    application = PermitApplication.query.get_or_404(permit_id)

    if not can_access_permit(application):
        flash('Access denied.', 'error')
        return redirect(url_for('main_bp.dashboard'))

    form = ApplicationReviewForm()

    if form.validate_on_submit():
        application.add_status_change(
            form.status.data,
            current_user.id,
            form.officer_comments.data
        )
        application.officer_comments = form.officer_comments.data
        application.priority = form.priority.data
        application.assigned_officer_id = current_user.id

        db.session.commit()

        flash(f'Application {form.status.data.lower()} successfully!', 'success')
        return redirect(url_for('main_bp.permit_detail', permit_id=permit_id))

    return render_template('main/review_permit.html', application=application, form=form)


def can_access_permit(application):
    """Check if current user can access this permit application"""
    if current_user.has_role('super_admin'):
        return True

    if current_user.has_role('staff'):
        return (
            application.county_id == current_user.county_id and
            application.department_id == current_user.department_id
        )

    if current_user.has_role('citizen'):
        return application.user_id == current_user.id

    return False

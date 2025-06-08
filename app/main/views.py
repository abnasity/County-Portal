from flask import Blueprint, flash, redirect, url_for, render_template, current_app
from flask_security import login_required, roles_required, current_user
from app.extensions import db
from app.models.county import County, Department
from app.models.user import Role, User
from app.utils.constants import UserRoles
from app.models.permit import PermitType, PermitApplication, PermitDocument
from app.forms import PermitApplicationForm, ApplicationReviewForm
from werkzeug.utils import secure_filename
import os
import json
from datetime import datetime

main_bp = Blueprint('main_bp', __name__)

@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main_bp.dashboard'))
    return render_template('main/index.html')

@main_bp.route('/dashboard')
@login_required
def dashboard():
    if current_user.has_role(UserRoles.SUPER_ADMIN):
        return redirect(url_for('main_bp.admin_dashboard'))
    elif current_user.has_role(UserRoles.COUNTY_ADMIN):
        return redirect(url_for('main_bp.county_admin_dashboard'))
    elif current_user.has_role(UserRoles.STAFF):
        return redirect(url_for('main_bp.staff_dashboard'))
    elif current_user.has_role(UserRoles.CITIZEN):
        return redirect(url_for('main_bp.citizen_dashboard'))
    else:
        return redirect(url_for('main_bp.guest_dashboard'))

@main_bp.route('/admin-dashboard')
@login_required
@roles_required(UserRoles.SUPER_ADMIN)
def admin_dashboard():
    total_users = User.query.count()
    total_counties = County.query.count()
    total_departments = Department.query.count()
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()
    role_stats = {role.name: len(role.users.all()) for role in Role.query.all()}
    county_stats = [{
        'county': county,
        'user_count': county.users.count(),
        'department_count': county.departments.count()
    } for county in County.query.all()]

    return render_template('main/admin_dashboard.html',
        total_users=total_users,
        total_counties=total_counties,
        total_departments=total_departments,
        recent_users=recent_users,
        role_stats=role_stats,
        county_stats=county_stats)
    
    
@main_bp.route('/county-admin-dashboard')
@login_required
def county_admin_dashboard():
    # Combined permission check
    if not (current_user.has_role(UserRoles.COUNTY_ADMIN) and 
            current_user.county and 
            current_user.county.code == '036'):
        flash('Access restricted to Bomet County Admins only.', 'danger')
        return redirect(url_for('main_bp.dashboard'))
    
    county = current_user.county
    users = county.users.all()
    departments = county.departments.all()
    applications = PermitApplication.query.filter_by(county_id=county.id).all()
    
     # Calculate role statistics
    role_stats = {}
    for user in users:
        for role in user.roles:
            role_stats[role.name] = role_stats.get(role.name, 0) + 1

    stats = {
        'total_users': len(users),
        'departments': len(departments),
        'applications': len(applications)
    }

    return render_template('main/county_admin_dashboard.html',
        county=county,
        users=users,
        departments=departments,
        applications=applications,
        stats=stats)



@main_bp.route('/staff-dashboard')                                            
@login_required                                                               
@roles_required(UserRoles.STAFF)                                              
def staff_dashboard():                                                        
    """Staff Dashboard - for county staff members"""                          
    if not current_user.county:                                               
        flash('Your account is not assigned to a county. Please contact an administrator.', 'warning')                                                     
        return redirect(url_for('main_bp.index'))                             
                                                                                  
    # Get county-specific data                                                
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
            'completed': len([app for app in applications if app.status in ['Approved', 'Rejected']])                                                      
        }                                                                         
                                                                                  
        # Get recent applications (last 10)                                       
    recent_applications = applications[:10] 
    return render_template('main/staff_dashboard.html',
                            county=county,
                            departments=departments,
                            stats=stats,
                            applications=applications,
                            recent_applications=recent_applications)                          

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
    # Get user's permit applications                                          
    applications = PermitApplication.query.filter_by(user_id=current_user.id)\
        .order_by(PermitApplication.submitted_at.desc()).all()                
                                                                                
    # Get available permit types for quick apply                              
    permit_types = []
    if current_user.county_id:
        permit_types = PermitType.query.join(Department).filter(Department.county_id == current_user.county_id, PermitType.active)\
            .limit(6).all()

        stats = {
            'total_applications': len(applications),
            'pending_applications': len([app for app in applications if app.status in ['Submitted', 'Under Review']]),
            'approved_applications': len([app for app in applications if app.status == 'Approved']),
            'rejected_applications': len([app for app in applications if app.status == 'Rejected'])
        }

    return render_template('main/citizen_dashboard.html',
                            county=county,
                            departments=departments,
                            permit_types=permit_types,
                            stats=stats)

@main_bp.route('/guest-dashboard')
@login_required
@roles_required(UserRoles.GUEST)
def guest_dashboard():
    """Guest Dashboard - limited access"""
    return render_template('main/guest_dashboard.html')                       
                                                                                  
@main_bp.route('/about')                                                      
def about():                                                                  
    """About page"""                                                          
    return render_template('main/about.html')

@main_bp.route('/apply', methods=['GET', 'POST'])                             
@login_required                                                               
def apply_permit():                                                           
    """Citizen permit application form"""                                     
    # Only citizens can apply for permits                                     
    if not current_user.has_role('citizen'):                                  
        flash('Only citizens can apply for permits.', 'error')                
        return redirect(url_for('main_bp.dashboard'))                         
                                                                                
    if not current_user.county_id:                                            
        flash('You must be assigned to a county to apply for permits.', 'error')                                                                        
        return redirect(url_for('main_bp.dashboard'))                         
                                                                                
    form = PermitApplicationForm()                                            
    form.populate_permit_types(current_user.county_id)                        
                                                                                
    if form.validate_on_submit():                                             
        # Create new permit application                                       
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
        db.session.flush()  # Get the application ID                          
                                                                                
            # Handle file upload if provided                                      
        if form.documents.data:                                               
            file = form.documents.data                                        
            if file.filename:                                                 
                filename = secure_filename(file.filename)                     
                # Create uploads directory if it doesn't exist                
                upload_dir = os.path.join(current_app.instance_path, 'uploads','permits')                                                                      
                os.makedirs(upload_dir, exist_ok=True)                        
                                                                                
                # Save file with unique name                                  
                unique_filename = f"{application.application_number}_{filename}"                                                 
                file_path = os.path.join(upload_dir, unique_filename)         
                file.save(file_path)                                          
                                                                                
                # Create document record                                      
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
                                                                                
        # Add initial status to history                                       
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
                                                                                
    # Check access permissions                                                
    if not can_access_permit(application):                                    
        flash('Access denied.', 'error')                                      
        return redirect(url_for('main_bp.dashboard'))                         
                                                                                
    return render_template('main/permit_detail.html', application=application)
                                                                                
@main_bp.route('/permit/<int:permit_id>/review', methods=['GET', 'POST'])     
@login_required                                                               
def review_permit(permit_id):                                                 
    """Staff review permit application"""                                     
    # Only staff can review permits                                           
    if not current_user.has_role('staff'):                                    
        flash('Access denied.', 'error')                                      
        return redirect(url_for('main_bp.dashboard'))                         
                                                                                
    application = PermitApplication.query.get_or_404(permit_id)               
                                                                                
    # Check if staff can access this permit (same county/department)          
    if not can_access_permit(application):                                    
        flash('Access denied.', 'error')                                      
        return redirect(url_for('main_bp.dashboard'))                         
                                                                                
    form = ApplicationReviewForm()                                            
                                                                                
    if form.validate_on_submit():                                             
        # Update application status                                           
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

# Add this helper function
def can_access_permit(application):
    """Check if current user can access this permit application"""
    # Super admin can access all
    if current_user.has_role('super_admin'):
        return True

    # Staff can access permits in their county and department
    if current_user.has_role('staff'):
        return (application.county_id == current_user.county_id and           
                application.department_id == current_user.department_id)      
                                                                                
    # Citizens can only access their own applications                         
    if current_user.has_role('citizen'):                                      
        return application.user_id == current_user.id                         
                                                                                
    return False
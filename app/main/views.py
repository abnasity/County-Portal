from flask import Blueprint, redirect, url_for, flash, request, render_template
from flask_security import login_required, current_user, roles_required

from app.models.county import County, Department
from app.models.user import Role, User
from app.utils.constants import UserRoles

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
        
        
        
        
        
@main_bp.route('/admin-dashboard')                                            
@login_required                                                               
@roles_required(UserRoles.SUPER_ADMIN)                                        
def admin_dashboard():                                                        
    """Super Admin Dashboard"""                                               
    # Get statistics for the admin dashboard                                  
    total_users = User.query.count()                                          
    total_counties = County.query.count()                                     
    total_departments = Department.query.count()                              
                                                                                
    # Get recent users                                                        
    recent_users = User.query.order_by(User.created_at.desc()).limit(5).all()  
                                                                                
    # Get users by role                                                       
    role_stats = {}                                                           
    for role in Role.query.all():                                             
        role_stats[role.name] = len(role.users.all())                         
                                                                                
    # Get county statistics                                                   
    county_stats = []                                                         
    for county in County.query.all():                                         
        county_stats.append({                                                 
            'county': county,                                                 
            'user_count': county.users.count(),                               
            'department_count': county.departments.count()                    
        })                                                                    
                                                                                
    return render_template('main/admin_dashboard.html',                       
                            total_users=total_users,                             
                            total_counties=total_counties,                       
                            total_departments=total_departments,                 
                            recent_users=recent_users,                           
                            role_stats=role_stats,                               
                            county_stats=county_stats)
    


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
                                                                                
    return render_template('main/staff_dashboard.html',                       
                            county=county,                                       
                            county_users=county_users,                           
                            departments=departments)                             
                                                                                
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
                                                                                
    return render_template('main/citizen_dashboard.html',                     
                            county=county,                                       
                            departments=departments)                             
                                                                                
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
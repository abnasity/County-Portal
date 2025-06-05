from flask import Blueprint, flash, jsonify, redirect, render_template, url_for, request
from flask_security import login_required, current_user, roles_required
from app.models.user import User, Role
from app.models.county import County, Department
from app.utils.constants import UserRoles
from app.extensions import db



auth_bp = Blueprint('auth_bp', __name__,)

@auth_bp.route('/profile')                                                    
@login_required                                                               
def profile():                                                                
    """User profile page"""                                                   
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/users')                                                      
@login_required                                                               
@roles_required(UserRoles.SUPER_ADMIN)                                        
def users():                                                                  
    """User management page for super admins"""                               
    page = request.args.get('page', 1, type=int)                              
    search = request.args.get('search', '', type=str)                         
    role_filter = request.args.get('role', '', type=str)                      
    county_filter = request.args.get('county', '', type=str)                  
                                                                                
    # Build query with filters                                                
    query = User.query                                                        
                                                                                
    if search:                                                                
        query = query.filter(                                                 
            (User.email.contains(search)) |                                   
            (User.first_name.contains(search)) |                              
            (User.last_name.contains(search))                                 
        )                                                                     
                                                                                
    if role_filter:                                                           
        role = Role.query.filter_by(name=role_filter).first()                 
        if role:                                                              
            query = query.filter(User.roles.contains(role))                   
                                                                                
    if county_filter:                                                         
        query = query.filter_by(county_id=county_filter)                      
                                                                                
    # Paginate results                                                        
    users = query.paginate(                                                   
        page=page, per_page=20, error_out=False                               
    )                                                                         
                                                                                
    # Get filter options                                                      
    roles = Role.query.all()                                                  
    counties = County.query.filter_by(active=True).all()                      
                                                                                
    return render_template('auth/users.html',                                 
                            users=users,                                         
                            roles=roles,                                         
                            counties=counties,                                   
                            current_search=search,                               
                            current_role=role_filter,                            
                            current_county=county_filter)                        
                                                                                  
@auth_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])          
@login_required                                                               
@roles_required(UserRoles.SUPER_ADMIN)                                        
def edit_user(user_id):                                                       
    """Edit user details"""                                                   
    user = User.query.get_or_404(user_id)                                     
                                                                                
    if request.method == 'POST':                                              
        # Update user details                                                 
        user.first_name = request.form.get('first_name')                      
        user.last_name = request.form.get('last_name')                        
        user.phone = request.form.get('phone')                                
        user.county_id = request.form.get('county_id') or None                
        user.department_id = request.form.get('department_id') or None        
        user.active = 'active' in request.form                                
                                                                                
        # Update roles                                                        
        user.roles.clear()                                                    
        role_ids = request.form.getlist('roles')                              
        for role_id in role_ids:                                              
            role = Role.query.get(role_id)                                    
            if role:                                                          
                user.roles.append(role)                                       
                                                                                
        try:                                                                  
            db.session.commit()                                               
            flash(f'User {user.email} updated successfully!', 'success')      
            return redirect(url_for('auth_bp.users'))                         
        except Exception as e:                                                
            db.session.rollback()                                             
            flash(f'Error updating user: {str(e)}', 'error')                  
                                                                                
    roles = Role.query.all()                                                  
    counties = County.query.filter_by(active=True).all()                      
    departments = Department.query.filter_by(active=True).all()               
                                                                                
    return render_template('auth/edit_user.html',                             
                            user=user,                                           
                            roles=roles,                                         
                            counties=counties,                                   
                            departments=departments)                             
                                                                                  
@auth_bp.route('/users/<int:user_id>/toggle-status', methods=['POST'])        
@login_required                                                               
@roles_required(UserRoles.SUPER_ADMIN)                                        
def toggle_user_status(user_id):                                              
    """Toggle user active status"""                                           
    user = User.query.get_or_404(user_id)                                     
                                                                                
    if user.id == current_user.id:                                            
        return jsonify({'error': 'You cannot deactivate your own account'}),  400                                                                             
                                                                                
    user.active = not user.active                                             
    db.session.commit()                                                       
                                                                                
    status = 'activated' if user.active else 'deactivated'                    
    return jsonify({'message': f'User {user.email} {status} successfully'})   
                                                                                
@auth_bp.route('/departments/by-county/<int:county_id>')                      
@login_required                                                               
def departments_by_county(county_id):                                         
    """Get departments for a specific county (AJAX endpoint)"""
    departments = Department.query.filter_by(county_id=county_id, active=True).all()
                                                                          
    return jsonify([                                                          
        {'id': dept.id, 'name': dept.name}                                    
        for dept in departments                                               
    ])
    
#
    

        
    
    
    
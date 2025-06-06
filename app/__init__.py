from flask import Flask
from flask_security import SQLAlchemyUserDatastore
from app.extensions import db, migrate, mail, security, csrf
from config import Config
import json


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    csrf.init_app(app)

    # Blueprint imports
    from app.main.views import main_bp
    from app.api.routes import api_bp
    from app.auth.routes import auth_bp
    
    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(auth_bp)

    # Import models and setup security
    from app.models.user import User, Role, uuid
    from app.models.county import County, Department
    from app.models.permit import PermitType, PermitApplication, PermitDocument
    from app.forms import ExtendedLoginForm, ExtendedRegisterForm
    from flask_security import hash_password
    
    # **************Advanced topics*************
    
    # custom user registration handler
    from flask_security.signals import user_registered
    
    @user_registered.connect_via(app)
    def user_registered_signhandler(sender, user, confirm_token, **extra):
        """Handle post-registration logic"""
        # Assign default 'citizen' role
        default_role = Role.query.filter_by(name='citizen').first()           
        if default_role and not user.roles:                                   
                user.roles.append(default_role)                                   
                db.session.commit()                                               
                                                                                  
        print(f"New user registered: {user.email} in {user.county.name if user.
  county else 'No County'}")
    
    
    # *********End***********
    
    # setup flask security
    user_datastore = SQLAlchemyUserDatastore(db, User, Role)
    security.init_app(app, user_datastore, register_form=ExtendedRegisterForm, login_form=ExtendedLoginForm)

    with app.app_context():
        db.create_all()
        # county data
        counties_data = [                                                         
            {'name': 'Bomet County', 'code': '036', 'description': 'Kipsisgis County'},                                                                       
            {'name': 'Narok County', 'code': '033', 'description': 'Maa county'},                                                                       
            {'name': 'Kericho County', 'code': '035', 'description': 'Green county'},                                                                       
        ]
        created_counties = {}
        for county_data in counties_data:
            county = County.query.filter_by(name=county_data['name']).first()
            if not county:
                county = County(**county_data)
                db.session.add(county)
                created_counties[county.code] = county
        db.session.commit()
        
        # Create departments for each county                                      
        departments_data = [                                                      
            {'name': 'Trade & Commerce', 'code': 'TC'},                           
            {'name': 'Lands & Housing', 'code': 'LH'},                            
            {'name': 'Health Services', 'code': 'HS'},                            
            {'name': 'Environment & Water', 'code': 'EW'},                        
        ]
        for county in created_counties.values():                                  
            for dept_data in departments_data:                                    
                dept = Department.query.filter_by(                                
                    code=dept_data['code'],                                       
                    county_id=county.id                                           
                ).first()                                                         
                if not dept:                                                      
                    dept = Department(                                            
                        name=dept_data['name'],                                   
                        code=dept_data['code'],                                   
                        county_id=county.id,                                      
                        description=f"{dept_data['name']} department for {county.name}"                                                                          
                    )                                                             
                    db.session.add(dept)                                         
                    print(f"Created department: {dept.name} in {county.name}")
                db.session.commit()
                
                
                
                
        """Initialize sample permit types for each department"""                  
        permit_types_data = [
            # Trade & Commerce permits                                            
            {                                                                     
                'name': 'Business License',                                       
                'description': 'License for operating a business within the county',                                                                        
                'department_code': 'TC',                                          
                'processing_fee': 5000.00,                                        
                'processing_days': 14,                                            
                'required_documents': ['ID Copy', 'Business Registration Certificate', 'Tax PIN Certificate', 'Location Map']                            
            },                                                                    
            {                                                                     
                'name': 'Trading License',                                        
                'description': 'License for retail and wholesale trading  activities',                                                                    
                'department_code': 'TC',                                          
                'processing_fee': 3000.00,                                        
                'processing_days': 10,                                            
                'required_documents': ['ID Copy', 'Business Permit', 'Store Photo']                                                                         
            },                                                                    
            # Lands & Housing permits                                             
            {                                                                     
                'name': 'Building Permit',                                        
                'description': 'Permit for construction and building activities', 
                'department_code': 'LH',                                          
                'processing_fee': 15000.00,                                       
                'processing_days': 21,                                            
                'required_documents': ['ID Copy', 'Site Plan', 'Architectural Drawings', 'Land Title Deed']                                                   
            },                                                                    
            {                                                                     
                'name': 'Change of Use Permit',                                   
                'description': 'Permit to change land use classification',        
                'department_code': 'LH',                                          
                'processing_fee': 8000.00,                                        
                'processing_days': 28,                                            
                'required_documents': ['ID Copy', 'Current Title Deed', 'Survey Plan', 'Development Proposal']                                                  
            },                                                                    
            # Health Services permits                                             
            {                                                                     
                'name': 'Food Handler License',                                   
                'description': 'License for individuals handling food  commercially',                                                                  
                'department_code': 'HS',                                          
                'processing_fee': 1500.00,                                        
                'processing_days': 7,                                             
                'required_documents': ['ID Copy', 'Medical Certificate', 'Passport Photo']                                                                         
            },                                                                    
            {                                                                     
                'name': 'Health Facility License',                                
                'description': 'License for operating health facilities',         
                'department_code': 'HS',                                          
                'processing_fee': 25000.00,                                       
                'processing_days': 30,                                            
                'required_documents': ['ID Copy', 'Professional License','Facility Inspection Report', 'Equipment List']                                 
            },                                                                    
            # Environment & Water permits                                         
            {                                                                     
                'name': 'Water Connection Permit',                                
                'description': 'Permit for new water connection',                 
                'department_code': 'EW',                                          
                'processing_fee': 5000.00,                                        
                'processing_days': 14,                                            
                'required_documents': ['ID Copy', 'Property Ownership Proof','Site Plan']                                                                    
            },                                                                    
            {                                                                     
                'name': 'Environmental Impact Assessment',                        
                'description': 'Assessment for projects with environmental impact',
                'department_code': 'EW',                                          
                'processing_fee': 50000.00,                                       
                'processing_days': 60,                                            
                'required_documents': ['ID Copy', 'Project Proposal','Environmental Study', 'Community Consent']                                     
            }                                                                     
        ]                                                                         
                                                                                  
        for county in created_counties.values():                                  
            for permit_data in permit_types_data:                                 
                # Find the department for this permit type                        
                department = Department.query.filter_by(                          
                    code=permit_data['department_code'],                          
                    county_id=county.id                                           
                ).first()                                                         
                                                                                  
                if department:                                                    
                    # Check if permit type already exists                         
                    existing_permit = PermitType.query.filter_by(                 
                        name=permit_data['name'],                                 
                        department_id=department.id                               
                    ).first()                                                     
                                                                                  
                    if not existing_permit:                                       
                        permit_type = PermitType(                                 
                            name=permit_data['name'],                             
                            description=permit_data['description'],               
                            department_id=department.id,                          
                            processing_fee=permit_data['processing_fee'],         
                            processing_days=permit_data['processing_days'],       
                            required_documents=json.dumps(permit_data['required_documents'])                                        
                        )                                                         
                        db.session.add(permit_type)                               
                        print(f"Created permit type: {permit_type.name} in {department.name}, {county.name}")                                              
                                                                                  
                db.session.commit()        
                
                
                
                
                
                
                
                
                
                

        # Create roles
        roles_data = [
            {'name': 'super_admin', 'description': 'Administrator role with full access'},
            {'name': 'staff', 'description': 'County staff with limited access'},
            {'name': 'citizen', 'description': 'Regular citizen with basic access'},
            {'name': 'guest', 'description': 'Guest user with minimal access'},
        ]
        for role_data in roles_data:
            role = Role.query.filter_by(name=role_data['name']).first()
            if not role:
                db.session.add(Role(**role_data))
        db.session.commit()
        
        
        

        # Create super admin user
        admin_role = Role.query.filter_by(name='super_admin').first()
        admin_user = User.query.filter_by(email='abdkpng@gmail.com').first()

        if not admin_user: 
            admin_user = User(
                email='abdkpng@gmail.com',
                first_name="Kipngeno",
                last_name="Abednego",
                password=hash_password("@bd1998z"),
                active=True,
                county_id=created_counties['036'].id,
                roles=[admin_role]
            )
            db.session.add(admin_user)
            db.session.commit()
            print("Database initialised and superuser created.")
        else:
            print("Superuser already exists.")
            

    return app





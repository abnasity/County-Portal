from flask_security import RegisterForm, LoginForm
from flask_security.forms import Form, Length
from wtforms import StringField, SelectField,  TelField
from wtforms.validators import DataRequired, Optional, ValidationError
from app.models.county import County


class ExtendedRegisterForm(RegisterForm):
    """Enhanced registration form with additional user fields
    """
    first_name = StringField(
        'First Name', validators=[DataRequired('First name is required'), Length(min=2, max=50, message='First name must be between 2 and 50 characters')]
    )
    last_name = StringField(
        'Last Name', validators=[DataRequired('Last name is required'), Length(min=2, max=50, message='Last name must be between 2 and 50 characters')]
    )
    phone_number = TelField(
        'Phone Number', validators=[Optional(), Length(min=10, max=20, message='phone number must be between 10 and 20 digits')]
    )
    county_id = SelectField(
        'County', validators=[DataRequired('County is required')], coerce=int, choices=[] #will be populated dynamically
    )
    
    

    def __init__(self, *args, **kwargs):                                      
            super(ExtendedRegisterForm, self).__init__(*args, **kwargs)           
            # Populate county choices dynamically                                 
            self.county_id.choices = [                                            
                (county.id, county.name)                                          
                for county in County.query.filter_by(active=True).order_by(County.
  name).all()                                                                     
            ]                                                                     
            # Add default "Select County" option       
                                      
            self.county_id.choices.insert(0, (0, 'Select your county...'))        
                                                                                  
    def validate_phone_number(self, field):                                   
            """Custom validator for phone number format"""                        
            if field.data:                                                        
                # Remove any non-digit characters                                 
                digits_only = ''.join(filter(str.isdigit, field.data))            
                if len(digits_only) < 10:                                         
                 raise ValidationError('Phone number must contain at least 10 digits')
                # Update field data with cleaned format                           
                field.data = digits_only                                          
                                                                                  
    def validate_county_id(self, field):                                      
            """Ensure a valid county is selected"""                               
            if field.data == 0:                                                   
                raise ValidationError('Please select your county')
            
class ExtendedLoginForm(LoginForm):                                           
        """Enhanced login form with better styling support"""                     
                                                                                  
        def _init_(self, *args, **kwargs):                                      
            super(ExtendedLoginForm, self)._init_(*args, **kwargs)              
            # Add placeholder text and styling classes                            
            self.email.render_kw = {                                              
                'placeholder': 'Enter your email address',                        
                'class': 'form-control form-control-lg'                           
            }                                                                     
            self.password.render_kw = {                                           
                'placeholder': 'Enter your password',                             
                'class': 'form-control form-control-lg'                           
            }                                                                     
                                                                                  
class UserProfileForm(Form):                                                  
        """Form for users to update their profile information"""                  
                                                                                  
        first_name = StringField(                                                 
            'First Name',                                                         
            validators=[DataRequired(), Length(min=2, max=50)]                    
        )                                                                         
                                                                                  
        last_name = StringField(                                                  
            'Last Name',                                                          
            validators=[DataRequired(), Length(min=2, max=50)]                    
        )                                                                         
                                                                                  
        phone_number = TelField(                                                  
            'Phone Number',                                                       
            validators=[Optional(), Length(min=10, max=15)]                       
        )                                                                         
                                                                                  
        def validate_phone_number(self, field):                                   
            """Custom validator for phone number format"""                        
            if field.data:                                                        
                digits_only = ''.join(filter(str.isdigit, field.data))            
                if len(digits_only) < 10:                                         
                 raise ValidationError('Phone number must contain at least 10 digits')                                                                        
                field.data = digits_only
import os
from dotenv import load_dotenv



load_dotenv()
class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///county.db')
    SQLALCHEMY__TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY')
    SECRET_PASSWORD_SALT = os.getenv('SECRET_PASSWORD_SALT')
    
   
   # Email templates and customization                                           
    SECURITY_EMAIL_HTML = True                 # Send HTML emails                 
    SECURITY_EMAIL_PLAINTEXT = True           # Send plain text emails
    
    # Email subjects (customizable)                                               
    SECURITY_EMAIL_SUBJECT_REGISTER = "Welcome to County Services Portal"         
    SECURITY_EMAIL_SUBJECT_PASSWORD_RESET = "Password Reset Instructions"         
    SECURITY_EMAIL_SUBJECT_PASSWORD_CHANGE_NOTICE = "Password Changed Successfully"
    
     #Flask-security settings
    SECURITY_PASSWORD_HASH = "bcrypt"  # use bcrypt for password hashing
    SECURITY_PASSWORD_SALT = os.getenv("SECURITY_PASSWORD_SALT")
    SECURITY_REGISTERABLE = True
    SECURITY_SEND_REGISTER_EMAIL = True
    SECURITY_CHANGEABLE = True
    SECURITY_TRACKABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_SEND_PASSWORD_RESET_EMAIL = True
    SECURITY_SEND_PASSWORD_CHANGE_EMAIL = True
    SECURITY_EMAIL_SENDER = os.getenv('MAIL_DEFAULT_SENDER')
    SECURITY_POST_RESET_VIEW = 'auth_bp.login'
    
    
    # Flask-Mail Settings (Gmail SMTP)
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 465  # Port for SSL
    MAIL_USE_TLS = False  # Don't use TLS when using SSL
    MAIL_USE_SSL = True  # Use SSL for Gmail
    MAIL_USERNAME = os.getenv('MAIL_USERNAME')
    MAIL_PASSWORD = os.getenv('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.getenv('MAIL_USERNAME')

    # Validate mail configuration
    if not all([MAIL_USERNAME, MAIL_PASSWORD]):
        raise ValueError("Mail settings are not properly configured. Check your .env file.")             
  
    
    
    
     
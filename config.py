import os
from dotenv import load_dotenv


load_dotenv()
class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///county.db')
    SQLALCHEMY__TRACK_MODIFICATIONS = False
    SECRET_KEY = os.getenv('SECRET_KEY')
    SECRET_PASSWORD_SALT = os.getenv('SECRET_PASSWORD_SALT')
    
    #Flask-security settings
    
    SECURITY_PASSWORD_HASH = "bcrypt" #use bcrypt for password hashing over argon2
    SECURITY_PASSWORD_SALT = os.environ.get("SECURITY_PASSWORD_SALT")
    SECURITY_REGISTERABLE = True
    SECURITY_SEND_REGISTER_EMAIL = False
    SECURITY_CHANGEABLE = True
    SECURITY_TRACKABLE = True
    SECURITY_RECOVERABLE = True
    SECURITY_SEND_PASSWORD_RESET_EMAIL = False
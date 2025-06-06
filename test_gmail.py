import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

def test_gmail_connection():
    username = os.getenv('MAIL_USERNAME')
    password = os.getenv('MAIL_PASSWORD')
    
    print(f"Testing connection for: {username}")
    
    try:
        # Try SSL connection
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.login(username, password)
        print("SSL Connection successful!")
        server.quit()
    except Exception as e:
        print(f"SSL Error: {str(e)}")

if __name__ == '__main__':
    test_gmail_connection()

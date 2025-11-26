"""
Test sending to DIFFERENT email address to verify SMTP works
"""
import smtplib
from email.mime.text import MIMEText

MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USERNAME = "izzulamir1602@gmail.com"
MAIL_PASSWORD = "pizwfunikxvxuwwn"

# Enter a DIFFERENT email address to test
# This will help us confirm if Gmail is blocking self-sent emails
test_email = input("Enter a different email address to test (e.g., friend's email): ").strip()

if not test_email:
    print("No email provided. Exiting.")
    exit()

try:
    msg = MIMEText("This is a test from KLSB notification system. If you receive this, SMTP is working!")
    msg['Subject'] = "KLSB Email Test - Please Confirm Receipt"
    msg['From'] = MAIL_USERNAME
    msg['To'] = test_email
    
    print(f"Sending test email to: {test_email}")
    
    server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
    server.starttls()
    server.login(MAIL_USERNAME, MAIL_PASSWORD)
    server.send_message(msg)
    server.quit()
    
    print(f"✅ Email sent successfully to {test_email}")
    print("Ask them to check their inbox (and spam folder)")
    
except Exception as e:
    print(f"❌ Error: {e}")

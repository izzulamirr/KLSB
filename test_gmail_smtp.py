"""
Quick diagnostic test for Gmail SMTP
This will test if your Gmail credentials work
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Your Gmail settings from config.py
MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USERNAME = "izzulamir1602@gmail.com"
MAIL_PASSWORD = "pizwfunikxvxuwwn"  # Your App Password without spaces
ADMIN_EMAIL = "izzulamir1602@gmail.com"

print("=" * 60)
print("Testing Gmail SMTP Configuration")
print("=" * 60)
print(f"Server: {MAIL_SERVER}:{MAIL_PORT}")
print(f"From: {MAIL_USERNAME}")
print(f"To: {ADMIN_EMAIL}")
print("-" * 60)

try:
    # Create test message
    msg = MIMEMultipart()
    msg['From'] = MAIL_USERNAME
    msg['To'] = ADMIN_EMAIL
    msg['Subject'] = "KLSB Test Email - SMTP Working!"
    
    body = """
    This is a test email from your KLSB notification system.
    
    If you receive this, your Gmail SMTP is configured correctly!
    
    - Server: smtp.gmail.com:587
    - From: izzulamir1602@gmail.com
    """
    msg.attach(MIMEText(body, 'plain'))
    
    # Connect and send
    print("\n1. Connecting to Gmail SMTP...")
    server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT, timeout=10)
    
    print("2. Starting TLS encryption...")
    server.starttls()
    
    print("3. Logging in...")
    server.login(MAIL_USERNAME, MAIL_PASSWORD)
    
    print("4. Sending test email...")
    server.send_message(msg)
    
    print("5. Closing connection...")
    server.quit()
    
    print("\n" + "=" * 60)
    print("✅ SUCCESS! Email sent successfully!")
    print("=" * 60)
    print(f"\nCheck your inbox at: {ADMIN_EMAIL}")
    print("(Also check Spam folder if not in inbox)")
    
except smtplib.SMTPAuthenticationError as e:
    print("\n❌ AUTHENTICATION FAILED!")
    print(f"Error: {e}")
    print("\nPossible fixes:")
    print("1. Make sure App Password is correct (16 characters, no spaces)")
    print("2. Get new App Password: https://myaccount.google.com/apppasswords")
    print("3. Ensure 2-Step Verification is enabled on your Google Account")
    
except smtplib.SMTPException as e:
    print(f"\n❌ SMTP Error: {e}")
    
except Exception as e:
    print(f"\n❌ Unexpected error: {e}")
    print(f"Error type: {type(e).__name__}")

print("\n" + "=" * 60)

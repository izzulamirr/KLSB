"""
Test sending HIGH PRIORITY email with importance markers
"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

MAIL_SERVER = "smtp.gmail.com"
MAIL_PORT = 587
MAIL_USERNAME = "izzulamir1602@gmail.com"
MAIL_PASSWORD = "pizwfunikxvxuwwn"
ADMIN_EMAIL = "izzulamir1602@gmail.com"

print("=" * 60)
print("Testing HIGH PRIORITY Email with Importance Markers")
print("=" * 60)

try:
    # Create message with HTML
    msg = MIMEMultipart('alternative')
    msg['From'] = MAIL_USERNAME
    msg['To'] = ADMIN_EMAIL
    msg['Subject'] = "🔔 [IMPORTANT] KLSB Test - High Priority Email"
    
    # Add priority headers
    msg['X-Priority'] = '1'  # 1=Highest, 5=Lowest
    msg['Importance'] = 'high'
    msg['X-MSMail-Priority'] = 'High'
    
    # Plain text version
    text = """
    IMPORTANT: This is a high-priority test email from KLSB notification system.
    
    This email should appear with importance markers in Gmail:
    - Red exclamation mark or "Important" label
    - Higher visibility in inbox
    
    If you see this with importance markers, the system is working!
    """
    
    # HTML version
    html = """
    <html>
    <body style="font-family: Arial, sans-serif;">
        <div style="background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%); padding: 20px; text-align: center; color: white;">
            <h1>🔔 IMPORTANT TEST EMAIL</h1>
        </div>
        <div style="padding: 20px; background-color: #fef2f2;">
            <h2 style="color: #dc2626;">High Priority Notification</h2>
            <p>This email has been marked as <strong>HIGH PRIORITY</strong> with the following headers:</p>
            <ul>
                <li>X-Priority: 1 (Highest)</li>
                <li>Importance: high</li>
                <li>X-MSMail-Priority: High</li>
            </ul>
            <p>Check if your email client shows importance indicators (red flag, exclamation mark, etc.)</p>
        </div>
    </body>
    </html>
    """
    
    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))
    
    # Send
    print("\n1. Connecting to Gmail...")
    server = smtplib.SMTP(MAIL_SERVER, MAIL_PORT)
    server.starttls()
    
    print("2. Logging in...")
    server.login(MAIL_USERNAME, MAIL_PASSWORD)
    
    print("3. Sending HIGH PRIORITY email...")
    server.send_message(msg)
    
    print("4. Closing connection...")
    server.quit()
    
    print("\n" + "=" * 60)
    print("✅ HIGH PRIORITY Email Sent Successfully!")
    print("=" * 60)
    print(f"\nCheck your inbox at: {ADMIN_EMAIL}")
    print("\nLook for:")
    print("  • Red exclamation mark or importance flag")
    print("  • Subject: 🔔 [IMPORTANT] KLSB Test - High Priority Email")
    print("  • Should appear at the top of your inbox")
    print("\nAlso check: Spam, Promotions, All Mail folders")
    
except Exception as e:
    print(f"\n❌ Error: {e}")
    print(f"Error type: {type(e).__name__}")

print("\n" + "=" * 60)

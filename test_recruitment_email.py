"""Test email to recruitment@kemuncaklanai.com"""
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# Gmail SMTP settings
smtp_server = "smtp.gmail.com"
smtp_port = 587
sender_email = "izzulamir1602@gmail.com"
app_password = "pizwfunikxvxuwwn"  # Your Gmail App Password
recipient_email = "sysdev@kemuncaklanai.com"

print("=" * 60)
print("Testing Email to sysdev@kemuncaklanai.com")
print("=" * 60)

try:
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = '🔔 [IMPORTANT] KLSB Test - Recruitment Email'
    msg['From'] = sender_email
    msg['To'] = recipient_email
    
    # Add importance headers
    msg['X-Priority'] = '1'
    msg['Importance'] = 'high'
    msg['Priority'] = 'urgent'
    msg['X-MSMail-Priority'] = 'High'
    msg['X-Gmail-Labels'] = 'Important'
    
    # Email body
    text = """
    This is a test email to recruitment@kemuncaklanai.com
    
    Your KLSB notification system is working!
    You will receive CV and Proposal notifications here.
    """
    
    html = """
    <html>
      <body style="font-family: Arial, sans-serif; margin: 0; padding: 20px; background-color: #f3f4f6;">
        <div style="max-width: 600px; margin: 0 auto; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
          <div style="background: linear-gradient(135deg, #3b82f6 0%, #1d4ed8 100%); padding: 30px; text-align: center;">
            <h1 style="color: white; margin: 0; font-size: 24px;">✅ Test Email Successful!</h1>
          </div>
          <div style="padding: 30px;">
            <h2 style="color: #1f2937; margin-top: 0;">Email System Working!</h2>
            <p style="color: #4b5563; line-height: 1.6;">
              This is a test email to <strong>recruitment@kemuncaklanai.com</strong>
            </p>
            <div style="background: #f0fdf4; border-left: 4px solid #22c55e; padding: 15px; margin: 20px 0;">
              <p style="margin: 0; color: #166534;">
                ✅ Your KLSB notification system is configured correctly!
              </p>
            </div>
            <p style="color: #4b5563;">
              You will receive CV and Proposal notifications at this email address.
            </p>
          </div>
        </div>
      </body>
    </html>
    """
    
    msg.attach(MIMEText(text, 'plain'))
    msg.attach(MIMEText(html, 'html'))
    
    print("\n1. Connecting to Gmail SMTP...")
    server = smtplib.SMTP(smtp_server, smtp_port)
    server.starttls()
    
    print("2. Logging in...")
    server.login(sender_email, app_password)
    
    print("3. Sending email to recruitment@kemuncaklanai.com...")
    server.send_message(msg)
    
    print("4. Closing connection...")
    server.quit()
    
    print("\n" + "=" * 60)
    print("✅ Email Sent Successfully!")
    print("=" * 60)
    print(f"\nFrom: {sender_email}")
    print(f"To: {recipient_email}")
    print(f"Subject: {msg['Subject']}")
    print("\nPlease check recruitment@kemuncaklanai.com inbox!")
    print("Also check Spam/Junk folder if not in inbox.")
    print("=" * 60)

except Exception as e:
    print("\n❌ Error sending email:")
    print(str(e))
    print("\nPlease check:")
    print("1. Gmail App Password is correct")
    print("2. Internet connection is working")
    print("3. recruitment@kemuncaklanai.com is a valid email address")

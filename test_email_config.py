"""
Quick test to find the correct SMTP server for your email
Run this to test different mail server configurations
"""

import smtplib
from email.mime.text import MIMEText

email = "sysdev@kemuncaklanai.com"
password = "sysdeev@klsb"

# Common SMTP configurations to try
servers = [
    ("mail.kemuncaklanai.com", 587, True, "Custom domain - TLS"),
    ("mail.kemuncaklanai.com", 465, False, "Custom domain - SSL"),
    ("smtp.hostinger.com", 587, True, "Hostinger - TLS"),
    ("smtp.hostinger.com", 465, False, "Hostinger - SSL"),
    ("smtp.gmail.com", 587, True, "Gmail - TLS"),
    ("smtp.office365.com", 587, True, "Office365 - TLS"),
]

print(f"Testing SMTP for: {email}\n")
print("=" * 60)

for server, port, use_tls, description in servers:
    try:
        print(f"\nTrying: {description}")
        print(f"  Server: {server}:{port} (TLS: {use_tls})")
        
        if use_tls:
            smtp = smtplib.SMTP(server, port, timeout=10)
            smtp.starttls()
        else:
            smtp = smtplib.SMTP_SSL(server, port, timeout=10)
        
        smtp.login(email, password)
        print(f"  ✅ SUCCESS! Use this configuration:")
        print(f"     MAIL_SERVER = '{server}'")
        print(f"     MAIL_PORT = {port}")
        print(f"     MAIL_USE_TLS = {use_tls}")
        smtp.quit()
        break
        
    except Exception as e:
        print(f"  ❌ Failed: {str(e)[:100]}")

print("\n" + "=" * 60)

"""Send a test email using Shinjiru/cPanel SMTP using env vars.
Required env:
  MAIL_SERVER, MAIL_PORT, MAIL_USE_SSL or MAIL_USE_TLS, MAIL_USERNAME, MAIL_PASSWORD,
  MAIL_DEFAULT_SENDER, ADMIN_EMAIL
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

server = os.environ.get('MAIL_SERVER', 'mail.kemuncaklanai.com.my')
port = int(os.environ.get('MAIL_PORT', '465'))
use_ssl = os.environ.get('MAIL_USE_SSL', 'true').lower() in ('1','true','yes')
use_tls = os.environ.get('MAIL_USE_TLS', 'false').lower() in ('1','true','yes')
username = os.environ.get('MAIL_USERNAME','webnotify@kemuncaklanai.com.my')
password = os.environ.get('MAIL_PASSWORD','Web@notifykl$8')
sender = os.environ.get('MAIL_DEFAULT_SENDER','webnotify@kemuncaklanai.com.my')
recipient_str = os.environ.get('ADMIN_EMAIL','izzulamir1602@gmail.com,sysdev@kemuncaklanai.com')
# Support comma-separated recipients
recipient_list = [r.strip() for r in recipient_str.split(',') if r.strip()]
recipient = recipient_list[0] if recipient_list else username

missing = [k for k,v in [('MAIL_SERVER',server),('MAIL_USERNAME',username),('MAIL_PASSWORD',password)] if not v]
if missing:
    print("Missing required env vars:", ', '.join(missing))
    print("Set them in this PowerShell session and run again.")
    raise SystemExit(1)

msg = MIMEMultipart('alternative')
msg['Subject'] = '🔔 [IMPORTANT] KLSB Shinjiru SMTP Test'
msg['From'] = sender
# Put all recipients in the To header (comma-separated)
msg['To'] = ', '.join(recipient_list)
# Importance headers
msg['X-Priority'] = '1'
msg['Priority'] = 'urgent'
msg['Importance'] = 'high'

text = 'Shinjiru SMTP test from KLSB.'
html = '<h2>Shinjiru SMTP test</h2><p>If you see this, outbound works.</p>'
msg.attach(MIMEText(text,'plain'))
msg.attach(MIMEText(html,'html'))

def attempt_send(host, prt, mode):
    print(f"\nConnecting to {host}:{prt} mode={mode} ...")
    if mode == 'ssl':
        smtp = smtplib.SMTP_SSL(host, prt)
    else:
        smtp = smtplib.SMTP(host, prt)
    try:
        # Optional: enable SMTP protocol debug (uncomment if needed)
        # smtp.set_debuglevel(1)
        if mode == 'tls':
            smtp.starttls()
        user_mask = (username[:2] + '***@' + username.split('@')[-1]) if username else '(none)'
        print("Logging in as", user_mask)
        smtp.login(username, password)
        print("Sending to", ", ".join(recipient_list))
        smtp.sendmail(sender, recipient_list, msg.as_string())
        print("✅ Sent successfully!")
        return True
    except smtplib.SMTPAuthenticationError as e:
        print("❌ SMTP Authentication failed:", e)
        print("Hints:")
        print(" - Verify the EXACT mailbox password by logging into Webmail (https://" + host + "/ or :2096)")
        print(" - Username must be the FULL email address (e.g., recruitment@yourdomain)")
        print(" - If many failures happened, the server may temporarily lock the account")
        return False
    finally:
        try:
            smtp.quit()
        except Exception:
            pass

# Try the configured mode first
ok = attempt_send(server, port, 'ssl' if use_ssl else ('tls' if use_tls else 'plain'))

# Fallbacks if first attempt fails
if not ok and use_ssl:
    ok = attempt_send(server, 587, 'tls')
if not ok and use_tls:
    ok = attempt_send(server, 465, 'ssl')
if not ok:
    print("\nAll attempts failed. Please double-check your credentials and server/port from cPanel's 'Mail Client Manual Settings'.")

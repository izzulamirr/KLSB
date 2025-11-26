# Admin Notification Implementation Guide

This guide provides multiple methods to receive notifications when someone submits a CV or proposal.

---

## Option 1: Email Notifications (Recommended)

### Method A: Using Gmail SMTP (Simple & Free)

**Step 1:** Update `config.py`

```python
import os
from urllib.parse import quote_plus

class BaseConfig:
    # ... existing config ...
    
    # Email Configuration
    MAIL_SERVER = 'smtp.gmail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'your-app-password')  # Use App Password, not regular password
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_USERNAME', 'your-email@gmail.com')
    
    # Admin notification email
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL', 'admin@kemuncaklanai.com')
```

**Step 2:** Install Flask-Mail

```powershell
pip install Flask-Mail
```

**Step 3:** Update `app/__init__.py`

```python
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail

db = SQLAlchemy()
mail = Mail()

def create_app(config_class='config.DevConfig'):
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    db.init_app(app)
    mail.init_app(app)  # Add this line
    
    with app.app_context():
        from app.routes import main_bp
        app.register_blueprint(main_bp)
    
    return app
```

**Step 4:** Create email utility file `app/email_utils.py`

```python
from flask import current_app
from flask_mail import Message
from app import mail
from threading import Thread

def send_async_email(app, msg):
    """Send email asynchronously to avoid blocking the request."""
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            current_app.logger.error(f"Failed to send email: {str(e)}")

def send_email(subject, recipients, text_body=None, html_body=None):
    """Send email notification."""
    msg = Message(
        subject=subject,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=recipients
    )
    msg.body = text_body
    msg.html = html_body
    
    # Send asynchronously
    Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()

def notify_cv_submission(applicant_name, position, email):
    """Notify admin when CV is submitted."""
    subject = f"New CV Submission: {applicant_name}"
    recipients = [current_app.config['ADMIN_EMAIL']]
    
    text_body = f"""
New CV Submission Received

Applicant: {applicant_name}
Position: {position}
Email: {email}

Please log in to the admin panel to review the application.
Admin Panel: {current_app.config.get('SITE_URL', 'https://kemuncaklanai.com')}/admin/login
    """
    
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9fafb; border-radius: 8px;">
            <h2 style="color: #1e40af; margin-bottom: 20px;">New CV Submission 📄</h2>
            
            <div style="background-color: white; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
                <p style="margin: 10px 0;"><strong>Applicant:</strong> {applicant_name}</p>
                <p style="margin: 10px 0;"><strong>Position:</strong> {position}</p>
                <p style="margin: 10px 0;"><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
            </div>
            
            <a href="{current_app.config.get('SITE_URL', 'https://kemuncaklanai.com')}/admin/login" 
               style="display: inline-block; background-color: #3b82f6; color: white; padding: 12px 24px; 
                      text-decoration: none; border-radius: 6px; font-weight: bold;">
                Review in Admin Panel
            </a>
            
            <p style="margin-top: 30px; font-size: 12px; color: #6b7280;">
                This is an automated notification from Kemuncak Lanai Sdn Bhd
            </p>
        </div>
    </body>
    </html>
    """
    
    send_email(subject, recipients, text_body, html_body)

def notify_proposal_submission(company_name, service, email):
    """Notify admin when proposal is submitted."""
    subject = f"New Proposal Request: {company_name}"
    recipients = [current_app.config['ADMIN_EMAIL']]
    
    text_body = f"""
New Proposal Request Received

Company: {company_name}
Service: {service}
Email: {email}

Please log in to the admin panel to review the request.
Admin Panel: {current_app.config.get('SITE_URL', 'https://kemuncaklanai.com')}/admin/login
    """
    
    html_body = f"""
    <html>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
        <div style="max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f9fafb; border-radius: 8px;">
            <h2 style="color: #1e40af; margin-bottom: 20px;">New Proposal Request 📋</h2>
            
            <div style="background-color: white; padding: 20px; border-radius: 6px; margin-bottom: 20px;">
                <p style="margin: 10px 0;"><strong>Company:</strong> {company_name}</p>
                <p style="margin: 10px 0;"><strong>Service:</strong> {service}</p>
                <p style="margin: 10px 0;"><strong>Email:</strong> <a href="mailto:{email}">{email}</a></p>
            </div>
            
            <a href="{current_app.config.get('SITE_URL', 'https://kemuncaklanai.com')}/admin/login" 
               style="display: inline-block; background-color: #3b82f6; color: white; padding: 12px 24px; 
                      text-decoration: none; border-radius: 6px; font-weight: bold;">
                Review in Admin Panel
            </a>
            
            <p style="margin-top: 30px; font-size: 12px; color: #6b7280;">
                This is an automated notification from Kemuncak Lanai Sdn Bhd
            </p>
        </div>
    </body>
    </html>
    """
    
    send_email(subject, recipients, text_body, html_body)
```

**Step 5:** Update `app/routes.py` to send notifications

Add at the top:
```python
from app.email_utils import notify_cv_submission, notify_proposal_submission
```

In the `services_manpower_send_cv()` function, after successful database insert:
```python
# After: db.session.commit()
try:
    notify_cv_submission(full_name, position, email)
except Exception as e:
    current_app.logger.error(f"Failed to send notification email: {str(e)}")
    # Don't fail the request if email fails
```

In the `submit_proposal()` function, after successful database insert:
```python
# After: db.session.commit()
try:
    notify_proposal_submission(company_name, service, client_email)
except Exception as e:
    current_app.logger.error(f"Failed to send notification email: {str(e)}")
```

**Step 6:** Setup Gmail App Password

1. Go to Google Account settings
2. Enable 2-Step Verification
3. Generate an App Password (Security > App passwords)
4. Use this App Password in your environment variables

**Step 7:** Set environment variables (for production)

```powershell
# Windows PowerShell
$env:MAIL_USERNAME = "your-email@gmail.com"
$env:MAIL_PASSWORD = "your-app-password"
$env:ADMIN_EMAIL = "admin@kemuncaklanai.com"
```

---

## Option 2: Telegram Bot Notifications (Instant & Free)

**Step 1:** Create a Telegram Bot
1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow instructions
3. Save your Bot Token

**Step 2:** Get your Chat ID
1. Message your bot
2. Visit: `https://api.telegram.org/bot<YourBOTToken>/getUpdates`
3. Look for `"chat":{"id":123456789}`

**Step 3:** Install requests library
```powershell
pip install requests
```

**Step 4:** Add to `config.py`
```python
TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN', '')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '')
```

**Step 5:** Create `app/telegram_notify.py`
```python
import requests
from flask import current_app

def send_telegram_notification(message):
    """Send notification via Telegram bot."""
    bot_token = current_app.config.get('TELEGRAM_BOT_TOKEN')
    chat_id = current_app.config.get('TELEGRAM_CHAT_ID')
    
    if not bot_token or not chat_id:
        current_app.logger.warning("Telegram credentials not configured")
        return False
    
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "HTML"
    }
    
    try:
        response = requests.post(url, json=data, timeout=10)
        return response.status_code == 200
    except Exception as e:
        current_app.logger.error(f"Telegram notification failed: {str(e)}")
        return False

def notify_cv_telegram(applicant_name, position, email):
    message = f"""
🆕 <b>New CV Submission</b>

👤 <b>Applicant:</b> {applicant_name}
💼 <b>Position:</b> {position}
📧 <b>Email:</b> {email}

Review in admin panel
    """
    send_telegram_notification(message)

def notify_proposal_telegram(company_name, service, email):
    message = f"""
📋 <b>New Proposal Request</b>

🏢 <b>Company:</b> {company_name}
🔧 <b>Service:</b> {service}
📧 <b>Email:</b> {email}

Review in admin panel
    """
    send_telegram_notification(message)
```

**Step 6:** Import and call in `routes.py`
```python
from app.telegram_notify import notify_cv_telegram, notify_proposal_telegram

# In CV submission after db.session.commit():
notify_cv_telegram(full_name, position, email)

# In proposal submission after db.session.commit():
notify_proposal_telegram(company_name, service, client_email)
```

---

## Option 3: Browser Push Notifications (Admin Panel)

For real-time notifications in the admin panel when logged in.

**Step 1:** Create `app/static/js/admin-notifications.js`
```javascript
// Check for new submissions every 30 seconds
function checkNewSubmissions() {
    fetch('/admin/api/check-new-submissions')
        .then(response => response.json())
        .then(data => {
            if (data.has_new) {
                showNotification(data.message, data.count);
                // Optional: play sound
                playNotificationSound();
            }
        })
        .catch(error => console.error('Error checking submissions:', error));
}

function showNotification(message, count) {
    // Check if browser supports notifications
    if (!("Notification" in window)) return;
    
    // Request permission if not granted
    if (Notification.permission === "default") {
        Notification.requestPermission();
    }
    
    // Show notification if permission granted
    if (Notification.permission === "granted") {
        new Notification("KLSB Admin", {
            body: message,
            icon: "/static/img/logo/KLSB_full_bottom.svg",
            badge: count
        });
    }
}

function playNotificationSound() {
    const audio = new Audio('/static/sounds/notification.mp3');
    audio.play().catch(e => console.log('Could not play sound'));
}

// Start checking when page loads
document.addEventListener('DOMContentLoaded', function() {
    if (window.location.pathname.includes('/admin/')) {
        // Check immediately
        checkNewSubmissions();
        // Then check every 30 seconds
        setInterval(checkNewSubmissions, 30000);
        
        // Request notification permission
        if (Notification.permission === "default") {
            Notification.requestPermission();
        }
    }
});
```

**Step 2:** Add API endpoint in `routes.py`
```python
@main_bp.route("/admin/api/check-new-submissions")
@admin_required
def check_new_submissions():
    """Check for new submissions since last check."""
    from datetime import datetime, timedelta
    
    # Store last check time in session
    last_check = session.get('last_notification_check')
    if last_check:
        last_check = datetime.fromisoformat(last_check)
    else:
        last_check = datetime.now() - timedelta(minutes=5)
    
    # Count new submissions
    new_cvs = Applicant.query.filter(Applicant.created_at > last_check).count()
    new_proposals = Proposal.query.filter(Proposal.created_at > last_check).count()
    
    total_new = new_cvs + new_proposals
    has_new = total_new > 0
    
    # Update last check time
    session['last_notification_check'] = datetime.now().isoformat()
    
    message = ""
    if new_cvs > 0 and new_proposals > 0:
        message = f"{new_cvs} new CV(s) and {new_proposals} new proposal(s)"
    elif new_cvs > 0:
        message = f"{new_cvs} new CV submission(s)"
    elif new_proposals > 0:
        message = f"{new_proposals} new proposal request(s)"
    
    return jsonify({
        'has_new': has_new,
        'count': total_new,
        'new_cvs': new_cvs,
        'new_proposals': new_proposals,
        'message': message
    })
```

**Step 3:** Include script in `admin_applicants.html`
```html
{% block extra_body %}
<script src="{{ url_for('static', filename='js/admin-notifications.js') }}"></script>
{% endblock %}
```

---

## Option 4: WhatsApp Notifications (via Twilio)

**Step 1:** Sign up for Twilio (Free trial available)

**Step 2:** Install Twilio SDK
```powershell
pip install twilio
```

**Step 3:** Add to `config.py`
```python
TWILIO_ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID', '')
TWILIO_AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN', '')
TWILIO_WHATSAPP_FROM = os.environ.get('TWILIO_WHATSAPP_FROM', 'whatsapp:+14155238886')
ADMIN_WHATSAPP = os.environ.get('ADMIN_WHATSAPP', 'whatsapp:+60123456789')
```

**Step 4:** Create `app/whatsapp_notify.py`
```python
from twilio.rest import Client
from flask import current_app

def send_whatsapp_notification(message):
    """Send WhatsApp notification via Twilio."""
    try:
        account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
        auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
        
        if not account_sid or not auth_token:
            return False
        
        client = Client(account_sid, auth_token)
        
        message = client.messages.create(
            from_=current_app.config.get('TWILIO_WHATSAPP_FROM'),
            body=message,
            to=current_app.config.get('ADMIN_WHATSAPP')
        )
        
        return True
    except Exception as e:
        current_app.logger.error(f"WhatsApp notification failed: {str(e)}")
        return False
```

---

## Option 5: Discord Webhook (Free & Simple)

**Step 1:** Create Discord webhook
1. Go to your Discord server settings
2. Integrations > Webhooks > New Webhook
3. Copy webhook URL

**Step 2:** Add to `config.py`
```python
DISCORD_WEBHOOK_URL = os.environ.get('DISCORD_WEBHOOK_URL', '')
```

**Step 3:** Create `app/discord_notify.py`
```python
import requests
from flask import current_app

def send_discord_notification(title, description, color=0x3b82f6):
    """Send notification to Discord via webhook."""
    webhook_url = current_app.config.get('DISCORD_WEBHOOK_URL')
    
    if not webhook_url:
        return False
    
    data = {
        "embeds": [{
            "title": title,
            "description": description,
            "color": color,
            "footer": {"text": "Kemuncak Lanai Admin Notification"}
        }]
    }
    
    try:
        response = requests.post(webhook_url, json=data, timeout=10)
        return response.status_code == 204
    except Exception as e:
        current_app.logger.error(f"Discord notification failed: {str(e)}")
        return False

def notify_cv_discord(applicant_name, position, email):
    title = "🆕 New CV Submission"
    description = f"**Applicant:** {applicant_name}\n**Position:** {position}\n**Email:** {email}"
    send_discord_notification(title, description)

def notify_proposal_discord(company_name, service, email):
    title = "📋 New Proposal Request"
    description = f"**Company:** {company_name}\n**Service:** {service}\n**Email:** {email}"
    send_discord_notification(title, description)
```

---

## Recommended Implementation Strategy

### For Immediate Setup (30 minutes):
1. **Email notifications** (Option 1) - Most professional and reliable
2. **Telegram notifications** (Option 2) - For instant mobile alerts

### For Enhanced Experience (1 hour):
Add **Browser push notifications** (Option 3) for real-time admin panel updates

### Quick Start Commands:

```powershell
# Install required packages
pip install Flask-Mail requests

# Update requirements.txt
pip freeze > requirements.txt
```

---

## Testing Notifications

Create a test route to verify setup:

```python
@main_bp.route("/admin/test-notifications")
@admin_required
def test_notifications():
    """Test all notification methods."""
    try:
        from app.email_utils import notify_cv_submission
        notify_cv_submission("Test User", "Test Position", "test@example.com")
        flash("Test email sent!", "success")
    except Exception as e:
        flash(f"Email test failed: {str(e)}", "error")
    
    return redirect(url_for('main.admin_applicants'))
```

Access: `/admin/test-notifications` after logging in.

---

## Security Notes

1. **Never commit credentials** - Always use environment variables
2. **Use app passwords** for Gmail, not your main password
3. **Rate limit** notifications to prevent spam
4. **Validate webhook URLs** before using
5. **Use HTTPS** in production

---

Would you like me to implement any of these options for you?

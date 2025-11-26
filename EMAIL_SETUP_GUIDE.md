# Email Notification Setup Guide

Email notifications have been successfully implemented for CV and proposal submissions!

## 📧 What's Been Done

✅ **Config updated** - Email settings added to `config.py`
✅ **Flask-Mail installed** - Email package configured in `app/__init__.py`
✅ **Email utilities created** - Beautiful HTML email templates in `app/email_utils.py`
✅ **CV notifications** - Admins notified when someone submits a CV
✅ **Proposal notifications** - Admins notified when someone requests a proposal
✅ **Requirements updated** - Flask-Mail added to `requirements.txt`

---

## 🚀 Quick Setup (Gmail - Recommended)

### Step 1: Enable 2-Step Verification on Gmail

1. Go to [Google Account Security](https://myaccount.google.com/security)
2. Enable **2-Step Verification** if not already enabled

### Step 2: Create App Password

1. Go to [App Passwords](https://myaccount.google.com/apppasswords)
2. Select app: **Mail**
3. Select device: **Windows Computer** (or other)
4. Click **Generate**
5. **Copy the 16-character password** (e.g., `abcd efgh ijkl mnop`)

### Step 3: Set Environment Variables

**For Development (Windows PowerShell):**

```powershell
# Set for current session
$env:MAIL_USERNAME = "your-email@gmail.com"
$env:MAIL_PASSWORD = "abcd efgh ijkl mnop"  # Your App Password from Step 2
$env:ADMIN_EMAIL = "recruitment@kemuncaklanai.com"
$env:SITE_URL = "http://localhost:5000"

# Run your Flask app
python run.py
```

**For Production (Passenger/cPanel):**

Add these environment variables in your hosting control panel or `.htaccess`:

```bash
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
ADMIN_EMAIL=recruitment@kemuncaklanai.com
SITE_URL=https://kemuncaklanai.com
```

### Step 4: Test It!

1. Run your Flask app
2. Go to `/services/manpower/send-cv` or `/proposal`
3. Submit a test form
4. Check your `ADMIN_EMAIL` inbox!

---

## 📝 Configuration Details

### Email Settings (already configured in `config.py`)

```python
MAIL_SERVER = 'smtp.gmail.com'          # Gmail SMTP server
MAIL_PORT = 587                         # TLS port
MAIL_USE_TLS = True                     # Enable TLS encryption
MAIL_USERNAME = ''                      # Set via environment variable
MAIL_PASSWORD = ''                      # Set via environment variable (App Password)
MAIL_DEFAULT_SENDER = MAIL_USERNAME     # Sender email
ADMIN_EMAIL = 'recruitment@kemuncaklanai.com'  # Where notifications are sent
SITE_URL = 'http://localhost:5000'     # Your website URL
```

---

## 🎨 Email Templates

Both CV and Proposal notifications include:

✨ **Beautiful HTML design** with your brand colors
✨ **Mobile-responsive** layout
✨ **Direct link** to admin panel
✨ **All submission details** clearly displayed
✨ **Professional branding** with KLSB identity

### CV Notification Includes:
- Applicant name
- Position applied for
- Email address
- Availability date
- "Review in Admin Panel" button

### Proposal Notification Includes:
- Company name
- Service requested
- Client email
- Proposal details preview (first 200 chars)
- "Review in Admin Panel" button

---

## 🔧 Alternative Email Providers

### Microsoft Outlook/Office 365

```python
MAIL_SERVER = 'smtp.office365.com'
MAIL_PORT = 587
MAIL_USE_TLS = True
```

### Custom SMTP Server

```python
MAIL_SERVER = 'mail.yourdomain.com'
MAIL_PORT = 587  # or 465 for SSL
MAIL_USE_TLS = True  # or False if using SSL
```

---

## 🧪 Testing Notifications

### Option 1: Submit Real Form
- Visit your website and submit a CV or proposal
- Check the admin email inbox

### Option 2: Create Test Route (Optional)

Add this to `app/routes.py`:

```python
@main_bp.route("/admin/test-email")
@admin_required
def test_email():
    """Test email notifications."""
    try:
        from app.email_utils import notify_cv_submission, notify_proposal_submission
        
        # Test CV notification
        notify_cv_submission(
            "Test Applicant", 
            "Test Position", 
            "test@example.com", 
            "Immediate"
        )
        
        # Test Proposal notification
        notify_proposal_submission(
            "Test Company", 
            "Engineering Services", 
            "test@example.com",
            "This is a test proposal request with some details."
        )
        
        flash("Test emails sent! Check your inbox.", "success")
    except Exception as e:
        flash(f"Error: {str(e)}", "error")
    
    return redirect(url_for('main.admin_applicants'))
```

Then visit: `http://localhost:5000/admin/test-email` (after logging in)

---

## ⚙️ How It Works

1. **User submits CV or Proposal** → Form is validated
2. **Data saved to database** → MySQL insert successful
3. **Email sent asynchronously** → Doesn't block the response
4. **Admin receives notification** → Beautiful HTML email with all details
5. **Click button** → Direct link to admin panel to review

**Note:** Emails are sent in background threads, so even if email fails, the submission still succeeds!

---

## 🔒 Security Best Practices

✅ **Never commit credentials** - Always use environment variables
✅ **Use App Passwords** - Not your main Gmail password
✅ **Enable 2FA** - Required for App Passwords
✅ **HTTPS in production** - Secure email transmission
✅ **Graceful fallback** - App works even if email fails

---

## 🐛 Troubleshooting

### No emails received?

1. **Check environment variables are set:**
   ```powershell
   echo $env:MAIL_USERNAME
   echo $env:MAIL_PASSWORD
   ```

2. **Check spam/junk folder** in your email

3. **Check Flask logs** for errors:
   ```
   Failed to send email: [error message]
   ```

4. **Verify Gmail App Password** is correct (16 chars, no spaces)

5. **Test SMTP connection:**
   ```python
   from flask import Flask
   from flask_mail import Mail, Message
   
   app = Flask(__name__)
   app.config['MAIL_SERVER'] = 'smtp.gmail.com'
   app.config['MAIL_PORT'] = 587
   app.config['MAIL_USE_TLS'] = True
   app.config['MAIL_USERNAME'] = 'your-email@gmail.com'
   app.config['MAIL_PASSWORD'] = 'your-app-password'
   
   mail = Mail(app)
   
   with app.app_context():
       msg = Message('Test', sender=app.config['MAIL_USERNAME'], recipients=['test@example.com'])
       msg.body = 'Test email'
       mail.send(msg)
       print("Email sent!")
   ```

### "Authentication failed" error?

- You're using your regular Gmail password instead of an App Password
- 2-Step Verification is not enabled
- App Password has spaces (remove them)

### Email takes long to send?

- This is normal! Gmail SMTP can take 1-5 seconds
- Emails are sent asynchronously, so users won't notice
- Consider using a dedicated transactional email service for production (SendGrid, Mailgun, AWS SES)

---

## 🚀 Production Recommendations

For high-volume production use, consider:

1. **SendGrid** (12,000 free emails/month)
2. **Mailgun** (5,000 free emails/month)  
3. **AWS SES** (62,000 free emails/month)
4. **Postmark** (100 free emails/month, very reliable)

These services have better deliverability and don't get blocked like Gmail might for bulk emails.

---

## 📊 What Gets Logged

The system logs:
- ✅ Email sent successfully
- ❌ Failed to send email (with error message)
- ⚠️ Email not configured (graceful skip)

Check your Flask logs for email activity!

---

**Need help?** Check the `NOTIFICATION_IMPLEMENTATION_GUIDE.md` for more notification options (Telegram, WhatsApp, Discord, etc.)

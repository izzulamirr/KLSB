# 📧 Quick Start: Email Notifications

## ⚡ 3-Minute Setup

### 1️⃣ Get Gmail App Password
- Go to: https://myaccount.google.com/apppasswords
- Enable 2-Step Verification first if needed
- Generate app password (16 characters)

### 2️⃣ Set Environment Variables

**PowerShell (Windows):**
```powershell
$env:MAIL_USERNAME = "your-email@gmail.com"
$env:MAIL_PASSWORD = "your-16-char-app-password"
$env:ADMIN_EMAIL = "recruitment@kemuncaklanai.com"
$env:SITE_URL = "http://localhost:5000"
```

**Bash (Linux/Mac):**
```bash
export MAIL_USERNAME="your-email@gmail.com"
export MAIL_PASSWORD="your-16-char-app-password"
export ADMIN_EMAIL="recruitment@kemuncaklanai.com"
export SITE_URL="http://localhost:5000"
```

### 3️⃣ Run Your App
```powershell
python run.py
```

### 4️⃣ Test It!
- Submit a CV at: `/services/manpower/send-cv`
- Submit a proposal at: `/proposal`
- Check your admin email!

---

## ✅ What You Get

**When someone submits a CV:**
- 📧 Beautiful HTML email to admin
- 👤 Applicant details
- 💼 Position & availability
- 🔗 Direct link to admin panel

**When someone requests a proposal:**
- 📧 Beautiful HTML email to admin
- 🏢 Company details
- 🔧 Service requested
- 📄 Proposal details preview
- 🔗 Direct link to admin panel

---

## 🔧 For Production

Add these to your `.env` file or hosting environment variables:
```
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
ADMIN_EMAIL=recruitment@kemuncaklanai.com
SITE_URL=https://kemuncaklanai.com
```

---

## 📚 Full Documentation

See `EMAIL_SETUP_GUIDE.md` for:
- Detailed setup instructions
- Troubleshooting guide
- Alternative email providers
- Production recommendations
- Security best practices

---

**That's it!** Email notifications are ready to use! 🎉

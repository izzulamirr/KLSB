# 🚨 ADMIN SECURITY GUIDE - URGENT

## ⚠️ YOUR SITE IS UNDER BRUTE FORCE ATTACK

### IMMEDIATE ACTIONS REQUIRED (Do NOW on live server)

---

## 🔐 Step 1: Change Admin Password IMMEDIATELY

### Option A: Via cPanel Environment Variables (RECOMMENDED - No file upload)

1. **Login to cPanel**
2. **Go to**: Setup Python App → Select your app → Edit
3. **Set Environment Variables**:
   ```
   ADMIN_USER=admin_klsb_2025_secure
   ADMIN_PASS=YourStr0ng!P@ssw0rd#2025
   ```
4. **Click Save**
5. **Restart the application**
6. ✅ **Done! New credentials active immediately**

### Option B: Edit config.py (if you can't access cPanel env vars)

1. Edit `d:\KLSB\config.py` lines 8-9:
   ```python
   ADMIN_USER = os.environ.get("ADMIN_USER", "your_new_username_here")
   ADMIN_PASS = os.environ.get("ADMIN_PASS", "Your$ecureP@ssw0rd!2025")
   ```
2. Upload to server
3. Restart app

---

## 🛡️ Step 2: Deploy Rate Limiting (ALREADY UPDATED in code)

I've already added brute-force protection to your code:

**Files Updated:**
- ✅ `config.py` - Changed default password
- ✅ `routes.py` - Added rate limiting (5 attempts, 15 min lockout)

**What the rate limiter does:**
- Blocks IP after 5 failed login attempts
- 15-minute lockout period
- Logs all failed attempts
- Clears counter on successful login

**To deploy:**
1. Upload the updated `config.py` and `routes.py` files
2. Restart your Flask app
3. Monitor logs for attack attempts

---

## 📋 Step 3: Additional Security Measures

### A. Change Admin URL (hide /admin path)

**Current URL:** `https://yoursite.com/admin/login`  
**Problem:** Attackers know this common path

**Solution:** Add to `routes.py` (after line 30):
```python
# Hidden admin path - keep this secret!
@main_bp.route("/secure-management-panel-2025", methods=["GET", "POST"])
def admin_login_secure():
    return admin_login()
```

Then access admin via: `https://yoursite.com/secure-management-panel-2025`

### B. IP Whitelist (if you have static IP)

Add to `routes.py` admin_login function (after line 33):
```python
# Whitelist your office/home IPs
ALLOWED_IPS = ['YOUR.IP.ADDRESS.HERE', '203.0.113.0']
if client_ip not in ALLOWED_IPS:
    current_app.logger.warning(f"Unauthorized IP blocked: {client_ip}")
    abort(403)
```

Get your IP: Visit https://whatismyipaddress.com/

### C. Enable HTTPS (SSL Certificate)

- Get free SSL from Let's Encrypt via cPanel
- Force HTTPS redirect in `.htaccess`:
```apache
RewriteEngine On
RewriteCond %{HTTPS} off
RewriteRule ^(.*)$ https://%{HTTP_HOST}%{REQUEST_URI} [L,R=301]
```

### D. Add CAPTCHA to login page

Install Flask-Limiter or add Google reCAPTCHA to `admin_login.html`

---

## 🔍 Step 4: Monitor & Investigate

### Check server logs NOW

**cPanel → Errors → Error Log:**
Look for:
- Multiple failed login attempts from same IP
- Repeated 401/403 errors
- Pattern of requests to `/admin/login`

**Check access logs:**
```bash
tail -f ~/access-logs/yourdomain.com
```

### Block attacking IPs in cPanel

1. cPanel → Security → IP Blocker
2. Add suspicious IPs (check logs first)
3. Block entire ranges if needed (e.g., `123.45.67.0/24`)

### Check if database was compromised

Run in phpMyAdmin:
```sql
SELECT * FROM applicants ORDER BY created_at DESC LIMIT 10;
SELECT * FROM proposals ORDER BY created_at DESC LIMIT 10;
```

Look for:
- Suspicious recent entries
- Unusual timestamps
- Spam/test data

---

## ✅ SECURITY CHECKLIST

- [ ] Changed ADMIN_USER and ADMIN_PASS via environment variables
- [ ] Uploaded updated `config.py` and `routes.py` files
- [ ] Restarted Flask application
- [ ] Tested new login credentials work
- [ ] Verified rate limiting is active (try 5 wrong passwords)
- [ ] Checked error logs for attack IPs
- [ ] Blocked suspicious IPs in cPanel
- [ ] Enabled HTTPS/SSL certificate
- [ ] Changed admin URL to secret path (optional)
- [ ] Set up IP whitelist (optional, if static IP)
- [ ] Notified team of new credentials (securely)

---

## 🆘 EMERGENCY: If Attackers Got In

### If you suspect breach:

1. **Change ALL passwords immediately:**
   - Admin panel
   - Database (MySQL)
   - cPanel
   - Email accounts
   - SSH/FTP

2. **Check for backdoors:**
   ```bash
   # Search for suspicious PHP files
   find ~/public_html -name "*.php" -mtime -7
   # Look for hidden files
   ls -la ~/public_html
   ```

3. **Export all data:**
   - Download database backup
   - Export applicants/proposals CSVs
   - Keep for evidence

4. **Contact hosting support:**
   - Report breach to Shinjiru/cPanel support
   - Request security audit
   - Check if other accounts affected

5. **Consider temporary takedown:**
   - Put site in maintenance mode
   - Fix security issues
   - Restore from clean backup

---

## 📞 CONTACTS

**Hosting Support (Shinjiru):**  
https://www.shinjiru.com.my/support/

**Emergency Developer Contact:**  
(Add your contact details here)

---

## 🔒 STRONG PASSWORD REQUIREMENTS

✅ **Good passwords:**
- `Kl$B@2025!Secur3#Admin`
- `MyC0mp@ny#Str0ng!Pass`
- `S3cur3$2025!KL_Admin`

❌ **Bad passwords:**
- `klsb123` (current default - TOO WEAK!)
- `admin` / `password` / `123456`
- Company name
- Dictionary words

**Requirements:**
- Minimum 16 characters
- Mix: uppercase, lowercase, numbers, symbols
- No dictionary words
- Unique (not reused from other sites)

---

## 📝 POST-DEPLOYMENT VERIFICATION

After deploying changes, test:

1. **Login with NEW credentials** → Should work ✅
2. **Try OLD password 3 times** → Should fail ❌
3. **Try wrong password 6 times** → Should show "Too many attempts" ✅
4. **Check logs** → Should see lockout messages ✅
5. **Wait 15 minutes** → Should allow retry ✅

---

## 📊 MONITORING SETUP

Set up alerts for:
- Failed login attempts (> 3 per hour)
- New admin sessions from unknown IPs
- Database changes outside business hours
- Sudden traffic spikes to `/admin/*` paths

Consider: CloudFlare WAF, Fail2Ban, or ModSecurity

---

**Document created:** November 17, 2025  
**Priority:** CRITICAL  
**Status:** ACTION REQUIRED IMMEDIATELY


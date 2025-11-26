# config.py
import os
import re
from urllib.parse import quote_plus

class BaseConfig:

    ADMIN_USER = os.environ.get("ADMIN_USER", "klsbadmin")
    ADMIN_PASS = os.environ.get("ADMIN_PASS", "klsb123")

    # Google reCAPTCHA v2 - Get keys from https://www.google.com/recaptcha/admin
    RECAPTCHA_SITE_KEY = os.environ.get("RECAPTCHA_SITE_KEY", "")
    RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY", "")
    RECAPTCHA_ENABLED = bool(RECAPTCHA_SITE_KEY and RECAPTCHA_SECRET_KEY)

    # Rate limiting settings
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_LOCKOUT_DURATION = 900  # 15 minutes
    MAX_CV_SUBMISSIONS_PER_HOUR = 3
    MAX_PROPOSAL_SUBMISSIONS_PER_HOUR = 3
    MAX_FILE_SIZE_MB = 10

    SECRET_KEY = "4d453d84e5c971b955366b277637c340ed34d10b9b05850bd3e6dc24de04980d"
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Email Configuration - Shinjiru/cPanel SMTP for notifications
    # Typical settings: server = mail.your-domain, SSL on 465 OR TLS on 587 (choose one)
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'mail.kemuncaklanai.com.my')
    # Be resilient if MAIL_PORT is non-numeric; default to 465
    try:
        MAIL_PORT = int(os.environ.get('MAIL_PORT', 465))
    except (TypeError, ValueError):
        MAIL_PORT = 465
    # Only one of these should be true. Defaults: SSL (465) true, TLS false.
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'true').lower() in ['true', '1', 'yes']
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'false').lower() in ['true', '1', 'yes']

    # Helper to sanitize env values (trim whitespace and accidental quotes)
    def _clean_env(name, default=''):
        v = os.environ.get(name, default)
        if v is None:
            return ''
        return str(v).strip().strip("'\"")

    # Authenticate with a valid mailbox (recommended: recruitment inbox)
    MAIL_USERNAME = _clean_env('MAIL_USERNAME', 'webnotify@kemuncaklanai.com.my')
    # SECURITY: Do not hardcode passwords. Set via environment variable on the server/host.
    MAIL_PASSWORD = _clean_env('MAIL_PASSWORD', '')
    # Default sender should match the authenticated mailbox for best SPF/DMARC alignment
    MAIL_DEFAULT_SENDER = _clean_env('MAIL_DEFAULT_SENDER', 'webnotify@kemuncaklanai.com.my') or MAIL_USERNAME

    # Allow forcing synchronous sends (recommended on shared hosting like cPanel/Passenger)
    MAIL_SEND_ASYNC = os.environ.get('MAIL_SEND_ASYNC', 'false').lower() in ['true', '1', 'yes']
    # When true, send one email per recipient (isolates per-recipient failures and avoids server policies that only accept single RCPT)
    MAIL_SEND_INDIVIDUAL = os.environ.get('MAIL_SEND_INDIVIDUAL', 'true').lower() in ['true','1','yes']
    # Run a quick SMTP preflight (DNS/TCP/EHLO/login) before attempting to send
    MAIL_PREFLIGHT_ON_SEND = os.environ.get('MAIL_PREFLIGHT_ON_SEND', 'true').lower() in ['true','1','yes']

    # Admin notification email(s) - where CV and proposal notifications are sent
    # Default recipients (ensure correct domain: kemuncaklanai.com.my)
    # Accepts comma, semicolon or newline separated lists in the ADMIN_EMAIL env var
    ADMIN_EMAIL = _clean_env('ADMIN_EMAIL', 'sysdev@kemuncaklanai.com,izzulamir1602@gmail.com')

    def _split_recipients(raw):
        """Split a raw recipient string into a cleaned list."""
        if not raw:
            return []
        parts = [p.strip() for p in re.split(r"[,;\n]+", raw) if p.strip()]
        return parts

    ADMIN_RECIPIENTS = _split_recipients(ADMIN_EMAIL)

    def _split_recipients(raw):
        """Split a raw recipient string into a cleaned list.

        Accepts commas, semicolons, or newlines as separators and strips whitespace.
        Returns an empty list if input is empty or None.
        """
        if not raw:
            return []
        parts = [p.strip() for p in re.split(r"[,;\n]+", raw) if p.strip()]
        return parts

    ADMIN_RECIPIENTS = _split_recipients(ADMIN_EMAIL)

    # Site URL for links in emails
    SITE_URL = os.environ.get('SITE_URL', 'http://localhost:5000')

    DB_USER = "root"
    DB_PASS = ""             # contains @ and $, so we URL-encode below
    DB_NAME = "klsb_test"  # Set DB_NAME to klsb_test
    DB_HOST = "127.0.0.1"  # Use 127.0.0.1 to force TCP (avoids socket vs TCP host resolution differences)
    DB_PORT = "3306"

    user_q = quote_plus(DB_USER)
    pass_q = quote_plus(DB_PASS) if DB_PASS else ""
    db_q   = quote_plus(DB_NAME)

    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or (
        f"mysql+mysqlconnector://{user_q}:{pass_q}@{DB_HOST}:{DB_PORT}/{db_q}?charset=utf8mb4"
    )

class DevConfig(BaseConfig):
    DEBUG = True

class ProdConfig(BaseConfig):
    DEBUG = False
# config.py
import os
import re
import secrets
from urllib.parse import quote_plus

class BaseConfig:

    # SECURITY: No hardcoded fallback. Set ADMIN_USER/ADMIN_PASS via environment variables.
    ADMIN_USER = os.environ.get("ADMIN_USER", "klsbadmin")
    ADMIN_PASS = os.environ.get("ADMIN_PASS", "")

     # Google reCAPTCHA v2 - Get keys from https://www.google.com/recaptcha/admin
    # SECURITY: No hardcoded fallback. Set both via environment variables.
    RECAPTCHA_SITE_KEY = os.environ.get("RECAPTCHA_SITE_KEY", "")
    RECAPTCHA_SECRET_KEY = os.environ.get("RECAPTCHA_SECRET_KEY", "")
    RECAPTCHA_ENABLED = bool(RECAPTCHA_SITE_KEY and RECAPTCHA_SECRET_KEY)

    # Rate limiting settings
    MAX_LOGIN_ATTEMPTS = 5
    LOGIN_LOCKOUT_DURATION = 900  # 15 minutes
    MAX_CV_SUBMISSIONS_PER_HOUR = 3
    MAX_PROPOSAL_SUBMISSIONS_PER_HOUR = 3
    MAX_FILE_SIZE_MB = 10
    
    # OpenAI Configuration for ChatGPT OCR
    # SECURITY: No hardcoded fallback. Set OPENAI_API_KEY via environment variable.
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY', '')

    USE_CHATGPT_OCR = True  # ChatGPT OCR enabled

    # SECURITY: No hardcoded fallback. Set SECRET_KEY via environment variable in
    # production (sessions/flash messages are signed with this). Falls back to a
    # random key generated at process start so local dev still works, but this
    # means sessions won't survive a restart unless SECRET_KEY is set explicitly.
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
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
    ADMIN_EMAIL = _clean_env('ADMIN_EMAIL', 'aininsofiya.a@kemuncaklanai.com.my,hafiz.azizan@kemuncaklanai.com,faris@kemuncaklanai.com,costner@kemuncaklanai.com,izzulamir@kemuncaklanai.com.my')

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
    SITE_URL = os.environ.get('SITE_URL', 'https://kemuncaklanai.com.my/')

    # Local dev defaults; override via env vars in production (values may contain
    # @ and $, so we URL-encode below).
    DB_USER = os.environ.get("DB_USER", "root")
    DB_PASS = os.environ.get("DB_PASS", "")
    DB_NAME = os.environ.get("DB_NAME", "klsb_test")

    # DB_HOST may be given as "host" or "host:port" (some hosting panels store it
    # that way) - tolerate both rather than producing a malformed "host:port:port" URL.
    _db_host_raw = os.environ.get("DB_HOST", "localhost")
    if ":" in _db_host_raw:
        DB_HOST, _host_embedded_port = _db_host_raw.rsplit(":", 1)
    else:
        DB_HOST, _host_embedded_port = _db_host_raw, None
    DB_PORT = os.environ.get("DB_PORT") or _host_embedded_port or "3306"

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
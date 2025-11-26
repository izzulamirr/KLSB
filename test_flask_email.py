"""Test Flask-Mail configuration from within the app context."""
from app import create_app
from app.email_utils import notify_cv_submission

# Create app with DevConfig
app = create_app()

with app.app_context():
    print("=" * 60)
    print("Flask Email Configuration Test")
    print("=" * 60)
    
    # Check config
    print(f"\nMAIL_SERVER: {app.config.get('MAIL_SERVER')}")
    print(f"MAIL_PORT: {app.config.get('MAIL_PORT')}")
    print(f"MAIL_USE_SSL: {app.config.get('MAIL_USE_SSL')}")
    print(f"MAIL_USE_TLS: {app.config.get('MAIL_USE_TLS')}")
    print(f"MAIL_USERNAME: {app.config.get('MAIL_USERNAME')}")
    
    # Check password (masked)
    pwd = app.config.get('MAIL_PASSWORD')
    if pwd:
        print(f"MAIL_PASSWORD: {'*' * len(pwd)} (length: {len(pwd)})")
    else:
        print("MAIL_PASSWORD: NOT SET ❌")
    
    print(f"MAIL_DEFAULT_SENDER: {app.config.get('MAIL_DEFAULT_SENDER')}")
    print(f"ADMIN_EMAIL: {app.config.get('ADMIN_EMAIL')}")
    
    # Try to send a test notification
    print("\n" + "=" * 60)
    print("Attempting to send test CV notification...")
    print("=" * 60)
    
    try:
        notify_cv_submission(
            applicant_name="Test User from Flask",
            position="Software Engineer",
            email="test@example.com",
            availability="Immediate"
        )
        print("\n✅ Notification queued (async). Check your email inbox.")
        print("If email doesn't arrive, check app logs for errors.")
    except Exception as e:
        print(f"\n❌ Error: {e}")
    
    # Give async thread time to send
    import time
    print("\nWaiting 3 seconds for async email to send...")
    time.sleep(3)
    print("Done. Check izzulamir@kemuncaklanai.com.my inbox (and Spam).")

from flask import current_app
from flask_mail import Message
from app import mail
from threading import Thread
import os
import mimetypes
import smtplib

def send_async_email(app, msg):
    """Send email asynchronously to avoid blocking the request."""
    with app.app_context():
        try:
            mail.send(msg)
            app.logger.info(f"Email sent successfully: {msg.subject}")
        except Exception as e:
            # Provide richer diagnostic logging for SMTP auth/errors
            try:
                if isinstance(e, smtplib.SMTPAuthenticationError):
                    # SMTPAuthenticationError exposes smtp_code and smtp_error
                    smtp_code = getattr(e, 'smtp_code', None)
                    smtp_err = getattr(e, 'smtp_error', None)
                    app.logger.error(f"Failed to send email: SMTP auth error {smtp_code} {smtp_err!r}")
                    # Try a manual fallback send (SSL/TLS alternates) to diagnose or succeed
                    try:
                        _attempt_manual_smtp_send(app, msg)
                    except Exception as _ef:
                        app.logger.error(f"Fallback manual SMTP attempt failed: {_ef!r}")
                else:
                    app.logger.error(f"Failed to send email: {repr(e)}")
            except Exception:
                # Ensure we never lose the original exception
                app.logger.error(f"Failed to send email (exception while logging): {repr(e)}")


def _attempt_manual_smtp_send(app, msg):
    """Attempt to send the given Flask-Mail Message manually over smtplib using common SSL/TLS ports.

    This acts as a fallback diagnostic/send when Flask-Mail's built-in send fails with auth errors.
    It will try combinations: configured mode first, then common alternates (SSL 465, TLS 587).
    """
    cfg = app.config
    server = cfg.get('MAIL_SERVER')
    port = cfg.get('MAIL_PORT') or 465
    use_ssl = bool(cfg.get('MAIL_USE_SSL'))
    use_tls = bool(cfg.get('MAIL_USE_TLS'))
    username = cfg.get('MAIL_USERNAME')
    password = cfg.get('MAIL_PASSWORD')
    sender = cfg.get('MAIL_DEFAULT_SENDER')
    recipients = msg.recipients if hasattr(msg, 'recipients') else cfg.get('ADMIN_RECIPIENTS') or []

    attempts = []
    # Determine attempt sequence: prefer configured, then try common alternates
    if use_ssl:
        attempts.append(('ssl', server, port))
        attempts.append(('tls', server, 587))
    elif use_tls:
        attempts.append(('tls', server, port))
        attempts.append(('ssl', server, 465))
    else:
        # Try both common combos
        attempts.append(('ssl', server, 465))
        attempts.append(('tls', server, 587))

    last_exc = None
    for mode, host, prt in attempts:
        app.logger.info(f"Fallback attempt: mode={mode} host={host} port={prt} user={'(hidden)'} recipients={recipients}")
        try:
            if mode == 'ssl':
                smtp = smtplib.SMTP_SSL(host, prt, timeout=20)
            else:
                smtp = smtplib.SMTP(host, prt, timeout=20)
            try:
                smtp.ehlo()
                if mode == 'tls':
                    smtp.starttls()
                    smtp.ehlo()
                smtp.login(username, password)
                smtp.sendmail(sender, recipients, msg.as_string())
                app.logger.info(f"Fallback manual send succeeded via {mode}:{prt}")
                try:
                    smtp.quit()
                except Exception:
                    pass
                return True
            finally:
                try:
                    smtp.quit()
                except Exception:
                    pass
        except Exception as e:
            last_exc = e
            app.logger.error(f"Fallback attempt {mode}:{prt} failed: {repr(e)}")

    # If we reach here, all attempts failed
    raise last_exc or RuntimeError('All fallback SMTP attempts failed')

def send_email(subject, recipients, text_body=None, html_body=None):
    """Send email notification."""
    # Optional: run preflight SMTP diagnose to surface live hosting issues early
    try:
        if current_app.config.get('MAIL_PREFLIGHT_ON_SEND', True):
            from .smtp_utils import run_smtp_diagnose
            report, code = run_smtp_diagnose(current_app)
            if code != 200:
                current_app.logger.warning(f"SMTP preflight warnings: {report}")
            else:
                current_app.logger.info("SMTP preflight OK")
    except Exception as _pf_e:
        current_app.logger.debug(f"SMTP preflight skipped/failed silently: {_pf_e}")
    # Skip if email is not configured
    if not current_app.config.get('MAIL_USERNAME') or not current_app.config.get('MAIL_PASSWORD'):
        current_app.logger.warning("Email not configured (username/password missing) - skipping notification")
        return
    
    # Build a message factory so we can send per-recipient if configured
    def _build_message(to_recipients):
        m = Message(
            subject=subject,
            sender=current_app.config['MAIL_DEFAULT_SENDER'],
            recipients=to_recipients if isinstance(to_recipients, list) else [to_recipients]
        )
        m.body = text_body
        m.html = html_body
        return m

    # Quick diagnostics: ensure recipients is a list and present
    if not recipients:
        current_app.logger.warning("No recipients provided for email; skipping send")
        return

    # Log the mail configuration (mask sensitive parts) to help diagnose 535 errors
    try:
        masked_user = None
        mu = current_app.config.get('MAIL_USERNAME')
        if mu:
            masked_user = mu if len(mu) <= 6 else (mu[:3] + '...' + mu.split('@')[-1])
        mail_cfg = {
            'MAIL_SERVER': current_app.config.get('MAIL_SERVER'),
            'MAIL_PORT': current_app.config.get('MAIL_PORT'),
            'MAIL_USE_SSL': current_app.config.get('MAIL_USE_SSL'),
            'MAIL_USE_TLS': current_app.config.get('MAIL_USE_TLS'),
            'MAIL_USERNAME': masked_user,
        }
        current_app.logger.info(f"Sending email using: {mail_cfg}; recipients: {recipients}")
    except Exception as _:
        current_app.logger.debug("Failed to read mail config for diagnostics")

    def _embed_logo(message_obj):
        # Embed company logo inline so mail clients display it without fetching remote images
        try:
            logo_path = os.path.join(current_app.root_path, 'static', 'img', 'logo', 'KLSB Diamond 1 .png')
            if os.path.exists(logo_path):
                with open(logo_path, 'rb') as f:
                    logo_data = f.read()
                ctype, _ = mimetypes.guess_type(logo_path)
                if not ctype:
                    ctype = 'image/png'
                message_obj.attach('KLSB Diamond 1 .png', ctype, logo_data, 'inline', headers={'Content-ID': '<logo_cid>'})
        except Exception as e:
            current_app.logger.debug(f"Could not embed logo inline: {e}")

    def _apply_headers(message_obj):
        # Mark as IMPORTANT with yellow flag (Gmail Important marker)
        message_obj.extra_headers = {
            'X-Priority': '1',
            'Priority': 'urgent',
            'Importance': 'high',
            'X-MSMail-Priority': 'High',
            'X-Gmail-Labels': 'Important',
            'X-Mailer-Priority': '1',
            'X-PM-Message-Priority': 'high'
        }

    # Send messages: either per-recipient (safer) or in one go
    send_individual = current_app.config.get('MAIL_SEND_INDIVIDUAL', True)
    try:
        send_async = bool(current_app.config.get('MAIL_SEND_ASYNC', False))
    except Exception:
        send_async = False
    # On Passenger/cPanel, background threads may not run reliably; force sync
    try:
        import os as _os
        if _os.environ.get('PASSENGER_APP_ENV') or _os.environ.get('PASSENGER_ROOT'):
            send_async = False
    except Exception:
        pass

    if send_individual:
        for r in recipients:
            msg = _build_message(r)
            _embed_logo(msg)
            _apply_headers(msg)
            current_app.logger.info(f"Queueing send to: {r}")
            if send_async:
                Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()
            else:
                send_async_email(current_app._get_current_object(), msg)
    else:
        msg = _build_message(recipients)
        _embed_logo(msg)
        _apply_headers(msg)
        if send_async:
            Thread(target=send_async_email, args=(current_app._get_current_object(), msg)).start()
        else:
            send_async_email(current_app._get_current_object(), msg)

def notify_cv_submission(applicant_name, position, email, availability=None):
    """Notify admin when CV is submitted."""
    subject = f"🔔 [IMPORTANT] New CV Submission: {applicant_name}"
    # Support multiple recipients configured in config: ADMIN_RECIPIENTS (preferred) or ADMIN_EMAIL
    recipients = current_app.config.get('ADMIN_RECIPIENTS') or [r.strip() for r in current_app.config.get('ADMIN_EMAIL', '').split(',') if r.strip()]
    
    availability_text = f"\nAvailability: {availability}" if availability else ""
    
    text_body = f"""
New CV Submission Received

Applicant: {applicant_name}
Position: {position}
Email: {email}{availability_text}

Please log in to the admin panel to review the application.
Admin Panel: {current_app.config.get('SITE_URL')}/admin/login

---
This is an automated notification from Kemuncak Lanai Sdn Bhd
    """
    
    availability_html = f"<p style='margin: 10px 0;'><strong>Availability:</strong> {availability}</p>" if availability else ""
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4;">
        <div style="max-width: 600px; margin: 20px auto; padding: 0; background-color: #f9fafb;">
            <!-- Header with logo -->
            <div style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); padding: 18px 20px; text-align: center;">
                <div style="display:flex; align-items:center; justify-content:center; gap:12px;">
                    <img src="cid:logo_cid" alt="Kemuncak Lanai" style="height:48px; width:auto; border-radius:6px; background:white; padding:4px;" />
                    <div style="text-align:left;">
                        <h1 style="color: white; margin: 0; font-size: 20px; font-weight: 700;">New CV Submission</h1>
                        <p style="color: #e0e7ff; margin: 6px 0 0 0; font-size: 13px;">Kemuncak Lanai Sdn Bhd</p>
                    </div>
                </div>
            </div>
            
            <!-- Content -->
            <div style="padding: 30px 20px;">
                <div style="background-color: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;">
                    <p style="margin: 0 0 20px 0; font-size: 16px; color: #1e293b;">
                        A new CV has been submitted through your website. Please review the details below:
                    </p>
                    
                    <div style="background-color: #f8fafc; padding: 20px; border-radius: 6px; border-left: 4px solid #3b82f6;">
                        <p style="margin: 10px 0;"><strong style="color: #1e40af;">Applicant:</strong> {applicant_name}</p>
                        <p style="margin: 10px 0;"><strong style="color: #1e40af;">Position:</strong> {position}</p>
                        <p style="margin: 10px 0;"><strong style="color: #1e40af;">Email:</strong> <a href="mailto:{email}" style="color: #3b82f6; text-decoration: none;">{email}</a></p>
                        {availability_html}
                    </div>
                </div>
                
                <!-- CTA Button -->
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{current_app.config.get('SITE_URL')}/admin/login" 
                       style="display: inline-block; background-color: #3b82f6; color: white; padding: 14px 32px; 
                              text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px;
                              box-shadow: 0 4px 6px rgba(59, 130, 246, 0.3);">
                        Review in Admin Panel
                    </a>
                </div>
            </div>
            
            <!-- Footer -->
            <div style="background-color: #1e293b; padding: 20px; text-align: center;">
                <p style="margin: 0; font-size: 12px; color: #94a3b8;">
                    This is an automated notification from Kemuncak Lanai Sdn Bhd<br>
                    <a href="{current_app.config.get('SITE_URL')}" style="color: #60a5fa; text-decoration: none;">www.kemuncaklanai.com</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    send_email(subject, recipients, text_body, html_body)

def notify_proposal_submission(company_name, service, email, proposal_details=None):
    """Notify admin when proposal is submitted."""
    subject = f"🔔 [IMPORTANT] New Proposal Request: {company_name}"
    # Support multiple recipients configured in config: ADMIN_RECIPIENTS (preferred) or ADMIN_EMAIL
    recipients = current_app.config.get('ADMIN_RECIPIENTS') or [r.strip() for r in current_app.config.get('ADMIN_EMAIL', '').split(',') if r.strip()]
    
    details_preview = ""
    if proposal_details:
        # Truncate to first 200 chars for preview
        preview = proposal_details[:200]
        if len(proposal_details) > 200:
            preview += "..."
        details_preview = f"\nDetails Preview: {preview}"
    
    text_body = f"""
New Proposal Request Received

Company: {company_name}
Service: {service}
Email: {email}{details_preview}

Please log in to the admin panel to review the full request.
Admin Panel: {current_app.config.get('SITE_URL')}/admin/login

---
This is an automated notification from Kemuncak Lanai Sdn Bhd
    """
    
    details_html = ""
    if proposal_details:
        preview = proposal_details[:200]
        if len(proposal_details) > 200:
            preview += "..."
        details_html = f"""
        <div style="margin-top: 15px; padding-top: 15px; border-top: 1px solid #e2e8f0;">
            <p style="margin: 0 0 10px 0;"><strong style="color: #1e40af;">Details Preview:</strong></p>
            <p style="margin: 0; color: #475569; font-size: 14px; font-style: italic;">"{preview}"</p>
        </div>
        """
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; margin: 0; padding: 0; background-color: #f4f4f4;">
        <div style="max-width: 600px; margin: 20px auto; padding: 0; background-color: #f9fafb;">
            <!-- Header with logo -->
            <div style="background: linear-gradient(135deg, #1e40af 0%, #3b82f6 100%); padding: 18px 20px; text-align: center;">
                <div style="display:flex; align-items:center; justify-content:center; gap:12px;">
                    <img src="cid:logo_cid" alt="Kemuncak Lanai" style="height:48px; width:auto; border-radius:6px; background:white; padding:4px;" />
                    <div style="text-align:left;">
                        <h1 style="color: white; margin: 0; font-size: 20px; font-weight: 700;">📋 New Proposal Request</h1>
                        <p style="color: #e0e7ff; margin: 6px 0 0 0; font-size: 13px;">Kemuncak Lanai Sdn Bhd</p>
                    </div>
                </div>
            </div>
            
            <!-- Content -->
            <div style="padding: 30px 20px;">
                <div style="background-color: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); margin-bottom: 20px;">
                    <p style="margin: 0 0 20px 0; font-size: 16px; color: #1e293b;">
                        A new proposal request has been submitted through your website. Please review the details below:
                    </p>
                    
                    <div style="background-color: #f8fafc; padding: 20px; border-radius: 6px; border-left: 4px solid #10b981;">
                        <p style="margin: 10px 0;"><strong style="color: #1e40af;">Company:</strong> {company_name}</p>
                        <p style="margin: 10px 0;"><strong style="color: #1e40af;">Service:</strong> {service}</p>
                        <p style="margin: 10px 0;"><strong style="color: #1e40af;">Email:</strong> <a href="mailto:{email}" style="color: #3b82f6; text-decoration: none;">{email}</a></p>
                        {details_html}
                    </div>
                </div>
                
                <!-- CTA Button -->
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{current_app.config.get('SITE_URL')}/admin/login" 
                       style="display: inline-block; background-color: #10b981; color: white; padding: 14px 32px; 
                              text-decoration: none; border-radius: 6px; font-weight: bold; font-size: 16px;
                              box-shadow: 0 4px 6px rgba(16, 185, 129, 0.3);">
                        Review in Admin Panel
                    </a>
                </div>
            </div>
            
            <!-- Footer -->
            <div style="background-color: #1e293b; padding: 20px; text-align: center;">
                <p style="margin: 0; font-size: 12px; color: #94a3b8;">
                    This is an automated notification from Kemuncak Lanai Sdn Bhd<br>
                    <a href="{current_app.config.get('SITE_URL')}" style="color: #60a5fa; text-decoration: none;">www.kemuncaklanai.com</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """
    
    send_email(subject, recipients, text_body, html_body)

import socket, smtplib, ssl
from flask import current_app


def run_smtp_diagnose(app=None):
    """
    Perform SMTP diagnostics using current Flask app config.
    Returns (report: dict, status_code: int)
    """
    app = app or current_app
    cfg = app.config
    server = cfg.get('MAIL_SERVER')
    port = int(cfg.get('MAIL_PORT') or 0)
    use_ssl = bool(cfg.get('MAIL_USE_SSL'))
    use_tls = bool(cfg.get('MAIL_USE_TLS'))
    username = cfg.get('MAIL_USERNAME') or ''
    password = cfg.get('MAIL_PASSWORD') or ''
    sender = cfg.get('MAIL_DEFAULT_SENDER') or ''
    recipients = cfg.get('ADMIN_RECIPIENTS') or []

    def _mask(s: str):
        if not s:
            return s
        if '@' in s:
            name, _, dom = s.partition('@')
            return (name[:2] + '***@' + dom) if name else '***@' + dom
        return s[:3] + '***' if len(s) > 6 else '***'

    report = {
        'config': {
            'MAIL_SERVER': server,
            'MAIL_PORT': port,
            'MAIL_USE_SSL': use_ssl,
            'MAIL_USE_TLS': use_tls,
            'MAIL_USERNAME': _mask(username),
            'MAIL_DEFAULT_SENDER': _mask(sender),
            'ADMIN_RECIPIENTS': recipients,
            'HAS_PASSWORD': bool(password),
        },
        'checks': {}
    }

    if not server or not port:
        report['checks']['config'] = 'FAIL: MAIL_SERVER/MAIL_PORT not set'
        return report, 500
    if not username or not password:
        report['checks']['auth_env'] = 'WARN: MAIL_USERNAME/PASSWORD not set; sending will be skipped by app'

    # DNS resolution
    try:
        addrs = socket.getaddrinfo(server, port, proto=socket.IPPROTO_TCP)
        ips = list({ai[4][0] for ai in addrs})
        report['checks']['dns'] = {'status': 'OK', 'ips': ips}
    except Exception as e:
        report['checks']['dns'] = {'status': 'FAIL', 'error': str(e)}
        return report, 500

    # TCP connect
    try:
        with socket.create_connection((server, port), timeout=10) as s:
            report['checks']['tcp_connect'] = 'OK'
    except Exception as e:
        report['checks']['tcp_connect'] = f'FAIL: {e}'
        return report, 500

    # SMTP handshake and optional login
    try:
        if use_ssl:
            context = ssl.create_default_context()
            smtp = smtplib.SMTP_SSL(server, port, timeout=15, context=context)
        else:
            smtp = smtplib.SMTP(server, port, timeout=15)
        try:
            code, hello = smtp.ehlo()
            report['checks']['smtp_ehlo'] = f'OK: {code}'
            if use_tls and not use_ssl:
                code, resp = smtp.starttls()
                report['checks']['starttls'] = f'OK: {code}'
                smtp.ehlo()
            if username and password:
                smtp.login(username, password)
                report['checks']['login'] = 'OK'
            else:
                report['checks']['login'] = 'SKIPPED (no creds)'
            try:
                smtp.quit()
            except Exception:
                pass
        finally:
            try:
                smtp.quit()
            except Exception:
                pass
    except smtplib.SMTPAuthenticationError as e:
        report['checks']['login'] = f"FAIL AUTH: {getattr(e, 'smtp_code', '?')}: {getattr(e, 'smtp_error', e)}"
        return report, 500
    except Exception as e:
        report['checks']['smtp'] = f'FAIL: {e}'
        return report, 500

    return report, 200

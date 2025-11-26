# KLSB Draft Flask Site

A modern Flask starter with theming, responsive layout, and test scaffolding.

## Features
- Flask app factory pattern
- Routes: `/`, `/about`, `/healthz`
- Modular CSS architecture (tokens, base, layout, utilities, components, page-specific)
- Modern responsive homepage (hero, metrics, testimonials, CTA) with dark mode
- Light/Dark theme toggle using `data-theme` + CSS custom properties
- Pytest tests (4 passing)

## Setup (Windows PowerShell)
```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

## Run Dev Server
```powershell
python run.py
```
Visit http://127.0.0.1:5000

## Run Tests
```powershell
pytest -q
```

## Deploying to cPanel (Passenger WSGI)

These steps deploy the Flask app on a typical cPanel host with Python App support (Phusion Passenger/WSGI).

1) Upload these files/folders to your app directory on the server:
  - app/ (all files inside)
  - templates/ and static/ are already under app/
  - uploads/ (keep folder; ensure it’s writable) and its subfolder uploads/cv/
  - config.py, passenger_wsgi.py, requirements.txt, run.py
  - instance/ (if present) for per‑env stuff; ensure it’s writable if used

2) In cPanel → Setup Python App:
  - Select a Python version compatible with requirements (3.8+ recommended)
  - Application startup file: passenger_wsgi.py
  - Application entry point: application
  - Create a virtualenv (the UI will do this) and then install deps:
    - Use the “Add Requirement” UI or run: pip install -r requirements.txt

3) Environment variables (set in the Python App UI):
  - MAIL_SERVER=mail.kemuncaklanai.com.my
  - MAIL_PORT=465             (or 587 if using TLS)
  - MAIL_USE_SSL=true         (set to false if you use TLS)
  - MAIL_USE_TLS=false        (set to true if you use port 587)
  - MAIL_USERNAME=webnotify@kemuncaklanai.com.my
  - MAIL_PASSWORD=<your-smtp-password>
  - MAIL_DEFAULT_SENDER=webnotify@kemuncaklanai.com.my
  - ADMIN_EMAIL=sysdev@kemuncaklanai.com.my,izzulamir1602@gmail.com
  - SITE_URL=https://your-domain
  - Optional for debugging:
    - MAIL_SEND_ASYNC=true
    - MAIL_SEND_INDIVIDUAL=true
  - Optional DB override (if not using local MySQL defaults):
    - DATABASE_URL=mysql+mysqlconnector://user:pass@host:3306/dbname?charset=utf8mb4

4) File/folder permissions
  - Ensure uploads/ and uploads/cv/ are writable by the web user (e.g., 755/775).

5) Verify email works
  - Log in to /admin/login, then visit /admin/test-email
  - Check admin inboxes listed in ADMIN_EMAIL for two test notifications (CV + Proposal).
  - If a 535 auth error appears in app logs, confirm MAIL_* creds, port and SSL/TLS mode.

6) Database
  - By default the app uses local MySQL (localhost:3306, db klsb_test, user root, no password).
  - On production, set DATABASE_URL as shown above to point to your hosting DB.

Notes
- The app embeds the inline logo at app/static/img/logo/KLSB Diamond 1 .png in outgoing emails.
- You can add or change recipients with the ADMIN_EMAIL env var (comma‑separated list).
 

## CSS Structure
Located under `app/static/css/`:
- `variables.css` – design tokens (colors, spacing, fonts, shadows)
- `base.css` – resets, typography, global element styles
- `layout.css` – structural containers (header, footer, generic hero)
- `utilities.css` – utility classes (flex helpers, spacing, fade-in)
- `components.css` – buttons, cards, navigation, panel component
- `home.css` – homepage-specific sections (market hero, logos bar, features, metrics, testimonials, CTA)
- `style.css` – deprecated placeholder (kept only for backwards compatibility; safe to delete)

To add page‑specific styles create `page-name.css` and include in that template via:
```jinja2
{% block extra_head %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/page-name.css') }}">
{% endblock %}
```

## Static Assets
Place images in `app/static/img/` (e.g. `hero.jpg`). Reference in CSS as `/static/img/hero.jpg` or in templates via `url_for('static', filename='img/hero.jpg')`.

## Theming
- Persisted in `localStorage` key `klsb-theme`
- Override or add tokens in `variables.css`
- Dark mode handled by `[data-theme='dark']` selectors

## Project Structure
```
app/
  __init__.py
  routes.py
  templates/
    base.html
    index.html
    about.html
  static/
    css/
      variables.css
      base.css
      layout.css
      utilities.css
      components.css
      home.css
      style.css (deprecated)
    img/
      hero.jpg (optional)
```

## Environment Variables
Use a `.env` file for secrets like `SECRET_KEY`.

## Extending Ideas
- Database (SQLAlchemy + Alembic)
- Blueprints (`api`, `auth`)
- Forms & validation (Flask-WTF)
- Background tasks (RQ / Celery)
- Asset build pipeline (minify + hash)
- Docker container + CI workflow

## Accessibility
- Skip link included; maintain contrast when adjusting palette.

## License
Specify license here (MIT recommended) if publishing.

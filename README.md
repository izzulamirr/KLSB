# KLSB Draft Flask Site

A modern Flask starter with theming, responsive layout, and test scaffolding.

## Features
- Flask app factory pattern
- Routes: `/`, `/about`, `/healthz`
- Modern responsive layout (marketplace hero, glass panel)
- Light/Dark theme toggle with `data-theme` & CSS custom properties
- Design tokens in `app/static/css/variables.css`
- Static assets served from `app/static` (Flask default with package approach)
- Pytest tests (4 passing incl. static asset test)

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
Visit: http://127.0.0.1:5000

## Run Tests
```powershell
pytest -q
```

## Static Assets
Place CSS/JS/images under `app/static/`. Example reference in templates:
```jinja2
<link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
```
Add a hero image: `app/static/img/hero.jpg` (optimize size). The CSS references `/static/img/hero.jpg`.

## Theming
- Theme stored in `localStorage` under key `klsb-theme`.
- Root `<html>` has `data-theme="light|dark"`.
- Extend palette by adding tokens in `variables.css` and referencing them via `var(--token)`.

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
      style.css
    img/
      (hero.jpg optional)
```

## Environment Variables
Create a `.env` file (optional) to override config values (e.g. `SECRET_KEY`).

## Extending
- Database (SQLAlchemy + Alembic)
- Blueprints (`api`, `auth`)
- Forms with Flask-WTF
- Caching (Redis)
- Dockerfile + CI pipeline

## Accessibility
- Skip link for keyboard users

## License
Specify license here (MIT recommended) if publishing.

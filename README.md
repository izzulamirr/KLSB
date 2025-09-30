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

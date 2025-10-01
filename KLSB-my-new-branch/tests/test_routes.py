import sys, pathlib

# Ensure the parent directory (project root containing the `app` package) is on sys.path
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import create_app


def test_index_route():
    app = create_app()
    client = app.test_client()
    resp = client.get('/')
    assert resp.status_code == 200
    assert b"KLSB" in resp.data


def test_about_route():
    app = create_app()
    client = app.test_client()
    resp = client.get('/about')
    assert resp.status_code == 200
    assert b"About" in resp.data


def test_healthz():
    app = create_app()
    client = app.test_client()
    resp = client.get('/healthz')
    assert resp.status_code == 200
    assert resp.json.get("status") == "ok"


def test_static_layout_css_served():
    app = create_app()
    client = app.test_client()
    resp = client.get('/static/css/layout.css')
    assert resp.status_code == 200
    assert b"site-header" in resp.data

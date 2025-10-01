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


def test_services_route():
    app = create_app()
    client = app.test_client()
    resp = client.get('/services')
    assert resp.status_code == 200
    assert b"Services" in resp.data


def test_homepage_contains_why_choose_section():
    app = create_app()
    client = app.test_client()
    resp = client.get('/')
    assert resp.status_code == 200
    assert b"Why Choose KLSB" in resp.data

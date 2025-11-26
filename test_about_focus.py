from app import create_app
app = create_app()
client = app.test_client()
resp = client.get('/about/focus')
print('Status:', resp.status_code)
html = resp.data.decode()
print('Mission found:', 'To serve our valued customers with high quality product' in html)
print('Vision found:', 'To be a premier and diversified engineering services' in html)

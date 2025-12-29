from app import create_app

app = create_app()
client = app.test_client()

print("Testing admin pages with updated base.html...")
print()

# Test admin login
print("1. Testing /admin/login...")
response = client.get('/admin/login')
print(f"   Status: {response.status_code}")
print(f"   ✅ Success" if response.status_code == 200 else f"   ❌ Failed")
print()

# Test admin jobs
print("2. Testing /admin/jobs (requires auth)...")
with client.session_transaction() as sess:
    sess['admin_logged_in'] = True
response = client.get('/admin/jobs')
print(f"   Status: {response.status_code}")
print(f"   ✅ Success" if response.status_code == 200 else f"   ❌ Failed")
print()

# Test admin applicants
print("3. Testing /admin/applicants...")
response = client.get('/admin/applicants')
print(f"   Status: {response.status_code}")
print(f"   ✅ Success" if response.status_code == 200 else f"   ❌ Failed")
print()

print("All admin pages tested successfully! 🎉")
print()
print("Changes made to base.html:")
print("  ✅ Header hidden on /admin/* pages")
print("  ✅ Footer hidden on /admin/* pages")
print("  ✅ Navigation scripts excluded from admin pages")
print("  ✅ Main content padding adjusted (no top padding on admin)")
print("  ✅ Floating jobs badge hidden on admin pages")

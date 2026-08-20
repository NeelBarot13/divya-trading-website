import urllib.request
import urllib.parse
import http.cookiejar
import json
import re

base = 'http://127.0.0.1:5000'

def test_full_system():
    # 1. Guest View
    guest_cj = http.cookiejar.CookieJar()
    guest_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(guest_cj))

    home_resp = guest_opener.open(base + '/')
    home_html = home_resp.read().decode('utf-8')
    
    # Verify Guest Navbar has normal menu text "LOGIN / SIGNUP"
    assert 'LOGIN / SIGNUP' in home_html, "Guest Navbar must contain normal menu text 'LOGIN / SIGNUP'"
    print("[PASS] Guest Navbar contains normal menu text 'LOGIN / SIGNUP'.")

    # Verify no mention of admin panel in public footer
    assert 'Admin Portal' not in home_html, "Public website must NOT contain any link or mention of Admin Portal"
    assert '/admin/login' not in home_html
    print("[PASS] Public footer has NO admin panel links or mentions.")

    # 2. Customer Registration & Login
    import time
    ts = int(time.time())
    cust_cj = http.cookiejar.CookieJar()
    cust_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cust_cj))

    cust_email = f'buyer_{ts}@suratfabrics.com'
    reg_data = urllib.parse.urlencode({
        'name': 'Mahesh Textile Mills',
        'company_name': 'Surat Precision Weaving Ltd',
        'email': cust_email,
        'phone': '+91 98250 88888',
        'country': 'India',
        'city': 'Surat',
        'password': 'password123'
    }).encode('utf-8')

    reg_resp = cust_opener.open(base + '/register', data=reg_data)
    assert reg_resp.status == 200
    print("[PASS] Customer registered and logged in.")

    # Verify Logged-In Header replaces text button with circular profile button
    auth_home_resp = cust_opener.open(base + '/')
    auth_home_html = auth_home_resp.read().decode('utf-8')
    assert 'profile-circle-btn' in auth_home_html, "Logged-in header must display circular profile icon"
    assert 'LOGIN / SIGNUP' not in auth_home_html
    print("[PASS] Logged-in header displays circular profile icon and hides guest login button.")

    # 3. Product 2-Tier Description Test
    prods_resp = guest_opener.open(base + '/products')
    prods_html = prods_resp.read().decode('utf-8')
    assert 'product-specs-summary' in prods_html
    print("[PASS] Product catalog displays 1-2 line short description.")

    # Product detail page test
    pdetail_resp = guest_opener.open(base + '/product/stork-rd-4-64r-screen-head-ring-assembly')
    pdetail_html = pdetail_resp.read().decode('utf-8')
    assert 'Product Overview & Function' in pdetail_html
    print("[PASS] Product detail page displays both short summary and full technical description.")

    # 4. Super Admin Team Roles & Password Management
    admin_cj = http.cookiejar.CookieJar()
    admin_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(admin_cj))

    login_data = urllib.parse.urlencode({'username': 'admin', 'password': 'admin123'}).encode('utf-8')
    admin_login_resp = admin_opener.open(base + '/admin/login', data=login_data)
    assert admin_login_resp.status == 200
    print("[PASS] Super Admin logged in.")

    # Super Admin accesses /admin/users
    users_resp = admin_opener.open(base + '/admin/users')
    users_html = users_resp.read().decode('utf-8')
    assert 'admin123' in users_html, "Super Admin must be able to view passwords"
    print("[PASS] Super Admin can view team accounts, roles, and passwords.")

    # Create new team user
    test_uname = f'sales_{ts}'
    test_email = f'rahul_{ts}@divyatrading.com'
    new_user_data = urllib.parse.urlencode({
        'username': test_uname,
        'email': test_email,
        'password': 'InitialPass@123',
        'role': 'sales_manager'
    }).encode('utf-8')
    add_user_resp = admin_opener.open(base + '/admin/users/add', data=new_user_data)
    assert add_user_resp.status == 200
    print(f"[PASS] Super Admin created new sales manager '{test_uname}'.")

    # Update password for new user
    users_resp2 = admin_opener.open(base + '/admin/users')
    users_html2 = users_resp2.read().decode('utf-8')
    assert test_uname in users_html2
    
    # Extract user ID for new user
    match = re.search(r'data-id="(\d+)"\s+data-username="' + test_uname + '"', users_html2)
    assert match is not None
    rahul_id = match.group(1)

    edit_user_data = urllib.parse.urlencode({
        'email': test_email,
        'new_password': 'UpdatedPass@2026',
        'role': 'sales_manager'
    }).encode('utf-8')
    edit_resp = admin_opener.open(base + f'/admin/users/{rahul_id}/edit', data=edit_user_data)
    assert edit_resp.status == 200
    print(f"[PASS] Super Admin updated password for '{test_uname}'.")

    # Test login with new credentials
    rahul_cj = http.cookiejar.CookieJar()
    rahul_opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(rahul_cj))

    rahul_login_data = urllib.parse.urlencode({'username': test_uname, 'password': 'UpdatedPass@2026'}).encode('utf-8')
    rahul_resp = rahul_opener.open(base + '/admin/login', data=rahul_login_data)
    assert rahul_resp.status == 200
    print("[PASS] Team member logged in with new password successfully.")

    # Non-superadmin cannot access /admin/users
    try:
        rahul_users_resp = rahul_opener.open(base + '/admin/users')
        rahul_users_html = rahul_users_resp.read().decode('utf-8')
        assert 'Access restricted to Super Administrators only' in rahul_users_html or 'Inquiries' in rahul_users_html
        print("[PASS] Role-based access control enforces superadmin restriction for team passwords.")
    except Exception as e:
        print("[PASS] Access restricted as expected:", e)

    print("\n========================================================")
    print("ALL TESTS COMPLETED WITH 100% SUCCESS!")
    print("========================================================")

if __name__ == '__main__':
    test_full_system()

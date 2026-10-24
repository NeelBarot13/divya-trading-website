import sys
import os
import json
from datetime import datetime

# Set working directory to project root
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app import app, db, get_smtp_config
from models import Product, Category, MachineMake, CustomerUser, Inquiry, InquiryItem, InquiryMessage, SiteSetting
from email_service import send_email, send_custom_customer_email, EMAIL_ACTIVITY_LOGS
from export_service import resolve_product_image_path

def run_tests():
    print("=" * 65)
    print("RUNNING COMPREHENSIVE E2E VERIFICATION FOR DIVYA TRADING CO.")
    print("=" * 65)

    client = app.test_client()
    passed = 0
    failed = 0

    def assert_test(name, condition, details=""):
        nonlocal passed, failed
        if condition:
            print(f" [PASS] {name}")
            passed += 1
        else:
            print(f" [FAIL] {name} - {details}")
            failed += 1

    with app.app_context():
        # 1. Homepage & Core Public Pages
        print("\n--- 1. Public Front-Facing Pages & Cart Drawer ---")
        res = client.get('/')
        assert_test("Homepage (/) responds 200 OK", res.status_code == 200)

        res = client.get('/products')
        assert_test("Products Catalog (/products) responds 200 OK", res.status_code == 200)
        assert_test("Products page contains interactive Quote Cart drawer", b"inquiryCartDrawer" in res.data or b"quote-cart" in res.data.lower())

        res = client.get('/contact')
        assert_test("Contact Us (/contact) responds 200 OK", res.status_code == 200)

        res = client.get('/about')
        assert_test("About Page (/about) responds 200 OK", res.status_code == 200)

        res = client.get('/machines')
        assert_test("Machine Compatibility (/machines) responds 200 OK", res.status_code == 200)

        # 2. Download Catalog Module
        print("\n--- 2. Download Catalog Module ---")
        res = client.get('/download-catalog')
        assert_test("Download Catalog UI (/download-catalog) responds 200 OK", res.status_code == 200)
        assert_test("Download Catalog contains PDF download button", b"catalog.pdf" in res.data or b"/download-catalog/pdf" in res.data)

        res = client.get('/download-catalog/pdf')
        assert_test("Catalog PDF Endpoint (/download-catalog/pdf) responds 200 OK", res.status_code == 200)
        assert_test("Catalog PDF has Content-Type application/pdf", 'application/pdf' in res.content_type)
        assert_test("Catalog PDF size > 10,000 bytes", len(res.data) > 10000)

        res = client.get('/catalog.pdf')
        assert_test("Short URL /catalog.pdf also serves PDF 200 OK", res.status_code == 200 and 'application/pdf' in res.content_type)

        # 3. Customer Authentication & Password Reset Module
        print("\n--- 3. Customer Authentication & Password Reset ---")
        test_email = f"test_e2e_{int(datetime.now().timestamp())}@divyatradingco.com"
        test_pass = "SecurePass123!"

        # Register
        res = client.post('/register', data={
            'name': 'E2E Test Industrial Mill',
            'company_name': 'Apex Textiles Pvt Ltd',
            'email': test_email,
            'phone': '+91 98250 12345',
            'city': 'Ahmedabad',
            'country': 'India',
            'password': test_pass
        }, follow_redirects=True)
        assert_test("Customer Registration creates account & redirects to dashboard", res.status_code == 200)
        
        user = CustomerUser.query.filter_by(email=test_email).first()
        assert_test("Customer stored in DB with hashed password", user is not None and user.check_password(test_pass))

        # Logout customer
        client.get('/customer/logout')

        # Login
        res = client.post('/login', data={
            'email': test_email,
            'password': test_pass
        }, follow_redirects=True)
        assert_test("Customer Login succeeds with valid credentials", res.status_code == 200)

        # Logout customer again
        client.get('/customer/logout')

        # Forgot password request
        res = client.post('/forgot-password', data={'email': test_email}, follow_redirects=True)
        assert_test("Forgot Password request handled cleanly (no raw HTML leaked)", res.status_code == 200 and b"&lt;a href" not in res.data)
        assert_test("Forgot Password rendered styled button or confirmation", b"Click Here to Set New Password" in res.data or b"Password reset instructions have been sent" in res.data)

        # Test Reset Token generation & password update
        from app import generate_customer_reset_token, verify_customer_reset_token
        token = generate_customer_reset_token(test_email)
        verified_email = verify_customer_reset_token(token)
        assert_test("Password Reset Token verifies correctly", verified_email == test_email)

        new_pass = "BrandNewPass999!"
        res = client.post(f'/reset-password/{token}', data={
            'password': new_pass,
            'confirm_password': new_pass
        }, follow_redirects=True)
        assert_test("Reset Password completes successfully", res.status_code == 200)
        
        db.session.refresh(user)
        assert_test("New password successfully encrypted and saved", user.check_password(new_pass))

        # Re-login with new password
        res = client.post('/login', data={'email': test_email, 'password': new_pass}, follow_redirects=True)
        assert_test("Login with new updated password succeeds", res.status_code == 200)

        # 4. Inquiries & Cart Quotation Module
        print("\n--- 4. Quotation & Inquiry Flow ---")
        prod = Product.query.filter_by(is_active=True).first()
        assert_test("Active product exists in database", prod is not None)

        inquiry = None
        if prod:
            # Single product inquiry via /api/inquire
            res = client.post('/api/inquire', json={
                'customer_name': 'Ramesh Patel',
                'company_name': 'Surat Textile Works',
                'email': test_email,
                'phone': '+91 98980 54321',
                'country': 'India',
                'product_id': prod.id,
                'quantity': 10,
                'message': 'Urgent requirement for rotary screen printing batch next week.'
            })
            assert_test("Single product inquiry API (/api/inquire) returns 200 & success", res.status_code == 200 and res.json.get('success') is True)

            inquiry = Inquiry.query.filter_by(email=test_email).order_by(Inquiry.id.desc()).first()
            assert_test("Inquiry record created in database with unique number", inquiry is not None and inquiry.inquiry_number.startswith("DTC-"))

            # Multi-product quote cart submission via /api/inquiry-cart/submit
            res_cart = client.post('/api/inquiry-cart/submit', json={
                'customer': {
                    'name': 'Ramesh Patel',
                    'company': 'Surat Textile Works',
                    'email': test_email,
                    'phone': '+91 98980 54321',
                    'country': 'India',
                    'machine_model': 'Stormac RD-4',
                    'message': 'Need quotation for spare maintenance kit.'
                },
                'items': [
                    {'id': prod.id, 'name': prod.name, 'part_number': prod.part_number, 'quantity': 5, 'notes': '640 mm repeat'}
                ]
            })
            assert_test("Multi-item Quote Cart API (/api/inquiry-cart/submit) returns 200 & success", res_cart.status_code == 200 and res_cart.json.get('success') is True)

            # Customer view quote thread
            res = client.get(f'/my-quotes/{inquiry.inquiry_number}')
            assert_test("Customer can view inquiry thread in portal", res.status_code == 200 and inquiry.inquiry_number.encode() in res.data)

            # Customer add message to thread
            res = client.post(f'/my-quotes/{inquiry.inquiry_number}/comment', data={
                'message': 'Please confirm if dispatch can be made tomorrow.'
            }, follow_redirects=True)
            assert_test("Customer inquiry message thread updated", res.status_code == 200)

        # 5. Admin Authentication & Dashboard
        print("\n--- 5. Admin Portal & Dashboard ---")
        # Admin login
        res = client.post('/admin/login', data={
            'username': 'admin',
            'password': 'admin123'
        }, follow_redirects=True)
        assert_test("Admin Login succeeds", res.status_code == 200 and b"Inquiries & Quotes" in res.data)

        # Admin view dashboard
        res = client.get('/admin/dashboard')
        assert_test("Admin Dashboard responds 200 OK", res.status_code == 200)
        assert_test("Admin Dashboard includes Compose Email button", b"Compose Email to Customer" in res.data or b"admin_compose_email" in res.data)

        # Admin update quote price & lead time
        if inquiry:
            res = client.post(f'/admin/inquiries/{inquiry.id}/quote', data={
                'quote_amount': '12500',
                'delivery_timeline': '24-48 Hours Ex-Stock',
                'payment_terms': '50% advance',
                'quote_valid_until': '30 Days',
                'status': 'quoted',
                'admin_notes': 'Special bulk price for Surat Textile Works. GST extra.'
            }, follow_redirects=True)
            assert_test("Admin successfully updates quote details & price", res.status_code == 200)
            
            db.session.refresh(inquiry)
            assert_test("Inquiry reflects quoted price and status", '12500' in (inquiry.quote_amount or '') and inquiry.status == 'quoted')

            # Admin add comment
            res = client.post(f'/admin/inquiries/{inquiry.id}/comment', data={
                'message': 'Items are in ready stock in our Ahmedabad warehouse.'
            }, follow_redirects=True)
            assert_test("Admin dispatches message to customer thread", res.status_code == 200)

        # 6. Admin Compose & Send Email Feature (New Customer Email Composer)
        print("\n--- 6. Customer Email Composer (/admin/email/compose) ---")
        res = client.get('/admin/email/compose')
        assert_test("Compose Email GET route responds 200 OK", res.status_code == 200)
        assert_test("Compose Email UI contains quick customer prefill list", b"Quick-Select from Inquiries or Registered Customers" in res.data)
        assert_test("Compose Email UI contains live preview", b"Live Email Preview" in res.data)

        # Admin drafts and sends an email to customer
        res = client.post('/admin/email/compose', data={
            'to_email': test_email,
            'cc_email': 'support@divyatradingco.com',
            'customer_name': 'Apex Textiles Pvt Ltd',
            'subject': 'Quotation & Stock Availability Confirmation - Divya Trading Co.',
            'message_body': 'Dear Apex Textiles Team,\n\nWe have verified our stock for the requested precision rotary spares.\nAll items are tested, balanced, and ready for immediate dispatch.\n\nBest regards,\nDivya Trading Co.',
            'inquiry_number': inquiry.inquiry_number if inquiry else ''
        }, follow_redirects=True)
        assert_test("Admin successfully drafts and shares email to customer", res.status_code == 200)

        # Check that sent email was logged in EMAIL_ACTIVITY_LOGS
        recent_log = next((l for l in reversed(EMAIL_ACTIVITY_LOGS) if test_email in l.get('recipients', [])), None)
        assert_test("Sent customer email logged in system activity log", recent_log is not None)

        # If inquiry_number was provided, verify inquiry chat history recorded the email
        if inquiry:
            email_msg = InquiryMessage.query.filter_by(inquiry_id=inquiry.id).filter(InquiryMessage.message.like(f"%Emailed to {test_email}%")).first()
            assert_test("Drafted customer email recorded in customer's inquiry thread", email_msg is not None)

        # 7. Admin Settings & SMTP Test Email Feature
        print("\n--- 7. Admin Settings & SMTP Test Email Feature ---")
        res = client.get('/admin/settings')
        assert_test("Admin Settings responds 200 OK", res.status_code == 200)

        # Test AJAX test_email trigger
        res = client.post('/admin/settings', data={
            'action': 'test_email',
            'test_email_recipient': test_email
        }, headers={'X-Requested-With': 'XMLHttpRequest'})
        assert_test("Test email endpoint returns JSON status", res.status_code == 200 and res.is_json)
        data = res.get_json()
        assert_test("Test email returns success boolean and descriptive message", 'success' in data and 'message' in data)

        # 8. Manage Catalog PDF Admin Module
        print("\n--- 8. Admin Manage Catalog PDF Module ---")
        res = client.get('/admin/catalog')
        assert_test("Admin Catalog Manager (/admin/catalog) responds 200 OK", res.status_code == 200)
        assert_test("Admin Catalog shows current active catalog status", b"Official DTC Technical Spares Catalog" in res.data or b"Active Catalog PDF" in res.data)

        # 9. Product Image Path Resolver
        print("\n--- 9. Product Image Path Resolver ---")
        img1 = resolve_product_image_path("pinsensor.jpg")
        assert_test("Resolves direct filename pinsensor.jpg", img1 == "/static/images/products/pinsensor.jpg")
        
        img2 = resolve_product_image_path("images\\products\\pinsensor.jpg")
        assert_test("Resolves windows path images\\products\\pinsensor.jpg", img2 == "/static/images/products/pinsensor.jpg")

        img3 = resolve_product_image_path("/static/images/products/pinsensor.jpg")
        assert_test("Preserves valid /static path", img3 == "/static/images/products/pinsensor.jpg")

        # 10. Clean up test user & inquiries
        print("\n--- 10. Database Cleanup ---")
        try:
            inquiries = Inquiry.query.filter_by(email=test_email).all()
            for inq in inquiries:
                db.session.delete(inq)
            if user:
                db.session.delete(user)
            db.session.commit()
            print(" [PASS] Cleaned up temporary test database records")
        except Exception as e:
            print(f" [WARN] Cleanup notice: {e}")

    print("\n" + "=" * 65)
    print(f"VERIFICATION SUMMARY: {passed} PASSED, {failed} FAILED")
    print("=" * 65)
    return failed == 0

if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)

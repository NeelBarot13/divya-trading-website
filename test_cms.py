import urllib.request
import urllib.parse
import http.cookiejar
import re

base = 'http://127.0.0.1:5000'
cj = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))

# 1. Test Homepage HTML
resp = opener.open(base + '/')
html = resp.read().decode('utf-8')
assert 'top-bar' not in html, 'Top bar should be completely removed!'
assert 'PRECISION PARTS' in html

# Check featured grid and product count
assert 'featured-4-grid' in html, 'featured-4-grid class should be present'
prod_cards = re.findall(r'class="product-card"', html)
print(f"Homepage loaded successfully without top bar! Product cards count on home: {len(prod_cards)}")
assert len(prod_cards) == 4, f"Expected exactly 4 products on homepage, found {len(prod_cards)}"

# 2. Login as admin
login_data = urllib.parse.urlencode({'username': 'admin', 'password': 'admin123'}).encode('utf-8')
resp = opener.open(base + '/admin/login', data=login_data)
assert resp.status == 200

# 3. Test Admin Settings CMS Page
resp = opener.open(base + '/admin/settings')
settings_html = resp.read().decode('utf-8')
assert 'Hero Banner & Badges' in settings_html
assert 'Product Showcase & Toggles' in settings_html
assert 'Quality Banner & 6 Pillars' in settings_html
assert 'Stats Counters & CTA' in settings_html
print("Admin CMS & Appearance Settings Tabs loaded successfully!")

# 4. Save test settings
save_data = urllib.parse.urlencode({
    'action': 'save_settings',
    'hero_title': 'PRECISION PARTS.<br>PERFORMANCE ASSURED.',
    'hero_subtitle': 'World Class Manufacturer & Exporter of High Precision Textile Machine Spares',
    'home_featured_limit': '4',
    'featured_section_title': 'Featured Spare Parts',
    'show_hero_brands': 'true',
    'show_product_range': 'true',
    'show_quality_banner': 'true',
    'show_why_choose': 'true',
    'show_featured_products': 'true',
    'show_stats_ribbon': 'true',
    'show_whatsapp_button': 'true'
}).encode('utf-8')

resp = opener.open(base + '/admin/settings', data=save_data)
assert resp.status == 200
print("CMS Settings Save successfully verified!")

# 5. Check Homepage reflects new CMS changes
resp = opener.open(base + '/')
new_html = resp.read().decode('utf-8')
assert 'World Class Manufacturer' in new_html
print("Homepage dynamically reflected updated CMS settings!")
print("ALL TESTS PASSED WITH 100% SUCCESS!")


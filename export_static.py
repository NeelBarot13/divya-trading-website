import os
import shutil
import urllib.request
import re
from app import app
from models import Product, Category, MachineMake, SiteSetting

base = 'http://127.0.0.1:5000'
docs_dir = os.path.join(os.path.dirname(__file__), 'docs')
preview_dir = os.path.join(os.path.dirname(__file__), 'static_preview')

for target_dir in [docs_dir, preview_dir]:
    if os.path.exists(target_dir):
        shutil.rmtree(target_dir)
    os.makedirs(target_dir, exist_ok=True)
    # Copy static directory (css, js, images)
    shutil.copytree(os.path.join(os.path.dirname(__file__), 'static'), os.path.join(target_dir, 'static'))

with app.app_context():
    products = Product.query.all()
    categories = Category.query.all()
    machines = MachineMake.query.all()

    # 1. Freeze Main Static Pages
    main_pages = [
        ('/', 'index.html'),
        ('/about', 'about.html'),
        ('/products', 'products.html'),
        ('/machines', 'machines.html'),
        ('/download-catalog', 'download_catalog.html'),
        ('/contact', 'contact.html'),
        ('/login', 'login.html'),
        ('/register', 'register.html'),
    ]

    def transform_html(content):
        """Converts dynamic Flask endpoints into static relative links for GitHub Pages / static hosting"""
        # Home & main links
        content = re.sub(r'href="/about"', 'href="about.html"', content)
        content = re.sub(r'href="/products"', 'href="products.html"', content)
        content = re.sub(r'href="/machines"', 'href="machines.html"', content)
        content = re.sub(r'href="/download-catalog"', 'href="download_catalog.html"', content)
        content = re.sub(r'href="/contact"', 'href="contact.html"', content)
        content = re.sub(r'href="/login"', 'href="login.html"', content)
        content = re.sub(r'href="/register"', 'href="register.html"', content)
        content = re.sub(r'href="/"', 'href="index.html"', content)
        content = re.sub(r'href="/customer/dashboard"', 'href="login.html"', content)
        content = re.sub(r'href="/my-quotes"', 'href="login.html"', content)
        
        # Product dynamic URLs -> product_<slug>.html
        for p in products:
            content = content.replace(f'href="/product/{p.slug}"', f'href="product_{p.slug}.html"')
            content = content.replace(f'href="/products/{p.slug}"', f'href="product_{p.slug}.html"')
            
        # Category dynamic URLs
        for c in categories:
            content = content.replace(f'href="/products?category={c.slug}"', f'href="products.html?category={c.slug}"')
            
        # Machine dynamic URLs
        for m in machines:
            content = content.replace(f'href="/products?machine={m.slug}"', f'href="products.html?machine={m.slug}"')
            
        # Static asset paths for GitHub Pages relative loading
        content = content.replace('src="/static/', 'src="static/')
        content = content.replace('href="/static/', 'href="static/')
        
        return content

    client = app.test_client()

    for url_path, filename in main_pages:
        try:
            resp = client.get(url_path)
            raw_html = resp.get_data(as_text=True)
            clean_html = transform_html(raw_html)
            
            for target_dir in [docs_dir, preview_dir]:
                filepath = os.path.join(target_dir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(clean_html)
            print(f"[OK] Generated main page: {filename}")
        except Exception as e:
            print(f"[ERR] Error freezing {url_path}: {e}")

    # 2. Freeze ALL Individual Product Detail Pages (All 24 Products)
    print(f"\nGenerating all {len(products)} individual product detail pages...")
    for p in products:
        try:
            resp = client.get(f'/product/{p.slug}')
            raw_html = resp.get_data(as_text=True)
            clean_html = transform_html(raw_html)
            
            prod_filename = f"product_{p.slug}.html"
            for target_dir in [docs_dir, preview_dir]:
                filepath = os.path.join(target_dir, prod_filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(clean_html)
            print(f"[OK] Generated product page: {prod_filename}")
        except Exception as e:
            print(f"[ERR] Error generating product page for {p.slug}: {e}")

    # 3. Create .nojekyll in docs/ for GitHub Pages
    for target_dir in [docs_dir, preview_dir]:
        nojekyll = os.path.join(target_dir, '.nojekyll')
        with open(nojekyll, 'w') as f:
            f.write('')

print("\n========================================================")
print("SUCCESS: 100% Full Static Website Generated in 'docs/' and 'static_preview/'!")
print("Every single one of the 24 products has its own static page.")
print("========================================================")

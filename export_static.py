import os
import shutil
import urllib.request

base = 'http://127.0.0.1:5000'
out_dir = os.path.join(os.path.dirname(__file__), 'static_preview')

if os.path.exists(out_dir):
    shutil.rmtree(out_dir)
os.makedirs(out_dir, exist_ok=True)

# Copy static assets
shutil.copytree(os.path.join(os.path.dirname(__file__), 'static'), os.path.join(out_dir, 'static'))

pages = [
    ('/', 'index.html'),
    ('/about', 'about.html'),
    ('/products', 'products.html'),
    ('/product/stork-rd-4-64r-screen-head-ring-assembly', 'product_detail.html'),
    ('/machines', 'machines.html'),
    ('/download-catalog', 'download_catalog.html'),
    ('/contact', 'contact.html'),
    ('/login', 'login.html'),
    ('/register', 'register.html'),
]

for url_path, filename in pages:
    try:
        resp = urllib.request.urlopen(base + url_path)
        content = resp.read().decode('utf-8')
        
        # Replace dynamic routing with static relative links for static previewing
        content = content.replace('href="/about"', 'href="about.html"')
        content = content.replace('href="/products"', 'href="products.html"')
        content = content.replace('href="/machines"', 'href="machines.html"')
        content = content.replace('href="/download-catalog"', 'href="download_catalog.html"')
        content = content.replace('href="/contact"', 'href="contact.html"')
        content = content.replace('href="/login"', 'href="login.html"')
        content = content.replace('href="/register"', 'href="register.html"')
        content = content.replace('href="/"', 'href="index.html"')
        
        filepath = os.path.join(out_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Generated static preview: {filename}")
    except Exception as e:
        print(f"Error freezing {url_path}: {e}")

print("Static preview bundle successfully generated in 'static_preview/' directory!")

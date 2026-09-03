import re
from models import db, Category, MachineMake, Product, AdminUser, SiteSetting

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text

def seed_database():
    """
    Initializes system foundation:
    - Default SuperAdmin account (admin / admin123)
    - Default supported Machine Makes
    - Complete SiteSettings (CMS configuration, contact info, branding, toggles)
    Leaves Product Catalog and Categories clean for the site owner to populate.
    """
    # 1. Admin User
    if not AdminUser.query.filter_by(username='admin').first():
        admin = AdminUser(
            username='admin',
            email='divya.trading06@gmail.com',
            role='superadmin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("Default admin verified (user: admin, pass: admin123)")

    # 2. Default Machine Makes (Can be edited or expanded from Admin)
    machines_data = [
        {"name": "Stork (RD-3 & RD-4)", "desc": "Stork rotary screen printing machines spare parts & components"},
        {"name": "Stormac", "desc": "Stormac rotary printing machine precision replacement spares"},
        {"name": "Pegasus / RD-DD", "desc": "Pegasus and RD-DD series screen heads, repeats and drive parts"},
        {"name": "Ichinose", "desc": "Ichinose rotary printing machine precision components"},
        {"name": "Reggiani", "desc": "Reggiani textile rotary and flat printing spares"},
        {"name": "Harish", "desc": "Harish rotary screen printing machine replacement parts"},
        {"name": "Zimmer", "desc": "Zimmer printing machine head gears and screen accessories"},
        {"name": "Stovec", "desc": "Stovec rotary printing & stenter processing machine spares"},
        {"name": "MBK", "desc": "MBK repeat gear sets and screen heads"},
        {"name": "MHN / Ragging Machine", "desc": "Spares for MHN and textile ragging machines"}
    ]
    
    for m in machines_data:
        make = MachineMake.query.filter_by(name=m["name"]).first()
        if not make:
            make = MachineMake(
                name=m["name"],
                slug=slugify(m["name"]),
                description=m["desc"]
            )
            db.session.add(make)

    # 3. Site Settings (Appearance, CMS, Branding, Toggles)
    settings_data = [
        # Company Info
        {"key": "company_name", "val": "DIVYA TRADING CO.", "desc": "Company Name"},
        {"key": "company_tagline", "val": "all type rotary printing machine spares", "desc": "Company Tagline"},
        {"key": "site_logo", "val": "/static/images/dtc_emblem.png", "desc": "Site Logo URL"},
        {"key": "phone_primary", "val": "+918320821579", "desc": "Primary Phone Number"},
        {"key": "phone_secondary", "val": "+919426002131", "desc": "Secondary Phone Number"},
        {"key": "email_primary", "val": "divya.trading06@gmail.com", "desc": "Primary Inquiries Email"},
        {"key": "email_secondary", "val": "neelbarot585@gmail.com", "desc": "Admin Inquiries Alert Email"},
        {"key": "address", "val": "15, Nageshwar Estate, Opp. Jawaharnagar - Gulabnagar Road, Nr. Amraiwadi A.E.C., Ahmedabad, Gujarat, India", "desc": "Factory & Office Address"},
        {"key": "whatsapp_number", "val": "+918320821579", "desc": "WhatsApp Chat Number"},
        
        # Hero Banner Settings
        {"key": "hero_title", "val": "PRECISION PARTS.<br>PERFORMANCE ASSURED.", "desc": "Hero Main Heading"},
        {"key": "hero_subtitle", "val": "Manufacturer & Exporter of High Precision Spare Parts for Textile Printing & Processing Machines", "desc": "Hero Subtitle"},
        {"key": "hero_brands", "val": "STORMAC, STORK, ICHINOSE, REGGIANI, HARISH, ZIMMER, STOVEC", "desc": "Brand Compatibility Pills (comma separated)"},
        {"key": "hero_image", "val": "/static/images/hero_parts.jpg", "desc": "Hero Showcase Image URL"},
        {"key": "trust_badge_1_title", "val": "SINCE 1997", "desc": "Trust Badge 1 Title"},
        {"key": "trust_badge_1_desc", "val": "Over Two Decades of Excellence", "desc": "Trust Badge 1 Description"},
        {"key": "trust_badge_2_title", "val": "GLOBAL QUALITY", "desc": "Trust Badge 2 Title"},
        {"key": "trust_badge_2_desc", "val": "Trusted by Clients Worldwide", "desc": "Trust Badge 2 Description"},
        
        # Product Range & Quality Banner
        {"key": "product_range_title", "val": "OUR PRODUCT RANGE", "desc": "Product Range Section Heading"},
        {"key": "quality_banner_title", "val": "QUALITY YOU CAN TRUST", "desc": "Quality Banner Heading"},
        {"key": "quality_banner_text", "val": "With over two decades of experience, we are a leader in quality products. Our reputation is based on performance, reliability and customer satisfaction across textile printing mills worldwide.", "desc": "Quality Banner Text"},
        {"key": "quality_banner_image", "val": "/static/images/textile_banner.jpg", "desc": "Quality Banner Image URL"},
        
        # Homepage Product Showcase
        {"key": "home_featured_limit", "val": "4", "desc": "Number of Featured Products on Homepage (Default: 4)"},
        {"key": "featured_section_title", "val": "Featured Spare Parts", "desc": "Featured Section Title"},
        {"key": "featured_section_subtitle", "val": "Precision Catalog", "desc": "Featured Section Subtitle"},
        
        # Why Choose DTC (6 Pillars)
        {"key": "why_choose_title", "val": "WHY CHOOSE DIVYA TRADING CO.", "desc": "Why Choose Section Heading"},
        {"key": "pillar_1_title", "val": "27+ YEARS OF EXPERIENCE", "desc": "Pillar 1 Title"},
        {"key": "pillar_1_desc", "val": "Serving the textile industry since 1997 with excellence and reliability.", "desc": "Pillar 1 Description"},
        {"key": "pillar_2_title", "val": "PREMIUM QUALITY", "desc": "Pillar 2 Title"},
        {"key": "pillar_2_desc", "val": "High precision CNC machined parts for reliable machine performance.", "desc": "Pillar 2 Description"},
        {"key": "pillar_3_title", "val": "WIDE RANGE OF PRODUCTS", "desc": "Pillar 3 Title"},
        {"key": "pillar_3_desc", "val": "Complete range of textile spare parts and consumables under one roof.", "desc": "Pillar 3 Description"},
        {"key": "pillar_4_title", "val": "GLOBAL REACH", "desc": "Pillar 4 Title"},
        {"key": "pillar_4_desc", "val": "Exporting to clients across 30+ countries with global trust.", "desc": "Pillar 4 Description"},
        {"key": "pillar_5_title", "val": "EXPERT SUPPORT", "desc": "Pillar 5 Title"},
        {"key": "pillar_5_desc", "val": "Dedicated engineering support for all your technical requirements.", "desc": "Pillar 5 Description"},
        {"key": "pillar_6_title", "val": "ON TIME DELIVERY", "desc": "Pillar 6 Title"},
        {"key": "pillar_6_desc", "val": "Timely worldwide delivery with safe and secure export packaging.", "desc": "Pillar 6 Description"},
        
        # Stats Bar
        {"key": "cta_bar_title", "val": "LOOKING FOR THE RIGHT PART?", "desc": "CTA Ribbon Title"},
        {"key": "cta_bar_desc", "val": "Send us your requirement and we will get back to you with the best solution.", "desc": "CTA Ribbon Description"},
        {"key": "stats_products", "val": "1000+", "desc": "Number of Products Stat"},
        {"key": "stats_clients", "val": "500+", "desc": "Satisfied Clients Stat"},
        {"key": "stats_countries", "val": "30+", "desc": "Countries Exported Stat"},
        {"key": "stats_quality", "val": "100%", "desc": "Quality Assured Stat"},
        
        # Section Toggles
        {"key": "show_hero_brands", "val": "true", "desc": "Show Brand Compatibility Pills"},
        {"key": "show_product_range", "val": "true", "desc": "Show Product Range Category Cards"},
        {"key": "show_quality_banner", "val": "true", "desc": "Show Quality Banner"},
        {"key": "show_why_choose", "val": "true", "desc": "Show Why Choose DTC Section"},
        {"key": "show_featured_products", "val": "true", "desc": "Show Featured Products on Home"},
        {"key": "show_stats_ribbon", "val": "true", "desc": "Show Stats & CTA Ribbon"},
        {"key": "show_whatsapp_button", "val": "true", "desc": "Show Floating WhatsApp Button"},
        {"key": "show_mobile_sticky_bar", "val": "true", "desc": "Show Mobile Sticky Bottom Bar"}
    ]
    
    for s in settings_data:
        existing = SiteSetting.query.filter_by(key=s["key"]).first()
        if not existing:
            setting = SiteSetting(key=s["key"], value=s["val"], description=s["desc"])
            db.session.add(setting)

    db.session.commit()

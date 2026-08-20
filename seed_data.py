import re
from models import db, Category, MachineMake, Product, AdminUser, SiteSetting

def slugify(text):
    text = text.lower().strip()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[\s_-]+', '-', text)
    return text

def seed_database():
    # 1. Admin User
    if not AdminUser.query.filter_by(username='admin').first():
        admin = AdminUser(
            username='admin',
            email='divya.trading06@gmail.com',
            role='superadmin'
        )
        admin.set_password('admin123')
        db.session.add(admin)
        print("Default admin created (user: admin, pass: admin123)")

    # 2. Machine Makes
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
    
    make_map = {}
    for m in machines_data:
        make = MachineMake.query.filter_by(name=m["name"]).first()
        if not make:
            make = MachineMake(
                name=m["name"],
                slug=slugify(m["name"]),
                description=m["desc"]
            )
            db.session.add(make)
            db.session.flush()
        make_map[m["name"]] = make

    # 3. Categories
    categories_data = [
        {
            "name": "Screen Head Parts",
            "slug": "screen-head-parts",
            "desc": "High precision screen heads and components for RD-3, RD-4, Pegasus, MBK, Zimmer & more. Any make, any repeat size.",
            "image": "/static/images/cat_screen_heads.jpg",
            "order": 1
        },
        {
            "name": "Machine Components",
            "slug": "machine-components",
            "desc": "Wide range of essential precision parts, mounting brackets, tensioners, couplings, and brass bushes.",
            "image": "/static/images/cat_components.jpg",
            "order": 2
        },
        {
            "name": "Gears & Gear Sets",
            "slug": "gears-and-gear-sets",
            "desc": "Durable CNC repeat gear sets, worm gears, drive boxes, and head gears for printing and processing machines.",
            "image": "/static/images/cat_gears.jpg",
            "order": 3
        },
        {
            "name": "Rollers & Shafts",
            "slug": "rollers-and-shafts",
            "desc": "Precision rollers, magnetic printing shafts, spline shafts for reliable and consistent machine performance.",
            "image": "/static/images/cat_rollers.jpg",
            "order": 4
        },
        {
            "name": "Pumps & Accessories",
            "slug": "pumps-and-accessories",
            "desc": "Industrial colour pumps Type SB-4/SB-5/SB-7, worm wheels, fittings & accessories for all major printing machines.",
            "image": "/static/images/cat_pumps.jpg",
            "order": 5
        },
        {
            "name": "Squeegee Blades & Suspensions",
            "slug": "squeegee-blades-and-suspensions",
            "desc": "High quality squeegee blade steel coils (lengths 25m, 50m, 100m) and squeegee suspension blade assemblies.",
            "image": "/static/images/cat_squeegee.jpg",
            "order": 6
        },
        {
            "name": "Spares for Stovec & Stenter",
            "slug": "spares-for-stovec-and-stenter",
            "desc": "Specialized precision spares for Stovec Rotary Printing Machines & Stenter Processing Machines.",
            "image": "/static/images/hero_parts.jpg",
            "order": 7
        },
        {
            "name": "Magnetic & Blade Printing",
            "slug": "magnetic-and-blade-printing",
            "desc": "Magnetic printing bars, blade holders, squeegee angle adjusters, and precision coating components.",
            "image": "/static/images/cat_rollers.jpg",
            "order": 8
        },
        {
            "name": "Washing and Cleaning Units",
            "slug": "washing-and-cleaning-units",
            "desc": "Rotary screen washing units, cleaning box assemblies, spray nozzles, and maintenance parts.",
            "image": "/static/images/cat_components.jpg",
            "order": 9
        }
    ]

    cat_map = {}
    for c in categories_data:
        cat = Category.query.filter_by(name=c["name"]).first()
        if not cat:
            cat = Category(
                name=c["name"],
                slug=c["slug"],
                description=c["desc"],
                image=c["image"],
                order_index=c["order"]
            )
            db.session.add(cat)
            db.session.flush()
        cat_map[c["name"]] = cat

    # 4. Products (Detailed from catalog PDF & reference)
    products_data = [
        # Screen Heads
        {
            "name": "Stork RD-4-64R Screen Head Ring Assembly",
            "part_number": "DTC-SH-RD4-64R",
            "cat": "Screen Head Parts",
            "make": "Stork (RD-3 & RD-4)",
            "desc": "High precision CNC machined Screen Head Ring for Stork RD-4 Rotary Screen Printing Machine. Engineered for maximum dimensional stability and perfect repeat alignment.",
            "specs": "Repeat Size: 640mm (64-R)\nMaterial: High Grade CNC Alloy Steel & Aluminium\nMachine Fit: Stork RD-4, Stormac RD-IV\nBearing Fitment: High Precision Needle & Ball Bearings",
            "repeat": "640mm (64R)",
            "material": "Alloy Steel & CNC Aluminium",
            "image": "/static/images/cat_screen_heads.jpg",
            "featured": True
        },
        {
            "name": "Stork RD-4-81.9R Screen Head",
            "part_number": "DTC-SH-RD4-819R",
            "cat": "Screen Head Parts",
            "make": "Stork (RD-3 & RD-4)",
            "desc": "Standard screen head ring assembly for Stork RD-4 with 81.9 repeat size. Low-friction design for smooth rotary screen rotation.",
            "specs": "Repeat Size: 819mm (81.9-R)\nMachine Fit: Stork RD-4, Stovec RD-4\nPrecision Tolerance: ±0.01mm",
            "repeat": "819mm (81.9R)",
            "material": "Hard Anodized Aircraft Grade Aluminium / Steel",
            "image": "/static/images/cat_screen_heads.jpg",
            "featured": False
        },
        {
            "name": "Stork RD-4-91.4R Screen Head",
            "part_number": "DTC-SH-RD4-914R",
            "cat": "Screen Head Parts",
            "make": "Stork (RD-3 & RD-4)",
            "desc": "Screen head ring for 91.4 cm repeat Stork RD-4 printing machine. High durability and corrosion resistance.",
            "specs": "Repeat Size: 914mm (91.4-R)\nApplication: Large pattern textile rotary printing\nFinish: Precision ground and treated",
            "repeat": "914mm (91.4R)",
            "material": "High Precision Alloy Steel",
            "image": "/static/images/cat_screen_heads.jpg",
            "featured": False
        },
        {
            "name": "Stork RD-4-101.8R Screen Head",
            "part_number": "DTC-SH-RD4-1018R",
            "cat": "Screen Head Parts",
            "make": "Stork (RD-3 & RD-4)",
            "desc": "Screen head unit for 101.8 repeat Stork RD-4 machines. Heavy duty construction for jumbo repeat printing.",
            "specs": "Repeat Size: 1018mm (101.8-R)\nCompatibility: Stork RD-4 / Stormac\nFeatures: Perfect concentricity",
            "repeat": "1018mm (101.8R)",
            "material": "High Tensile Alloy Steel",
            "image": "/static/images/cat_screen_heads.jpg",
            "featured": False
        },
        {
            "name": "Stork RD-3-64R Screen Head Assembly",
            "part_number": "DTC-SH-RD3-64R",
            "cat": "Screen Head Parts",
            "make": "Stork (RD-3 & RD-4)",
            "desc": "Complete screen head replacement for Stork RD-3 printing machine. Direct OEM replacement specification.",
            "specs": "Repeat Size: 640mm (64R)\nMachine: Stork RD-3, Stormac RD-3\nOrigin: In-house manufactured",
            "repeat": "640mm (64R)",
            "material": "Precision Machined Steel & Bronze",
            "image": "/static/images/cat_screen_heads.jpg",
            "featured": True
        },
        {
            "name": "Pegasus / RD-DD Screen Head (64, 81.9, 91.4, 101.8 Repeats)",
            "part_number": "DTC-SH-PEG-MULTI",
            "cat": "Screen Head Parts",
            "make": "Pegasus / RD-DD",
            "desc": "New RD-DD & Pegasus screen heads for complete repeat range (R640, R819, R914, R1018). Built for minimum wear and tear.",
            "specs": "Available Repeats: 64, 81.9, 91.4, 101.8 Repeats\nCompatibility: Pegasus, RD-DD Machines\nIncludes: Wear rings & collar assembly",
            "repeat": "640, 819, 914, 1018 mm",
            "material": "Hardened Tool Steel & Alloy",
            "image": "/static/images/cat_screen_heads.jpg",
            "featured": True
        },
        {
            "name": "Stork PD Line Coating 64-R Screen Head",
            "part_number": "DTC-SH-PD-64R",
            "cat": "Screen Head Parts",
            "make": "Stork (RD-3 & RD-4)",
            "desc": "Specialized PD Line Coating Screen Head 64-R repeat for rotary paste coating and screen printing.",
            "specs": "Repeat Size: 640mm (64R)\nCoating: Hard chrome wear coating\nApplication: Stork PD Line Coating Unit",
            "repeat": "640mm (64R)",
            "material": "Chrome Plated Steel",
            "image": "/static/images/cat_screen_heads.jpg",
            "featured": False
        },

        # Gears & Gear Sets
        {
            "name": "Repeat Gear Set Stork-MBK 64-R",
            "part_number": "DTC-GR-STK-64R",
            "cat": "Gears & Gear Sets",
            "make": "MBK",
            "desc": "CNC gear cut repeat gear set for Stork and MBK rotary printing machines with 64-R repeat configuration. Zero-backlash precision teeth.",
            "specs": "Repeat: 640mm (64-R)\nTeeth Profile: Involute CNC hobbed & induction hardened\nMachine: Stork RD-3, RD-4, MBK",
            "repeat": "640mm (64R)",
            "material": "EN24 / Case Hardened Steel",
            "image": "/static/images/cat_gears.jpg",
            "featured": True
        },
        {
            "name": "Repeat Gear Set Stork-MBK (81.9-R / 91.4-R / 101.8-R)",
            "part_number": "DTC-GR-STK-COMBO",
            "cat": "Gears & Gear Sets",
            "make": "MBK",
            "desc": "High accuracy repeat gear set for large repeats on Stork and MBK machines. Ensures smooth sync and high printing definition.",
            "specs": "Repeats: 81.9-R, 91.4-R, 101.8-R\nPrecision Grade: DIN 6\nHardness: 58-62 HRC",
            "repeat": "81.9R, 91.4R, 101.8R",
            "material": "Induction Hardened Alloy Steel",
            "image": "/static/images/cat_gears.jpg",
            "featured": False
        },
        {
            "name": "Stork / Zimmer Type Head Gear Set",
            "part_number": "DTC-GR-ZIM-HEAD",
            "cat": "Gears & Gear Sets",
            "make": "Zimmer",
            "desc": "Precision head gear set compatible with Zimmer and Stork rotary screen head drive mechanisms.",
            "specs": "Compatibility: Zimmer / Stork Rotary Printing M/C\nIncludes: Driving gear, driven gear, pinion\nFinish: Ground teeth",
            "repeat": "Universal Repeats",
            "material": "Phosphor Bronze & Hardened Steel",
            "image": "/static/images/cat_gears.jpg",
            "featured": False
        },
        {
            "name": "Worm & Worm Wheel Drive Set",
            "part_number": "DTC-GR-WRM-01",
            "cat": "Gears & Gear Sets",
            "make": "Stork (RD-3 & RD-4)",
            "desc": "Precision worm and bronze worm wheel for smooth speed reduction and drive synchronization in rotary screen printing.",
            "specs": "Material: High grade PB2 phosphor bronze wheel with case-hardened alloy worm shaft\nRatio: Standard OEM match",
            "repeat": "All Repeats",
            "material": "Phosphor Bronze (PB2) + Steel Worm",
            "image": "/static/images/cat_gears.jpg",
            "featured": True
        },
        {
            "name": "RD3 & RD4 Drive Box Assembly",
            "part_number": "DTC-DB-RD34",
            "cat": "Gears & Gear Sets",
            "make": "Stork (RD-3 & RD-4)",
            "desc": "Complete Drive Box transmission assembly for RD3 & RD4 printing machines. Sealed lubrication design.",
            "specs": "Includes: Main drive gear, drive housing, bearings, input/output flanges\nTested for: Zero vibration at high RPM",
            "repeat": "All Repeats",
            "material": "Cast Iron GGG40 + Hardened Gears",
            "image": "/static/images/cat_gears.jpg",
            "featured": False
        },

        # Pumps & Accessories
        {
            "name": "Colour Pump Type SB-4 / SB-5 / SB-7 for Rotary Printing Machine",
            "part_number": "DTC-PUMP-SB457",
            "cat": "Pumps & Accessories",
            "make": "Stork (RD-3 & RD-4)",
            "desc": "Industrial colour feeding pump (Type SB-4, SB-5, SB-7) designed specifically for continuous paste transfer in rotary textile printing machines.",
            "specs": "Pump Type: SB-4 / SB-5 / SB-7 Rotary Screen Paste Pump\nFlow Rate: High volumetric efficiency\nFlange: Universal mounting\nMotor Compatibility: Standard 3-phase flange motor",
            "repeat": "Universal",
            "material": "Cast Iron Casing with Stainless Steel Internal Rotor",
            "image": "/static/images/cat_pumps.jpg",
            "featured": True
        },
        {
            "name": "Colour Pump Impeller & Rotor Assembly",
            "part_number": "DTC-PUMP-ROTOR",
            "cat": "Pumps & Accessories",
            "make": "Stormac",
            "desc": "High precision internal rotor and bronze impeller for rotary printing colour feed pumps.",
            "specs": "Wear resistant material\nDirect replacement for SB series colour pumps",
            "repeat": "Universal",
            "material": "SS316 / Bronze",
            "image": "/static/images/cat_pumps.jpg",
            "featured": False
        },

        # Squeegee Blades & Suspensions
        {
            "name": "High Quality Squeegee Blade Steel Coils (25m, 50m, 100m)",
            "part_number": "DTC-SQ-BLADE-COIL",
            "cat": "Squeegee Blades & Suspensions",
            "make": "Stork (RD-3 & RD-4)",
            "desc": "Premium Swedish blue/white spring steel squeegee blades for razor-sharp textile printing results. Available in standard and custom thickness/widths.",
            "specs": "Available Sizes: 40 x 0.15mm, 45 x 0.15mm, 50 x 0.15mm, 55 x 0.15mm, 40 x 0.20mm, 45 x 0.20mm, 50 x 0.20mm, 55 x 0.20mm\nLengths: 25 Meter, 50 Meter, 100 Meter Coils\nCustom sizes available on request",
            "repeat": "All Machine Sizes",
            "material": "Premium Hardened Spring Steel",
            "image": "/static/images/cat_squeegee.jpg",
            "featured": True
        },
        {
            "name": "Squeegee Suspension Blade Holder Unit",
            "part_number": "DTC-SQ-SUSP-01",
            "cat": "Squeegee Blades & Suspensions",
            "make": "Stork (RD-3 & RD-4)",
            "desc": "Precision squeegee suspension blade holder assembly with micro-adjustment knobs and spring tensioners for RD3 & RD4 machines.",
            "specs": "Adjustment: Micro angle and pressure settings\nFeatures: Quick blade clamp mechanism\nCorrosion proof anodized body",
            "repeat": "Universal",
            "material": "CNC Aluminium Alloy & Stainless Steel",
            "image": "/static/images/cat_squeegee.jpg",
            "featured": False
        },

        # Rollers & Shafts
        {
            "name": "Precision Magnetic Printing Roller & Beam",
            "part_number": "DTC-ROL-MAG-01",
            "cat": "Rollers & Shafts",
            "make": "Zimmer",
            "desc": "Precision ground magnetic printing roller bar and beam for uniform magnetic pressure distribution across the rotary screen.",
            "specs": "Diameter: Standard 12mm, 15mm, 20mm, 25mm\nSurface: Ground & polished stainless steel\nEven magnetic flux",
            "repeat": "Universal Widths (1800mm - 3400mm)",
            "material": "High Permeability Stainless Steel",
            "image": "/static/images/cat_rollers.jpg",
            "featured": True
        },
        {
            "name": "Spline Drive Shaft for Rotary Screen",
            "part_number": "DTC-SFT-SPLINE-02",
            "cat": "Rollers & Shafts",
            "make": "Stork (RD-3 & RD-4)",
            "desc": "High torque precision involute spline drive shaft for screen head transmission with zero vibration.",
            "specs": "Spline Standard: DIN 5480\nLength: Custom to machine width\nHeat Treatment: Induction hardened splines",
            "repeat": "All Repeats",
            "material": "EN19 / 4140 Alloy Steel",
            "image": "/static/images/cat_rollers.jpg",
            "featured": False
        },

        # Machine Components
        {
            "name": "Precision Machine Mounting Brackets & Tensioners",
            "part_number": "DTC-MC-BRK-SET",
            "cat": "Machine Components",
            "make": "Stormac",
            "desc": "Wide range of essential metal brackets, spring tensioners, and pivot pins for smooth machine operation and long-lasting performance.",
            "specs": "Includes: L-brackets, tensioning linkages, pivot pins, adjustable clamps\nSurface: Zinc passivated / black oxide",
            "repeat": "Universal",
            "material": "Forged Carbon Steel & Zinc Plating",
            "image": "/static/images/cat_components.jpg",
            "featured": True
        },
        {
            "name": "Heavy Duty Flexible Bellows & Shaft Couplings",
            "part_number": "DTC-MC-CPL-FLEX",
            "cat": "Machine Components",
            "make": "Stork (RD-3 & RD-4)",
            "desc": "Zero-backlash stainless steel bellows coupling and jaw couplings for rotary printing drive shaft alignment.",
            "specs": "Bore Sizes: 15mm to 45mm\nHigh torsional stiffness\nCompensates for angular and parallel misalignment",
            "repeat": "Universal",
            "material": "Stainless Steel Bellows & Aluminium Hubs",
            "image": "/static/images/cat_components.jpg",
            "featured": False
        },
        {
            "name": "Self-Lubricating Precision Brass Bushings & Collars",
            "part_number": "DTC-MC-BSH-SET",
            "cat": "Machine Components",
            "make": "Harish",
            "desc": "Flanged and cylindrical sintered bronze and brass bushings for screen heads and guide roller shafts.",
            "specs": "Types: Flanged & Plain Cylindrical\nSelf-lubricating oil impregnated\nHigh load capacity",
            "repeat": "Universal",
            "material": "Sintered Bronze / Gunmetal CuSn8",
            "image": "/static/images/cat_components.jpg",
            "featured": False
        },

        # Spares for Stovec & Stenter
        {
            "name": "Spares for Stovec Rotary Printing Machine",
            "part_number": "DTC-STV-SPARE-01",
            "cat": "Spares for Stovec & Stenter",
            "make": "Stovec",
            "desc": "Specialized replacement spares for Stovec rotary printing machines including wear rings, seal plates, and guide bearings.",
            "specs": "OEM compatible dimensions\nHigh temperature and chemical resistance",
            "repeat": "64R, 81.9R, 91.4R",
            "material": "Alloy Steel / Engineering Polymers",
            "image": "/static/images/hero_parts.jpg",
            "featured": True
        },
        {
            "name": "Stenter Processing Machine Spares & Pin Plates",
            "part_number": "DTC-STN-PIN-PLATE",
            "cat": "Spares for Stovec & Stenter",
            "make": "Stovec",
            "desc": "High precision pin plates, clip chains, graphite lube bushes, and edge spreaders for textile stenter processing machines.",
            "specs": "Applications: Hot air stenter frames, drying ranges\nHeat treated precision brass pins",
            "repeat": "Universal",
            "material": "Brass Pin Base with High Tensile Steel Pins",
            "image": "/static/images/hero_parts.jpg",
            "featured": False
        },

        # Washing & Cleaning
        {
            "name": "Rotary Screen Washing and Cleaning Box Unit",
            "part_number": "DTC-WSH-BOX-01",
            "cat": "Washing and Cleaning Units",
            "make": "Stork (RD-3 & RD-4)",
            "desc": "Complete washing and cleaning box unit with high-pressure internal water spray nozzles and squeegee wash manifold for RD3 & RD4 machines.",
            "specs": "Nozzle configuration: High pressure flat fan\nDrainage: Stainless steel sump\nFittings: Quick connect water couplings",
            "repeat": "Universal",
            "material": "SS304 Stainless Steel & Brass Nozzles",
            "image": "/static/images/cat_components.jpg",
            "featured": False
        }
    ]

    for p in products_data:
        prod = Product.query.filter_by(part_number=p["part_number"]).first()
        if not prod:
            cat_obj = cat_map.get(p["cat"])
            make_obj = make_map.get(p["make"])
            
            # Short description: 1-2 concise lines
            desc_text = p.get("desc", "")
            short_desc = p.get("short_desc") or (desc_text.split(".")[0] + "." if "." in desc_text else desc_text[:120])
            
            prod = Product(
                name=p["name"],
                part_number=p["part_number"],
                slug=slugify(p["name"]),
                category_id=cat_obj.id if cat_obj else 1,
                machine_make_id=make_obj.id if make_obj else None,
                short_description=short_desc,
                description=desc_text,
                specifications=p["specs"],
                repeat_sizes=p["repeat"],
                material=p["material"],
                image_url=p["image"],
                is_featured=p["featured"],
                is_active=True,
                stock_status=p.get("stock_status", "in_stock")
            )
            db.session.add(prod)
    
    # 5. Site Settings & Full CMS Appearance Controls
    settings_data = [
        # Branding & Theme
        {"key": "company_name", "val": "DIVYA TRADING CO.", "desc": "Company Name"},
        {"key": "company_tagline", "val": "all type rotary printing machine spares", "desc": "Company Tagline"},
        {"key": "site_logo", "val": "/static/images/logo.png", "desc": "Header Logo URL"},
        {"key": "theme_primary_color", "val": "#0A2540", "desc": "Primary Dark Navy Color"},
        {"key": "theme_accent_color", "val": "#0052CC", "desc": "Accent Blue Color"},
        
        # Contact Information
        {"key": "phone_primary", "val": "+91 83208 21579", "desc": "Primary Phone / WhatsApp"},
        {"key": "phone_secondary", "val": "+91 94260 64807", "desc": "Secondary Phone"},
        {"key": "email_primary", "val": "divya.trading06@gmail.com", "desc": "Primary Email"},
        {"key": "email_secondary", "val": "neelbarot585@gmail.com", "desc": "Secondary Email"},
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
        {"key": "show_whatsapp_button", "val": "true", "desc": "Show Floating WhatsApp Button"}
    ]
    
    for s in settings_data:
        existing = SiteSetting.query.filter_by(key=s["key"]).first()
        if not existing:
            setting = SiteSetting(key=s["key"], value=s["val"], description=s["desc"])
            db.session.add(setting)

    db.session.commit()
    print("Catalog, categories, and full CMS settings seeded successfully!")

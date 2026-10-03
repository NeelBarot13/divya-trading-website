import csv
import io
import re
from datetime import datetime
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

from models import db, Category, MachineMake, Product
from seed_data import slugify


def export_inquiries_csv(inquiries):
    """
    Exports a list of inquiries to a CSV string.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # Header
    writer.writerow([
        'Inquiry Ref #',
        'Date (UTC)',
        'Customer Name',
        'Company Name',
        'Email',
        'Phone',
        'Country',
        'Machine Model',
        'Status',
        'Product Name',
        'Part Number',
        'Quantity',
        'Item Notes',
        'Customer Message',
        'Admin Notes'
    ])
    
    for inq in inquiries:
        created_str = inq.created_at.strftime('%Y-%m-%d %H:%M') if inq.created_at else ''
        if inq.items:
            for item in inq.items:
                writer.writerow([
                    inq.inquiry_number,
                    created_str,
                    inq.customer_name,
                    inq.company_name or '',
                    inq.email,
                    inq.phone,
                    inq.country or '',
                    inq.machine_model or '',
                    inq.status,
                    item.product_name,
                    item.part_number or '',
                    item.quantity,
                    item.notes or '',
                    inq.message or '',
                    inq.admin_notes or ''
                ])
        else:
            writer.writerow([
                inq.inquiry_number,
                created_str,
                inq.customer_name,
                inq.company_name or '',
                inq.email,
                inq.phone,
                inq.country or '',
                inq.machine_model or '',
                inq.status,
                'General Inquiry',
                '',
                1,
                '',
                inq.message or '',
                inq.admin_notes or ''
            ])
            
    output.seek(0)
    return output.getvalue()


def export_products_csv(products):
    """
    Exports product catalog to CSV format.
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    writer.writerow([
        'ID',
        'Part Number',
        'Product Name',
        'Category',
        'Machine Make',
        'Stock Status',
        'Short Description',
        'Detailed Description',
        'Specifications',
        'Repeat Sizes',
        'Material',
        'Featured',
        'Active',
        'Image URL',
        'Created Date'
    ])
    
    for p in products:
        writer.writerow([
            p.id,
            p.part_number,
            p.name,
            p.category.name if p.category else '',
            p.machine_make.name if p.machine_make else 'Universal',
            p.stock_status or 'in_stock',
            p.short_description or '',
            p.description or '',
            p.specifications or '',
            p.repeat_sizes or '',
            p.material or '',
            'Yes' if p.is_featured else 'No',
            'Yes' if p.is_active else 'No',
            p.image_url or '',
            p.created_at.strftime('%Y-%m-%d') if p.created_at else ''
        ])
        
    output.seek(0)
    return output.getvalue()


def generate_product_template_excel(categories=None, machines=None):
    """
    Generates a beautifully styled demo Excel template (.xlsx) for bulk product import.
    Includes realistic sample rows and a dedicated reference guide sheet.
    """
    if categories is None:
        categories = Category.query.order_by(Category.name).all()
    if machines is None:
        machines = MachineMake.query.order_by(MachineMake.name).all()

    wb = openpyxl.Workbook()
    
    # ----------------------------------------------------
    # Sheet 1: Product Import Data Entry
    # ----------------------------------------------------
    ws = wb.active
    ws.title = "Products_Import"
    ws.views.sheetView[0].showGridLines = True

    # Styling definitions
    header_fill = PatternFill(start_color="0B2545", end_color="0B2545", fill_type="solid")
    header_font = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
    
    sample_font = Font(name="Segoe UI", size=10, color="1E293B")
    sample_fill_even = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")
    sample_fill_odd = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
    
    thin_border_side = Side(border_style="thin", color="CBD5E1")
    cell_border = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    
    headers = [
        "Part Number *",
        "Product Name *",
        "Category *",
        "Machine Make",
        "Stock Status",
        "Short Description",
        "Detailed Description",
        "Specifications",
        "Repeat Sizes",
        "Material Grade",
        "Featured (Yes/No)",
        "Active (Yes/No)",
        "Image Preset or URL"
    ]
    
    ws.append(headers)
    ws.row_dimensions[1].height = 28
    
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        cell.border = cell_border

    # Demo / Sample Rows for user guidance
    demo_rows = [
        [
            "DTC-SH-RD4-64R",
            "Stork RD-4 Screen Head Ring 64R Assembly",
            "Screen Heads & End Rings",
            "Stork (RD-3 & RD-4)",
            "in_stock",
            "High precision 64R rotary screen head ring for Stork RD-4 rotary machines.",
            "Manufactured from high-grade aircraft aluminium alloy ensuring strict concentricity, minimal runout, and long operating life under continuous printing pressure.",
            "Repeat: 640mm (64R) | Concentricity: <0.015mm | Finish: Hard Anodized | Weight: 4.8kg",
            "64R",
            "Alloy Steel & CNC Aluminium",
            "Yes",
            "Yes",
            "/static/images/cat_screen_heads.jpg"
        ],
        [
            "DTC-GR-RD4-64R-M3",
            "Main Drive Repeat Spur Gear 64R (Module 3)",
            "Gears & Transmission",
            "Stork (RD-3 & RD-4)",
            "in_stock",
            "Precision ground repeat gear for synchronized rotary printing drive transmission.",
            "Case-hardened steel repeat gear with induction-hardened teeth providing maximum wear resistance in harsh print house environments.",
            "Module: 3 | Teeth: 64 | Bore: 45mm H7 | Hardness: HRC 58-62",
            "64R, 81.9R",
            "EN353 Case Hardened Steel",
            "No",
            "Yes",
            "/static/images/cat_gears.jpg"
        ],
        [
            "DTC-CP-SS-01",
            "Stainless Steel Color Pump 1-Inch",
            "Colour Pumps & Spares",
            "Universal",
            "in_stock",
            "Pneumatic diaphragm color pump for viscous dye and pigment paste transfer.",
            "Corrosion resistant SS-316 body color feed pump designed for rotary printing machine print paste feed systems.",
            "Inlet/Outlet: 1\" BSP | Flow Rate: 45 L/min | Max Air Pressure: 7 Bar | Diaphragm: PTFE",
            "",
            "Stainless Steel 316",
            "Yes",
            "Yes",
            "/static/images/cat_pumps.jpg"
        ],
        [
            "DTC-SQ-SS-020",
            "Squeegee Blade Coil 0.20mm x 50mm",
            "Squeegee Blades & Holders",
            "Zimmer",
            "made_to_order",
            "Imported Swedish stainless steel doctor squeegee blade coil.",
            "Precision ground edge doctor blade providing uniform color paste penetration across wide printing widths.",
            "Thickness: 0.20mm | Width: 50mm | Coil Length: 100 meters | Straightness: 0.1mm/m",
            "",
            "Swedish Spring Steel",
            "No",
            "Yes",
            "/static/images/cat_squeegee.jpg"
        ],
        [
            "DTC-BR-SKF-6008",
            "Heavy Duty Sealed Bearing Unit 6008-2RS",
            "Bearings & Bushes",
            "Universal",
            "in_stock",
            "Deep groove sealed ball bearing for rotary machine head assemblies.",
            "High temperature grease packed bearing with dual rubber seals protecting against dye ingress and corrosion.",
            "ID: 40mm | OD: 68mm | Width: 15mm | Dynamic Load: 17.8 kN",
            "",
            "Chrome Steel (GCr15)",
            "No",
            "Yes",
            "/static/images/hero_parts.jpg"
        ]
    ]

    for row_idx, row_data in enumerate(demo_rows, start=2):
        ws.append(row_data)
        ws.row_dimensions[row_idx].height = 24
        fill = sample_fill_even if row_idx % 2 == 0 else sample_fill_odd
        for col_idx in range(1, len(row_data) + 1):
            cell = ws.cell(row=row_idx, column=col_idx)
            cell.font = sample_font
            cell.fill = fill
            cell.border = cell_border
            align_h = "center" if col_idx in (1, 4, 5, 9, 11, 12) else "left"
            cell.alignment = Alignment(horizontal=align_h, vertical="center")

    # Column widths
    col_widths = {
        1: 22,  # Part Number
        2: 38,  # Product Name
        3: 28,  # Category
        4: 24,  # Machine Make
        5: 18,  # Stock Status
        6: 45,  # Short Description
        7: 55,  # Detailed Description
        8: 42,  # Specifications
        9: 18,  # Repeat Sizes
        10: 25, # Material Grade
        11: 18, # Featured
        12: 16, # Active
        13: 35  # Image URL
    }
    for col_num, width in col_widths.items():
        ws.column_dimensions[get_column_letter(col_num)].width = width

    # ----------------------------------------------------
    # Sheet 2: Reference Guide & Help
    # ----------------------------------------------------
    ws2 = wb.create_sheet(title="Reference_Guide")
    ws2.views.sheetView[0].showGridLines = True
    
    ref_header_fill = PatternFill(start_color="1E3A8A", end_color="1E3A8A", fill_type="solid")
    ref_sub_fill = PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid")
    ref_sub_font = Font(name="Segoe UI", size=10, bold=True, color="1E3A8A")

    # Title block
    ws2.merge_cells("A1:D1")
    title_cell = ws2.cell(row=1, column=1, value="DIVYA TRADING CO. - EXCEL BULK PRODUCT IMPORT REFERENCE GUIDE")
    title_cell.fill = ref_header_fill
    title_cell.font = Font(name="Segoe UI", size=12, bold=True, color="FFFFFF")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws2.row_dimensions[1].height = 32

    # Column Headers for Reference Guide
    ref_headers = ["Existing Categories", "Existing Machine Makes", "Valid Stock Statuses", "Instructions & Helpful Tips"]
    ws2.append(ref_headers)
    ws2.row_dimensions[2].height = 24
    for col_idx in range(1, 5):
        cell = ws2.cell(row=2, column=col_idx)
        cell.fill = ref_sub_fill
        cell.font = ref_sub_font
        cell.alignment = Alignment(horizontal="center", vertical="center")
        cell.border = cell_border

    cat_names = [c.name for c in categories] if categories else ["Screen Heads & End Rings", "Gears & Transmission", "Colour Pumps & Spares", "Squeegee Blades & Holders", "Bearings & Bushes"]
    make_names = [m.name for m in machines] if machines else ["Universal", "Stork (RD-3 & RD-4)", "Stormac", "Pegasus / RD-DD", "Ichinose", "Reggiani", "Zimmer"]
    stock_statuses = [
        "in_stock (Item is in stock ready to ship)",
        "out_of_stock (Item temporarily out of stock)",
        "made_to_order (Manufactured / imported on order)"
    ]
    instructions = [
        "1. Required fields are Part Number, Product Name, and Category (marked with *).",
        "2. If you type a Category that doesn't exist yet, our system will automatically create it for you!",
        "3. If you type a Machine Make that doesn't exist yet, our system will automatically create it.",
        "4. Part Number is used as the unique key. If a product with the same Part Number exists, it will update it.",
        "5. Stock Status accepts: 'in_stock', 'out_of_stock', or 'made_to_order'.",
        "6. Featured and Active accept: 'Yes' or 'No'. Default is Active=Yes, Featured=No.",
        "7. You can leave Image URL blank to use the default spare part graphic.",
        "8. You can add as many rows as you need, then save and upload this Excel file in the admin panel."
    ]

    max_len = max(len(cat_names), len(make_names), len(stock_statuses), len(instructions))
    for i in range(max_len):
        r_idx = i + 3
        c_val = cat_names[i] if i < len(cat_names) else ""
        m_val = make_names[i] if i < len(make_names) else ""
        s_val = stock_statuses[i] if i < len(stock_statuses) else ""
        tip_val = instructions[i] if i < len(instructions) else ""
        
        ws2.append([c_val, m_val, s_val, tip_val])
        ws2.row_dimensions[r_idx].height = 20
        for col_idx in range(1, 5):
            c = ws2.cell(row=r_idx, column=col_idx)
            c.font = Font(name="Segoe UI", size=9, color="334155")
            c.border = cell_border
            if col_idx == 4:
                c.alignment = Alignment(horizontal="left", vertical="center")
            else:
                c.alignment = Alignment(horizontal="center", vertical="center")

    ws2.column_dimensions['A'].width = 30
    ws2.column_dimensions['B'].width = 28
    ws2.column_dimensions['C'].width = 40
    ws2.column_dimensions['D'].width = 75

    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return output.getvalue()


def import_products_from_file(file_storage, update_existing=True):
    """
    Parses and imports products from an uploaded Excel (.xlsx, .xls) or CSV file.
    
    Features:
    - Flexible column matching (case-insensitive, trims punctuation/spaces)
    - Automatic category matching & creation if category does not exist
    - Automatic machine make matching & creation
    - Safe unique slug generation
    - Seamless update of existing products if Part Number matches
    - Informative return statistics & row-by-row error logs
    """
    if isinstance(file_storage, str):
        filename = file_storage.lower()
        file_obj = open(file_storage, 'rb')
    else:
        filename = (getattr(file_storage, 'filename', '') or '').lower()
        file_obj = getattr(file_storage, 'stream', file_storage)

    rows_data = []

    # 1. Read file rows into standardized dictionaries
    if filename.endswith('.csv'):
        # Parse CSV
        content = file_obj.read()

        for encoding in ('utf-8-sig', 'utf-8', 'latin-1', 'cp1252'):
            try:
                text = content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            text = content.decode('utf-8', errors='replace')
            
        reader = csv.reader(io.StringIO(text))
        all_lines = list(reader)
        if not all_lines:
            return {'success': False, 'message': 'Uploaded CSV file is completely empty.', 'created': 0, 'updated': 0, 'skipped': 0, 'total': 0, 'errors': []}
        
        header_row = None
        data_rows = []
        for line in all_lines:
            if not any(cell.strip() for cell in line):
                continue
            if header_row is None:
                header_row = [str(c).strip() for c in line]
            else:
                data_rows.append([str(c).strip() for c in line])
    else:
        # Parse Excel (.xlsx, .xls) via openpyxl
        try:
            wb = openpyxl.load_workbook(file_obj, data_only=True)
            # Find the best sheet (look for 'import' or 'product' or take the active one)
            target_sheet = None
            for sname in wb.sheetnames:
                if 'import' in sname.lower() or 'product' in sname.lower():
                    target_sheet = wb[sname]
                    break
            if target_sheet is None:
                target_sheet = wb.active
                
            header_row = None
            data_rows = []
            for row in target_sheet.iter_rows(values_only=True):
                # Filter empty rows
                if not any(val is not None and str(val).strip() != '' for val in row):
                    continue
                row_vals = []
                for v in row:
                    if v is None:
                        row_vals.append('')
                    elif isinstance(v, float) and v.is_integer():
                        row_vals.append(str(int(v)))
                    else:
                        row_vals.append(str(v).strip())
                        
                if header_row is None:
                    header_row = row_vals
                else:
                    data_rows.append(row_vals)
        except Exception as e:
            return {
                'success': False,
                'message': f'Failed to read Excel workbook: {str(e)}',
                'created': 0, 'updated': 0, 'skipped': 0, 'total': 0, 'errors': [str(e)]
            }

    if not header_row or not data_rows:
        return {
            'success': False,
            'message': 'No product data rows found in the uploaded file.',
            'created': 0, 'updated': 0, 'skipped': 0, 'total': 0, 'errors': []
        }

    # Map headers to standard field keys
    def normalize_header(h):
        return re.sub(r'[^a-z0-9]', '', str(h).lower())

    header_map = {}
    field_patterns = {
        'part_number': ('partnumber', 'partno', 'partnum', 'part', 'code', 'itemcode', 'sku'),
        'name': ('productname', 'name', 'product', 'title', 'itemname'),
        'category': ('category', 'categoryname', 'cat', 'categoryslug'),
        'machine_make': ('machinemake', 'make', 'machine', 'brand', 'machinemodel', 'model'),
        'stock_status': ('stockstatus', 'stock', 'availability', 'stockavailability'),
        'short_description': ('shortdescription', 'shortdesc', 'summary', 'carddescription', 'shortoverview'),
        'description': ('detaileddescription', 'description', 'desc', 'fulldescription', 'details', 'technicaldescription'),
        'specifications': ('specifications', 'specs', 'specification', 'technicalspecifications', 'techspecs'),
        'repeat_sizes': ('repeatsizes', 'repeatsize', 'repeat', 'repeats'),
        'material': ('materialgrade', 'material', 'composition', 'metal'),
        'is_featured': ('featured', 'isfeatured', 'highlight'),
        'is_active': ('active', 'isactive', 'status', 'livestatus', 'enabled'),
        'image_url': ('imagepresetorurl', 'imageurl', 'image', 'photo', 'preset', 'photourl')
    }

    for idx, raw_h in enumerate(header_row):
        norm = normalize_header(raw_h)
        for field, patterns in field_patterns.items():
            if norm in patterns and field not in header_map:
                header_map[field] = idx
                break

    # Check minimum required mappings
    if 'name' not in header_map or 'part_number' not in header_map:
        return {
            'success': False,
            'message': f"Missing essential column headers. Required columns are 'Product Name' and 'Part Number'. Found columns: {', '.join(header_row)}",
            'created': 0, 'updated': 0, 'skipped': 0, 'total': len(data_rows), 'errors': []
        }

    created_count = 0
    updated_count = 0
    skipped_count = 0
    errors = []

    # Cache categories and machines to minimize DB lookups
    category_cache = {c.name.strip().lower(): c for c in Category.query.all()}
    category_slug_cache = {c.slug: c for c in Category.query.all()}
    machine_cache = {m.name.strip().lower(): m for m in MachineMake.query.all()}
    machine_slug_cache = {m.slug: m for m in MachineMake.query.all()}

    # Ensure a fallback category exists
    default_category = Category.query.first()
    if not default_category:
        default_category = Category(
            name="General Spare Parts",
            slug="general-spare-parts",
            description="General replacement spare parts and components for textile rotary machines."
        )
        db.session.add(default_category)
        db.session.commit()
        category_cache[default_category.name.lower()] = default_category
        category_slug_cache[default_category.slug] = default_category

    for row_num, row in enumerate(data_rows, start=2):
        def get_val(field, default=''):
            if field in header_map and header_map[field] < len(row):
                val = str(row[header_map[field]]).strip()
                return val if val else default
            return default

        name = get_val('name')
        part_number = get_val('part_number')

        if not name and not part_number:
            # Empty row, ignore
            continue

        if not name:
            errors.append(f"Row {row_num}: Missing 'Product Name' for item with Part Number '{part_number}'. Skipped.")
            continue
        if not part_number:
            errors.append(f"Row {row_num}: Missing 'Part Number' for product '{name}'. Skipped.")
            continue

        # 1. Resolve Category
        cat_str = get_val('category')
        category_obj = None
        if cat_str:
            cat_lower = cat_str.lower()
            cat_slug = slugify(cat_str)
            if cat_lower in category_cache:
                category_obj = category_cache[cat_lower]
            elif cat_slug in category_slug_cache:
                category_obj = category_slug_cache[cat_slug]
            else:
                # Create category dynamically
                new_cat = Category(
                    name=cat_str,
                    slug=cat_slug,
                    description=f"Precision replacement parts and spares for {cat_str}."
                )
                db.session.add(new_cat)
                db.session.commit()
                category_cache[cat_lower] = new_cat
                category_slug_cache[cat_slug] = new_cat
                category_obj = new_cat
        else:
            category_obj = default_category

        # 2. Resolve Machine Make
        make_str = get_val('machine_make')
        machine_obj = None
        if make_str and make_str.lower() not in ('universal', 'all makes', 'all', '-', 'none', 'n/a'):
            make_lower = make_str.lower()
            make_slug = slugify(make_str)
            if make_lower in machine_cache:
                machine_obj = machine_cache[make_lower]
            elif make_slug in machine_slug_cache:
                machine_obj = machine_slug_cache[make_slug]
            else:
                # Create machine make dynamically
                new_make = MachineMake(
                    name=make_str,
                    slug=make_slug,
                    description=f"Spare parts and consumables for {make_str} machines."
                )
                db.session.add(new_make)
                db.session.commit()
                machine_cache[make_lower] = new_make
                machine_slug_cache[make_slug] = new_make
                machine_obj = new_make

        # 3. Resolve Stock Status
        raw_stock = get_val('stock_status', 'in_stock').lower().replace('-', '_').replace(' ', '_')
        if raw_stock in ('in_stock', 'instock', 'available', 'yes', 'in'):
            stock_status = 'in_stock'
        elif raw_stock in ('out_of_stock', 'outofstock', 'unavailable', 'no', 'out'):
            stock_status = 'out_of_stock'
        elif raw_stock in ('made_to_order', 'madetoorder', 'order', 'custom', 'mto'):
            stock_status = 'made_to_order'
        else:
            stock_status = 'in_stock'

        # 4. Descriptions & Specs
        short_desc = get_val('short_description')
        desc = get_val('description')
        specs = get_val('specifications')
        repeat_sizes = get_val('repeat_sizes')
        material = get_val('material')

        if not short_desc and desc:
            short_desc = desc[:140] + ('...' if len(desc) > 140 else '')
        elif not desc and short_desc:
            desc = short_desc

        # 5. Booleans
        raw_feat = get_val('is_featured', 'no').lower()
        is_featured = raw_feat in ('yes', 'true', '1', 'y')

        raw_active = get_val('is_active', 'yes').lower()
        is_active = raw_active not in ('no', 'false', '0', 'n', 'disabled', 'inactive')

        # 6. Image URL
        image_url = get_val('image_url')
        if not image_url:
            image_url = '/static/images/hero_parts.jpg'

        # 7. Check if Product with this Part Number exists
        existing_prod = Product.query.filter(
            db.func.lower(Product.part_number) == part_number.lower()
        ).first()

        try:
            if existing_prod:
                if update_existing:
                    existing_prod.name = name
                    existing_prod.category_id = category_obj.id
                    existing_prod.machine_make_id = machine_obj.id if machine_obj else None
                    existing_prod.short_description = short_desc
                    existing_prod.description = desc
                    existing_prod.specifications = specs
                    existing_prod.repeat_sizes = repeat_sizes
                    existing_prod.material = material
                    existing_prod.stock_status = stock_status
                    existing_prod.is_featured = is_featured
                    existing_prod.is_active = is_active
                    if image_url != '/static/images/hero_parts.jpg' or not existing_prod.image_url:
                        existing_prod.image_url = image_url
                    updated_count += 1
                else:
                    skipped_count += 1
            else:
                # Generate unique slug
                base_slug = slugify(f"{name}-{part_number}")
                candidate_slug = base_slug
                counter = 1
                while Product.query.filter_by(slug=candidate_slug).first():
                    candidate_slug = f"{base_slug}-{counter}"
                    counter += 1

                new_product = Product(
                    name=name,
                    part_number=part_number,
                    slug=candidate_slug,
                    category_id=category_obj.id,
                    machine_make_id=machine_obj.id if machine_obj else None,
                    short_description=short_desc,
                    description=desc,
                    specifications=specs,
                    repeat_sizes=repeat_sizes,
                    material=material,
                    stock_status=stock_status,
                    is_featured=is_featured,
                    is_active=is_active,
                    image_url=image_url
                )
                db.session.add(new_product)
                created_count += 1
        except Exception as row_err:
            errors.append(f"Row {row_num} ('{name}'): {str(row_err)}")

    try:
        db.session.commit()
    except Exception as commit_err:
        db.session.rollback()
        return {
            'success': False,
            'message': f"Database commit failed: {str(commit_err)}",
            'created': 0, 'updated': 0, 'skipped': 0, 'total': len(data_rows), 'errors': [str(commit_err)]
        }

    total_processed = created_count + updated_count + skipped_count
    msg = f"Bulk Import Completed: {created_count} new product(s) added, {updated_count} existing product(s) updated."
    if skipped_count > 0:
        msg += f" {skipped_count} product(s) skipped (already existing)."
    if errors:
        msg += f" Encountered {len(errors)} notice(s)/issue(s)."

    return {
        'success': True,
        'message': msg,
        'created': created_count,
        'updated': updated_count,
        'skipped': skipped_count,
        'total': total_processed,
        'errors': errors
    }

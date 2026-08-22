import os
import time
import random
import string
from functools import wraps
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, session, flash, Response, send_file
from werkzeug.utils import secure_filename

from config import Config
from models import db, Category, MachineMake, Product, Inquiry, InquiryItem, InquiryMessage, CustomerUser, AdminUser, SiteSetting
from seed_data import seed_database, slugify
from email_service import notify_admin_new_inquiry, send_customer_acknowledgment, send_email, EMAIL_ACTIVITY_LOGS
from export_service import export_inquiries_csv, export_products_csv

app = Flask(__name__)
app.config.from_object(Config)

# Ensure upload directory exists
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize DB
db.init_app(app)

with app.app_context():
    db.create_all()
    seed_database()


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']


def generate_inquiry_ref():
    date_str = datetime.utcnow().strftime('%Y%m%d')
    rand_chars = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    return f"DTC-{date_str}-{rand_chars}"


def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        admin_id = session.get('admin_user_id')
        if not admin_id:
            flash('Please log in to access the admin area.', 'warning')
            return redirect(url_for('admin_login', next=request.url))
        admin = AdminUser.query.get(admin_id)
        if not admin:
            session.pop('admin_user_id', None)
            session.pop('admin_username', None)
            session.pop('admin_role', None)
            flash('Admin session expired. Please log in again.', 'warning')
            return redirect(url_for('admin_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


def customer_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        cust_id = session.get('customer_id')
        if not cust_id:
            flash('Please sign in or create an account to view your quotes.', 'info')
            return redirect(url_for('customer_login', next=request.url))
        customer = CustomerUser.query.get(cust_id)
        if not customer:
            session.pop('customer_id', None)
            session.pop('customer_name', None)
            session.pop('customer_email', None)
            session.pop('customer_company', None)
            flash('Your session has expired. Please sign in again.', 'info')
            return redirect(url_for('customer_login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function


# Context Processor for Global Template Variables
@app.context_processor
def inject_global_data():
    categories = Category.query.order_by(Category.order_index).all()
    machines = MachineMake.query.order_by(MachineMake.name).all()
    settings_records = SiteSetting.query.all()
    settings = {s.key: s.value for s in settings_records}
    current_year = datetime.utcnow().year
    
    current_customer = None
    if 'customer_id' in session:
        current_customer = CustomerUser.query.get(session['customer_id'])
        if not current_customer:
            session.pop('customer_id', None)
            session.pop('customer_name', None)
            session.pop('customer_email', None)
            session.pop('customer_company', None)
        
    return {
        'nav_categories': categories,
        'nav_machines': machines,
        'site_settings': settings,
        'current_year': current_year,
        'current_customer': current_customer
    }


# ==========================================
# PUBLIC FRONTEND ROUTES
# ==========================================

@app.route('/')
def home():
    settings_records = SiteSetting.query.all()
    settings = {s.key: s.value for s in settings_records}
    
    # Homepage featured products limit (default 4 as requested)
    try:
        featured_limit = int(settings.get('home_featured_limit', 4))
    except (ValueError, TypeError):
        featured_limit = 4
        
    featured_products = Product.query.filter_by(is_featured=True, is_active=True).limit(featured_limit).all()
    categories = Category.query.order_by(Category.order_index).all()
    machines = MachineMake.query.all()
    
    # Parse brand pills from structured JSON or fallback
    import json
    brand_pills = []
    hero_json = settings.get('hero_brands_json')
    if hero_json:
        try:
            brand_pills = json.loads(hero_json)
        except Exception:
            brand_pills = []
            
    if not brand_pills:
        raw_brands = settings.get('hero_brands', 'STORMAC, STORK, ICHINOSE, REGGIANI, HARISH, ZIMMER, STOVEC')
        brand_names = [b.strip() for b in raw_brands.split(',') if b.strip()]
        for b in brand_names:
            matched_make = MachineMake.query.filter(MachineMake.name.ilike(f"%{b}%")).first()
            if matched_make:
                brand_url = url_for('products', machine=matched_make.slug)
            else:
                brand_url = url_for('products', q=b)
            brand_pills.append({
                'name': b,
                'slug': slugify(b),
                'url': brand_url
            })
    
    return render_template(
        'index.html',
        featured_products=featured_products,
        categories=categories,
        machines=machines,
        brand_pills=brand_pills
    )


@app.route('/products')
def products():
    category_slug = request.args.get('category')
    machine_slug = request.args.get('machine')
    search_query = request.args.get('q', '').strip()
    
    query = Product.query.filter_by(is_active=True)
    
    selected_category = None
    if category_slug:
        selected_category = Category.query.filter_by(slug=category_slug).first()
        if selected_category:
            query = query.filter_by(category_id=selected_category.id)
            
    selected_machine = None
    if machine_slug:
        selected_machine = MachineMake.query.filter_by(slug=machine_slug).first()
        if selected_machine:
            query = query.filter_by(machine_make_id=selected_machine.id)
            
    if search_query:
        search_pattern = f"%{search_query}%"
        query = query.filter(
            (Product.name.ilike(search_pattern)) |
            (Product.part_number.ilike(search_pattern)) |
            (Product.description.ilike(search_pattern)) |
            (Product.repeat_sizes.ilike(search_pattern))
        )
        
    all_products = query.order_by(Product.id.desc()).all()
    categories = Category.query.order_by(Category.order_index).all()
    machines = MachineMake.query.order_by(MachineMake.name).all()
    
    return render_template(
        'products.html',
        products=all_products,
        categories=categories,
        machines=machines,
        selected_category=selected_category,
        selected_machine=selected_machine,
        search_query=search_query
    )


@app.route('/product/<slug>')
def product_detail(slug):
    product = Product.query.filter_by(slug=slug, is_active=True).first_or_404()
    
    # Related products from same category or machine make
    related_products = Product.query.filter(
        Product.id != product.id,
        Product.is_active == True,
        (Product.category_id == product.category_id) | (Product.machine_make_id == product.machine_make_id)
    ).limit(4).all()
    
    return render_template('product_detail.html', product=product, related_products=related_products)


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/machines')
def machines():
    all_machines = MachineMake.query.order_by(MachineMake.name).all()
    return render_template('machines.html', machines=all_machines)


@app.route('/download-catalog')
def download_catalog():
    return render_template('download_catalog.html')


@app.route('/contact')
def contact():
    products = Product.query.filter_by(is_active=True).order_by(Product.name).all()
    return render_template('contact.html', products=products)


# ==========================================
# CUSTOMER AUTHENTICATION & MY QUOTES PORTAL
# ==========================================

@app.route('/login', methods=['GET', 'POST'])
@app.route('/customer/login', methods=['GET', 'POST'])
def customer_login():
    if 'customer_id' in session:
        return redirect(url_for('customer_dashboard'))
        
    next_url = request.args.get('next') or request.form.get('next') or url_for('customer_dashboard')
    
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        
        user = CustomerUser.query.filter_by(email=email).first()
        if user and user.check_password(password):
            session.permanent = True
            session['customer_id'] = user.id
            session['customer_name'] = user.name
            session['customer_email'] = user.email
            session['customer_company'] = user.company_name or ''
            
            # Automatically link past guest inquiries matching this email
            Inquiry.query.filter_by(email=email, customer_id=None).update({'customer_id': user.id})
            db.session.commit()
            
            flash(f'Welcome back, {user.name}!', 'success')
            return redirect(next_url)
        else:
            flash('Invalid email address or password. Please try again.', 'danger')
            
    return render_template('customer/login.html', next_url=next_url)


@app.route('/register', methods=['GET', 'POST'])
@app.route('/customer/register', methods=['GET', 'POST'])
def customer_register():
    if 'customer_id' in session:
        return redirect(url_for('customer_dashboard'))
        
    next_url = request.args.get('next') or request.form.get('next') or url_for('customer_dashboard')
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        company_name = request.form.get('company_name', '').strip()
        email = request.form.get('email', '').strip().lower()
        phone = request.form.get('phone', '').strip()
        country = request.form.get('country', 'India').strip()
        city = request.form.get('city', '').strip()
        password = request.form.get('password', '')
        
        if not name or not email or not phone or not password:
            flash('Name, email, phone, and password are required.', 'danger')
            return render_template('customer/register.html', next_url=next_url)
            
        existing = CustomerUser.query.filter_by(email=email).first()
        if existing:
            flash('An account with this email address already exists. Please log in.', 'warning')
            return redirect(url_for('customer_login', next=next_url))
            
        user = CustomerUser(
            name=name,
            company_name=company_name,
            email=email,
            phone=phone,
            country=country,
            city=city
        )
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        
        # Link past inquiries matching this email
        Inquiry.query.filter_by(email=email).update({'customer_id': user.id})
        db.session.commit()
        
        session.permanent = True
        session['customer_id'] = user.id
        session['customer_name'] = user.name
        session['customer_email'] = user.email
        session['customer_company'] = user.company_name or ''
        
        flash(f'Account created successfully! Welcome to Divya Trading Co., {user.name}.', 'success')
        return redirect(next_url)
        
    return render_template('customer/register.html', next_url=next_url)


@app.route('/logout')
@app.route('/customer/logout')
def customer_logout():
    session.pop('customer_id', None)
    session.pop('customer_name', None)
    session.pop('customer_email', None)
    session.pop('customer_company', None)
    flash('You have been logged out of your customer portal.', 'info')
    return redirect(url_for('home'))


@app.route('/my-quotes')
@app.route('/customer/dashboard')
@customer_required
def customer_dashboard():
    customer = CustomerUser.query.get(session.get('customer_id'))
    if not customer:
        session.pop('customer_id', None)
        session.pop('customer_name', None)
        session.pop('customer_email', None)
        session.pop('customer_company', None)
        return redirect(url_for('customer_login'))
        
    inquiries = Inquiry.query.filter(
        (Inquiry.customer_id == customer.id) | (Inquiry.email == customer.email)
    ).order_by(Inquiry.id.desc()).all()
    
    # Calculate stats
    total_quotes = len(inquiries)
    pending_quotes = sum(1 for q in inquiries if q.status in ('new', 'contacted'))
    ready_quotes = sum(1 for q in inquiries if q.status == 'quoted')
    completed_quotes = sum(1 for q in inquiries if q.status == 'completed')
    
    return render_template(
        'customer/dashboard.html',
        customer=customer,
        inquiries=inquiries,
        total_quotes=total_quotes,
        pending_quotes=pending_quotes,
        ready_quotes=ready_quotes,
        completed_quotes=completed_quotes
    )


@app.route('/my-quotes/<inquiry_number>')
@customer_required
def customer_quote_detail(inquiry_number):
    customer = CustomerUser.query.get(session['customer_id'])
    inquiry = Inquiry.query.filter(
        Inquiry.inquiry_number == inquiry_number,
        (Inquiry.customer_id == customer.id) | (Inquiry.email == customer.email)
    ).first_or_404()
    
    return render_template('customer/quote_detail.html', inquiry=inquiry, customer=customer)


@app.route('/my-quotes/<inquiry_number>/comment', methods=['POST'])
@customer_required
def customer_add_comment(inquiry_number):
    customer = CustomerUser.query.get(session['customer_id'])
    inquiry = Inquiry.query.filter(
        Inquiry.inquiry_number == inquiry_number,
        (Inquiry.customer_id == customer.id) | (Inquiry.email == customer.email)
    ).first_or_404()
    
    message_text = request.form.get('message', '').strip()
    if message_text:
        msg = InquiryMessage(
            inquiry_id=inquiry.id,
            sender_type='customer',
            sender_name=customer.name,
            message=message_text
        )
        db.session.add(msg)
        inquiry.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Email notification to admin about customer reply
        admin_subject = f"💬 Customer Reply on Quote #{inquiry.inquiry_number} ({customer.name})"
        admin_body = f"""
        <h3>New Customer Message Received</h3>
        <p><strong>Customer:</strong> {customer.name} ({customer.company_name or 'Mill'})</p>
        <p><strong>Quote Ref:</strong> #{inquiry.inquiry_number}</p>
        <p><strong>Message:</strong></p>
        <blockquote style="background:#f1f5f9; padding:12px; border-left:4px solid #0052cc;">{message_text}</blockquote>
        <p><a href="{request.host_url}admin/dashboard">Open Admin Dashboard to Reply ➔</a></p>
        """
        send_email(admin_subject, app.config['ADMIN_NOTIFICATION_EMAIL'], admin_body, app.config)
        
        flash('Your message has been sent to Divya Trading Co. engineering team.', 'success')
    else:
        flash('Message content cannot be empty.', 'warning')
        
    return redirect(url_for('customer_quote_detail', inquiry_number=inquiry_number))


# ==========================================
# PUBLIC INQUIRY APIs (With Automatic Account Linking)
# ==========================================

@app.route('/api/products')
def api_products():
    category_id = request.args.get('category_id', type=int)
    machine_id = request.args.get('machine_id', type=int)
    query_str = request.args.get('q', '').strip()
    
    query = Product.query.filter_by(is_active=True)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if machine_id:
        query = query.filter_by(machine_make_id=machine_id)
    if query_str:
        pattern = f"%{query_str}%"
        query = query.filter(
            (Product.name.ilike(pattern)) |
            (Product.part_number.ilike(pattern)) |
            (Product.description.ilike(pattern))
        )
        
    products_list = query.all()
    return jsonify([p.to_dict() for p in products_list])


@app.route('/api/inquire', methods=['POST'])
def api_inquire():
    """Single product instant inquiry submission"""
    data = request.get_json() or request.form.to_dict()
    
    customer_name = data.get('customer_name', '').strip()
    email = data.get('email', '').strip().lower()
    phone = data.get('phone', '').strip()
    
    if not customer_name or not email or not phone:
        return jsonify({'success': False, 'message': 'Name, email, and phone number are required.'}), 400
        
    product_id = data.get('product_id')
    product = Product.query.get(product_id) if product_id else None
    
    inquiry_num = generate_inquiry_ref()
    
    # Check if customer user exists
    customer_user = None
    if 'customer_id' in session:
        customer_user = CustomerUser.query.get(session['customer_id'])
    elif email:
        customer_user = CustomerUser.query.filter_by(email=email).first()
        
    inquiry = Inquiry(
        inquiry_number=inquiry_num,
        customer_id=customer_user.id if customer_user else None,
        customer_name=customer_name,
        company_name=data.get('company_name', '').strip(),
        email=email,
        phone=phone,
        country=data.get('country', 'India').strip(),
        machine_model=data.get('machine_model', '').strip(),
        message=data.get('message', '').strip(),
        status='new'
    )
    db.session.add(inquiry)
    db.session.flush()
    
    # Add inquiry item
    if product:
        item = InquiryItem(
            inquiry_id=inquiry.id,
            product_id=product.id,
            product_name=product.name,
            part_number=product.part_number,
            quantity=int(data.get('quantity', 1)),
            notes=data.get('repeat_notes') or product.repeat_sizes
        )
        db.session.add(item)
    elif data.get('product_name'):
        item = InquiryItem(
            inquiry_id=inquiry.id,
            product_name=data.get('product_name'),
            part_number=data.get('part_number', ''),
            quantity=int(data.get('quantity', 1)),
            notes=data.get('notes', '')
        )
        db.session.add(item)
        
    db.session.commit()
    
    # Send email notifications
    notify_admin_new_inquiry(inquiry, app.config)
    send_customer_acknowledgment(inquiry, app.config)
    
    return jsonify({
        'success': True,
        'inquiry_number': inquiry_num,
        'message': f'Thank you! Your inquiry reference #{inquiry_num} has been received. You can view its real-time status under My Quotes.'
    })


@app.route('/api/inquiry-cart/submit', methods=['POST'])
def api_inquiry_cart_submit():
    """Multi-product Quote Cart submission"""
    data = request.get_json()
    if not data:
        return jsonify({'success': False, 'message': 'Invalid payload.'}), 400
        
    customer = data.get('customer', {})
    items_data = data.get('items', [])
    
    customer_name = customer.get('name', '').strip()
    email = customer.get('email', '').strip().lower()
    phone = customer.get('phone', '').strip()
    
    if not customer_name or not email or not phone:
        return jsonify({'success': False, 'message': 'Customer Name, Email, and Phone are required.'}), 400
        
    if not items_data:
        return jsonify({'success': False, 'message': 'Your quote cart is empty.'}), 400
        
    inquiry_num = generate_inquiry_ref()
    
    customer_user = None
    if 'customer_id' in session:
        customer_user = CustomerUser.query.get(session['customer_id'])
    elif email:
        customer_user = CustomerUser.query.filter_by(email=email).first()
        
    inquiry = Inquiry(
        inquiry_number=inquiry_num,
        customer_id=customer_user.id if customer_user else None,
        customer_name=customer_name,
        company_name=customer.get('company', '').strip(),
        email=email,
        phone=phone,
        country=customer.get('country', 'India').strip(),
        machine_model=customer.get('machine_model', '').strip(),
        message=customer.get('message', '').strip(),
        status='new'
    )
    db.session.add(inquiry)
    db.session.flush()
    
    for item in items_data:
        prod_id = item.get('id')
        prod = Product.query.get(prod_id) if prod_id else None
        
        inq_item = InquiryItem(
            inquiry_id=inquiry.id,
            product_id=prod.id if prod else None,
            product_name=prod.name if prod else item.get('name', 'General Spare Part'),
            part_number=prod.part_number if prod else item.get('part_number', ''),
            quantity=int(item.get('quantity', 1)),
            notes=item.get('notes', '') or (prod.repeat_sizes if prod else '')
        )
        db.session.add(inq_item)
        
    db.session.commit()
    
    # Dispatched emails
    notify_admin_new_inquiry(inquiry, app.config)
    send_customer_acknowledgment(inquiry, app.config)
    
    return jsonify({
        'success': True,
        'inquiry_number': inquiry_num,
        'message': f'Your quote request #{inquiry_num} for {len(items_data)} items has been submitted successfully!'
    })


# ==========================================
# ADMIN AUTHENTICATION & MANAGEMENT PANEL
# ==========================================

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if 'admin_user_id' in session:
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '').strip()
        
        admin = AdminUser.query.filter_by(username=username).first()
        if admin and admin.check_password(password):
            session.permanent = True
            session['admin_user_id'] = admin.id
            session['admin_username'] = admin.username
            session['admin_role'] = admin.role
            flash('Welcome to Divya Trading Co. Admin Portal.', 'success')
            next_page = request.args.get('next') or url_for('admin_dashboard')
            return redirect(next_page)
        else:
            flash('Invalid admin credentials. Please try again.', 'danger')
            
    return render_template('admin/login.html')


@app.route('/admin/logout')
def admin_logout():
    session.pop('admin_user_id', None)
    session.pop('admin_username', None)
    session.pop('admin_role', None)
    flash('Logged out successfully.', 'info')
    return redirect(url_for('admin_login'))


@app.route('/admin')
@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    # Filter by status or search
    status_filter = request.args.get('status')
    search_q = request.args.get('q', '').strip()
    
    query = Inquiry.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    if search_q:
        pattern = f"%{search_q}%"
        query = query.filter(
            (Inquiry.inquiry_number.ilike(pattern)) |
            (Inquiry.customer_name.ilike(pattern)) |
            (Inquiry.company_name.ilike(pattern)) |
            (Inquiry.email.ilike(pattern)) |
            (Inquiry.phone.ilike(pattern))
        )
        
    inquiries = query.order_by(Inquiry.id.desc()).all()
    
    # Stats
    total_inquiries = Inquiry.query.count()
    new_inquiries = Inquiry.query.filter_by(status='new').count()
    quoted_inquiries = Inquiry.query.filter_by(status='quoted').count()
    completed_inquiries = Inquiry.query.filter_by(status='completed').count()
    total_products = Product.query.count()
    active_products = Product.query.filter_by(is_active=True).count()
    total_customers = CustomerUser.query.count()
    
    return render_template(
        'admin/dashboard.html',
        inquiries=inquiries,
        total_inquiries=total_inquiries,
        new_inquiries=new_inquiries,
        quoted_inquiries=quoted_inquiries,
        completed_inquiries=completed_inquiries,
        total_products=total_products,
        active_products=active_products,
        total_customers=total_customers,
        current_status=status_filter,
        search_q=search_q
    )


@app.route('/admin/inquiries/<int:inquiry_id>')
@admin_required
def admin_get_inquiry(inquiry_id):
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    return jsonify(inquiry.to_dict())


@app.route('/admin/inquiries/<int:inquiry_id>/quote', methods=['POST'])
@admin_required
def admin_update_quote_details(inquiry_id):
    """Update formal quotation price, delivery, and payment terms"""
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    
    quote_amount = request.form.get('quote_amount', '').strip()
    delivery_timeline = request.form.get('delivery_timeline', '').strip()
    payment_terms = request.form.get('payment_terms', '').strip()
    quote_valid_until = request.form.get('quote_valid_until', '').strip()
    new_status = request.form.get('status', 'quoted')
    admin_notes = request.form.get('admin_notes', '').strip()
    
    inquiry.quote_amount = quote_amount
    inquiry.delivery_timeline = delivery_timeline
    inquiry.payment_terms = payment_terms
    inquiry.quote_valid_until = quote_valid_until
    inquiry.status = new_status
    inquiry.admin_notes = admin_notes
    inquiry.updated_at = datetime.utcnow()
    
    # Add an automatic message in thread
    if quote_amount:
        msg = InquiryMessage(
            inquiry_id=inquiry.id,
            sender_type='admin',
            sender_name='Divya Trading Co.',
            message=f"Quotation Prepared: Amount: {quote_amount} | Delivery: {delivery_timeline} | Payment: {payment_terms}"
        )
        db.session.add(msg)
        
    db.session.commit()
    
    # Notify customer via email
    if inquiry.email and 'notify_customer' in request.form:
        cust_subject = f"📋 Quotation Ready for Reference #{inquiry.inquiry_number} - Divya Trading Co."
        cust_body = f"""
        <h3>Your Quotation is Ready!</h3>
        <p>Dear {inquiry.customer_name},</p>
        <p>Our sales engineering team has prepared the quotation for your spare parts inquiry <strong>#{inquiry.inquiry_number}</strong>.</p>
        <div style="background:#f8fafc; border:1px solid #cbd5e1; border-radius:8px; padding:16px; margin:16px 0;">
            <p><strong>Quotation Amount:</strong> <span style="font-size:1.2rem; color:#0052cc; font-weight:bold;">{quote_amount}</span></p>
            <p><strong>Delivery Timeline:</strong> {delivery_timeline}</p>
            <p><strong>Payment Terms:</strong> {payment_terms}</p>
            <p><strong>Validity:</strong> {quote_valid_until}</p>
        </div>
        <p>You can view full quotation details, item breakdown, and chat directly with our team under your customer portal:</p>
        <p><a href="{request.host_url}my-quotes/{inquiry.inquiry_number}" style="display:inline-block; background:#0A2540; color:white; padding:10px 20px; text-decoration:none; border-radius:6px; font-weight:bold;">View My Quotation ➔</a></p>
        """
        send_email(cust_subject, inquiry.email, cust_body, app.config)
        
    flash(f'Quotation details for #{inquiry.inquiry_number} updated successfully.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/inquiries/<int:inquiry_id>/comment', methods=['POST'])
@admin_required
def admin_add_comment(inquiry_id):
    """Admin sends comment/reply to customer"""
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    message_text = request.form.get('message', '').strip()
    
    if message_text:
        msg = InquiryMessage(
            inquiry_id=inquiry.id,
            sender_type='admin',
            sender_name='Divya Trading Co. (Admin)',
            message=message_text
        )
        db.session.add(msg)
        inquiry.updated_at = datetime.utcnow()
        db.session.commit()
        
        # Email notification to customer
        if inquiry.email:
            cust_subject = f"💬 New Message on Quote #{inquiry.inquiry_number} - Divya Trading Co."
            cust_body = f"""
            <h3>New Message from Divya Trading Co.</h3>
            <p>Dear {inquiry.customer_name},</p>
            <p>Our team has sent a message regarding your inquiry <strong>#{inquiry.inquiry_number}</strong>:</p>
            <blockquote style="background:#f1f5f9; padding:12px; border-left:4px solid #0A2540;">{message_text}</blockquote>
            <p><a href="{request.host_url}my-quotes/{inquiry.inquiry_number}">View & Reply in Your Portal ➔</a></p>
            """
            send_email(cust_subject, inquiry.email, cust_body, app.config)
            
        flash('Message dispatched to customer thread successfully.', 'success')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/inquiries/<int:inquiry_id>/delete', methods=['POST'])
@admin_required
def admin_delete_inquiry(inquiry_id):
    inquiry = Inquiry.query.get_or_404(inquiry_id)
    ref = inquiry.inquiry_number
    db.session.delete(inquiry)
    db.session.commit()
    flash(f'Inquiry #{ref} deleted.', 'info')
    return redirect(url_for('admin_dashboard'))


@app.route('/admin/export/inquiries')
@admin_required
def admin_export_inquiries():
    inquiries = Inquiry.query.order_by(Inquiry.id.desc()).all()
    csv_data = export_inquiries_csv(inquiries)
    filename = f"DTC_Inquiries_Export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


# ==========================================
# ADMIN PRODUCT MANAGEMENT & QUICK TOGGLES
# ==========================================

@app.route('/admin/products')
@admin_required
def admin_products():
    category_id = request.args.get('category', type=int)
    machine_id = request.args.get('machine', type=int)
    search_q = request.args.get('q', '').strip()
    status_filter = request.args.get('status')
    
    query = Product.query
    if category_id:
        query = query.filter_by(category_id=category_id)
    if machine_id:
        query = query.filter_by(machine_make_id=machine_id)
    if status_filter == 'active':
        query = query.filter_by(is_active=True)
    elif status_filter == 'deactive':
        query = query.filter_by(is_active=False)
    elif status_filter == 'out_of_stock':
        query = query.filter_by(stock_status='out_of_stock')
        
    if search_q:
        pattern = f"%{search_q}%"
        query = query.filter(
            (Product.name.ilike(pattern)) |
            (Product.part_number.ilike(pattern)) |
            (Product.description.ilike(pattern)) |
            (Product.repeat_sizes.ilike(pattern))
        )
        
    products_list = query.order_by(Product.id.desc()).all()
    categories = Category.query.order_by(Category.order_index).all()
    machines = MachineMake.query.order_by(MachineMake.name).all()
    
    return render_template(
        'admin/products.html',
        products=products_list,
        categories=categories,
        machines=machines,
        selected_category=category_id,
        selected_machine=machine_id,
        status_filter=status_filter,
        search_q=search_q
    )


@app.route('/admin/products/add', methods=['POST'])
@admin_required
def admin_add_product():
    name = request.form.get('name', '').strip()
    part_number = request.form.get('part_number', '').strip()
    category_id = request.form.get('category_id', type=int)
    machine_make_id = request.form.get('machine_make_id', type=int) or None
    short_description = request.form.get('short_description', '').strip()
    description = request.form.get('description', '').strip()
    specifications = request.form.get('specifications', '').strip()
    repeat_sizes = request.form.get('repeat_sizes', '').strip()
    material = request.form.get('material', '').strip()
    stock_status = request.form.get('stock_status', 'in_stock')
    is_featured = 'is_featured' in request.form
    is_active = 'is_active' in request.form
    
    if not name or not part_number or not category_id:
        flash('Product name, part number, and category are required.', 'danger')
        return redirect(url_for('admin_products'))
        
    slug = slugify(f"{name}-{part_number}")
    
    # Image handling
    image_url = request.form.get('image_preset', '/static/images/hero_parts.jpg')
    if 'image_file' in request.files:
        file = request.files['image_file']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"prod_{int(time.time())}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            image_url = f"/static/uploads/{filename}"
            
    product = Product(
        name=name,
        part_number=part_number,
        slug=slug,
        category_id=category_id,
        machine_make_id=machine_make_id,
        short_description=short_description,
        description=description,
        specifications=specifications,
        repeat_sizes=repeat_sizes,
        material=material,
        image_url=image_url,
        is_featured=is_featured,
        is_active=is_active,
        stock_status=stock_status
    )
    db.session.add(product)
    db.session.commit()
    
    flash(f'Product "{name}" added successfully.', 'success')
    return redirect(url_for('admin_products'))


@app.route('/admin/products/<int:product_id>/edit', methods=['POST'])
@admin_required
def admin_edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    
    product.name = request.form.get('name', product.name).strip()
    product.part_number = request.form.get('part_number', product.part_number).strip()
    product.category_id = request.form.get('category_id', type=int) or product.category_id
    product.machine_make_id = request.form.get('machine_make_id', type=int) or None
    product.short_description = request.form.get('short_description', product.short_description or '').strip()
    product.description = request.form.get('description', '').strip()
    product.specifications = request.form.get('specifications', '').strip()
    product.repeat_sizes = request.form.get('repeat_sizes', '').strip()
    product.material = request.form.get('material', '').strip()
    product.stock_status = request.form.get('stock_status', 'in_stock')
    product.is_featured = 'is_featured' in request.form
    product.is_active = 'is_active' in request.form
    
    # Image upload
    if 'image_file' in request.files:
        file = request.files['image_file']
        if file and file.filename and allowed_file(file.filename):
            filename = secure_filename(f"prod_{int(time.time())}_{file.filename}")
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            product.image_url = f"/static/uploads/{filename}"
    elif request.form.get('image_preset'):
        product.image_url = request.form.get('image_preset')
        
    db.session.commit()
    flash(f'Product "{product.name}" updated successfully.', 'success')
    return redirect(url_for('admin_products'))


@app.route('/admin/products/<int:product_id>/toggle-active', methods=['POST'])
@admin_required
def admin_toggle_product_active(product_id):
    """1-Click Quick Toggle for Active/Deactive Product Status"""
    product = Product.query.get_or_404(product_id)
    product.is_active = not product.is_active
    db.session.commit()
    
    status_label = 'Activated' if product.is_active else 'Deactivated (Disabled from Catalog)'
    return jsonify({
        'success': True,
        'is_active': product.is_active,
        'message': f'Product "{product.name}" is now {status_label}.'
    })


@app.route('/admin/products/<int:product_id>/stock-status', methods=['POST'])
@admin_required
def admin_toggle_stock_status(product_id):
    """1-Click Quick Toggle for Stock Status (in_stock, out_of_stock, made_to_order)"""
    product = Product.query.get_or_404(product_id)
    new_status = request.form.get('stock_status') or (request.get_json() or {}).get('stock_status')
    
    if new_status in ('in_stock', 'out_of_stock', 'made_to_order'):
        product.stock_status = new_status
        db.session.commit()
        return jsonify({
            'success': True,
            'stock_status': product.stock_status,
            'message': f'Stock status updated to {new_status.replace("_", " ").title()}.'
        })
    return jsonify({'success': False, 'message': 'Invalid status'}), 400


@app.route('/admin/products/<int:product_id>/delete', methods=['POST'])
@admin_required
def admin_delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    name = product.name
    db.session.delete(product)
    db.session.commit()
    flash(f'Product "{name}" deleted.', 'info')
    return redirect(url_for('admin_products'))


@app.route('/admin/export/products')
@admin_required
def admin_export_products():
    products_list = Product.query.order_by(Product.id).all()
    csv_data = export_products_csv(products_list)
    filename = f"DTC_Products_Catalog_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    
    return Response(
        csv_data,
        mimetype='text/csv',
        headers={'Content-Disposition': f'attachment; filename={filename}'}
    )


# ==========================================
# ADMIN CUSTOMERS & CATEGORIES
# ==========================================

@app.route('/admin/customers')
@admin_required
def admin_customers():
    customers = CustomerUser.query.order_by(CustomerUser.id.desc()).all()
    return render_template('admin/customers.html', customers=customers)


@app.route('/admin/categories', methods=['GET', 'POST'])
@admin_required
def admin_categories():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add_category':
            name = request.form.get('name', '').strip()
            desc = request.form.get('description', '').strip()
            image = request.form.get('image', '/static/images/cat_screen_heads.jpg')
            order = request.form.get('order_index', 0, type=int)
            if name:
                cat = Category(name=name, slug=slugify(name), description=desc, image=image, order_index=order)
                db.session.add(cat)
                db.session.commit()
                flash(f'Category "{name}" added.', 'success')
        elif action == 'add_machine':
            name = request.form.get('name', '').strip()
            desc = request.form.get('description', '').strip()
            if name:
                m = MachineMake(name=name, slug=slugify(name), description=desc)
                db.session.add(m)
                db.session.commit()
                flash(f'Machine make "{name}" added.', 'success')
        return redirect(url_for('admin_categories'))
        
    categories = Category.query.order_by(Category.order_index).all()
    machines = MachineMake.query.order_by(MachineMake.name).all()
    return render_template('admin/categories.html', categories=categories, machines=machines)


@app.route('/admin/categories/<int:cat_id>/delete', methods=['POST'])
@admin_required
def admin_delete_category(cat_id):
    cat = Category.query.get_or_404(cat_id)
    name = cat.name
    db.session.delete(cat)
    db.session.commit()
    flash(f'Category "{name}" and associated products deleted.', 'info')
    return redirect(url_for('admin_categories'))


@app.route('/admin/machines/<int:make_id>/delete', methods=['POST'])
@admin_required
def admin_delete_machine(make_id):
    m = MachineMake.query.get_or_404(make_id)
    name = m.name
    db.session.delete(m)
    db.session.commit()
    flash(f'Machine make "{name}" deleted.', 'info')
    return redirect(url_for('admin_categories'))


# ==========================================
# ADMIN TEAM ROLES & PASSWORD MANAGEMENT (SUPER ADMIN)
# ==========================================

@app.route('/admin/users')
@admin_required
def admin_users():
    current_admin = AdminUser.query.get(session.get('admin_user_id'))
    if not current_admin or not current_admin.is_superadmin():
        flash('Access restricted to Super Administrators only.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    users = AdminUser.query.order_by(AdminUser.id.asc()).all()
    return render_template('admin/users.html', admin_users=users)


@app.route('/admin/users/add', methods=['POST'])
@admin_required
def admin_add_user():
    current_admin = AdminUser.query.get(session.get('admin_user_id'))
    if not current_admin or not current_admin.is_superadmin():
        flash('Access restricted to Super Administrators only.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    username = request.form.get('username', '').strip().lower()
    email = request.form.get('email', '').strip().lower()
    password = request.form.get('password', '').strip()
    role = request.form.get('role', 'sales_manager')
    
    if not username or not email or not password:
        flash('Username, email, and password are required.', 'danger')
        return redirect(url_for('admin_users'))
        
    if AdminUser.query.filter((AdminUser.username == username) | (AdminUser.email == email)).first():
        flash(f'An admin user with username "{username}" or email "{email}" already exists.', 'danger')
        return redirect(url_for('admin_users'))
        
    new_admin = AdminUser(
        username=username,
        email=email,
        role=role
    )
    new_admin.set_password(password)
    db.session.add(new_admin)
    db.session.commit()
    
    flash(f'Admin user "{username}" with role "{new_admin.get_role_display()}" created successfully.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/users/<int:user_id>/edit', methods=['POST'])
@admin_required
def admin_edit_user(user_id):
    current_admin = AdminUser.query.get(session.get('admin_user_id'))
    if not current_admin or not current_admin.is_superadmin():
        flash('Access restricted to Super Administrators only.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    target_user = AdminUser.query.get_or_404(user_id)
    email = request.form.get('email', '').strip().lower()
    new_password = request.form.get('new_password', '').strip()
    role = request.form.get('role')
    
    if email:
        target_user.email = email
    if role:
        target_user.role = role
    if new_password:
        target_user.set_password(new_password)
        
    db.session.commit()
    flash(f'Admin user "{target_user.username}" credentials and role updated successfully.', 'success')
    return redirect(url_for('admin_users'))


@app.route('/admin/users/<int:user_id>/delete', methods=['POST'])
@admin_required
def admin_delete_user(user_id):
    current_admin = AdminUser.query.get(session.get('admin_user_id'))
    if not current_admin or not current_admin.is_superadmin():
        flash('Access restricted to Super Administrators only.', 'danger')
        return redirect(url_for('admin_dashboard'))
        
    target_user = AdminUser.query.get_or_404(user_id)
    if target_user.username == 'admin' or target_user.id == current_admin.id:
        flash('Cannot delete primary super administrator account.', 'danger')
        return redirect(url_for('admin_users'))
        
    uname = target_user.username
    db.session.delete(target_user)
    db.session.commit()
    flash(f'Admin user "{uname}" removed.', 'info')
    return redirect(url_for('admin_users'))


# ==========================================
# ADMIN SETTINGS & FULL WEBSITE CMS
# ==========================================

@app.route('/admin/settings', methods=['GET', 'POST'])
@admin_required
def admin_settings():
    if request.method == 'POST':
        action = request.form.get('action')
        
        if action == 'save_settings':
            # 1. Process dynamic Hero Brand Badges (Names and URLs)
            import json
            hero_brand_names = request.form.getlist('hero_brand_name[]')
            hero_brand_urls = request.form.getlist('hero_brand_url[]')
            if hero_brand_names:
                badges_list = []
                for name, url in zip(hero_brand_names, hero_brand_urls):
                    name_clean = name.strip()
                    url_clean = url.strip()
                    if name_clean:
                        badges_list.append({
                            'name': name_clean,
                            'url': url_clean if url_clean else f"/products?q={name_clean}"
                        })
                setting_json = SiteSetting.query.filter_by(key='hero_brands_json').first()
                if setting_json:
                    setting_json.value = json.dumps(badges_list)
                else:
                    db.session.add(SiteSetting(key='hero_brands_json', value=json.dumps(badges_list)))
                    
                setting_plain = SiteSetting.query.filter_by(key='hero_brands').first()
                plain_val = ", ".join([b['name'] for b in badges_list])
                if setting_plain:
                    setting_plain.value = plain_val
                else:
                    db.session.add(SiteSetting(key='hero_brands', value=plain_val))

            # 2. Update standard text inputs
            for key, value in request.form.items():
                if key not in ('action', 'hero_brand_name[]', 'hero_brand_url[]', 'show_hero_brands', 'show_product_range', 
                               'show_quality_banner', 'show_why_choose', 'show_featured_products', 'show_stats_ribbon', 
                               'show_whatsapp_button', 'show_mobile_sticky_bar'):
                    setting = SiteSetting.query.filter_by(key=key).first()
                    if setting:
                        setting.value = value
                    else:
                        db.session.add(SiteSetting(key=key, value=value))
                        
            # 3. Update Checkbox Toggles
            toggle_keys = [
                'show_hero_brands', 'show_product_range', 'show_quality_banner',
                'show_why_choose', 'show_featured_products', 'show_stats_ribbon', 
                'show_whatsapp_button', 'show_mobile_sticky_bar'
            ]
            for t_key in toggle_keys:
                val = 'true' if t_key in request.form else 'false'
                setting = SiteSetting.query.filter_by(key=t_key).first()
                if setting:
                    setting.value = val
                else:
                    db.session.add(SiteSetting(key=t_key, value=val))
                    
            # 4. Handle File Uploads for Banners and Logo
            upload_files = {
                'site_logo_file': 'site_logo',
                'hero_image_file': 'hero_image',
                'quality_banner_image_file': 'quality_banner_image'
            }
            for file_field, setting_key in upload_files.items():
                if file_field in request.files:
                    f = request.files[file_field]
                    if f and f.filename and allowed_file(f.filename):
                        fname = secure_filename(f"cms_{setting_key}_{int(time.time())}_{f.filename}")
                        fpath = os.path.join(app.config['UPLOAD_FOLDER'], fname)
                        f.save(fpath)
                        img_val = f"/static/uploads/{fname}"
                        
                        setting = SiteSetting.query.filter_by(key=setting_key).first()
                        if setting:
                            setting.value = img_val
                        else:
                            db.session.add(SiteSetting(key=setting_key, value=img_val))
                            
            db.session.commit()
            flash('Website CMS, homepage hero badges, and appearance settings saved successfully!', 'success')
            
        elif action == 'test_email':
            test_target = request.form.get('test_email_recipient', 'divya.trading06@gmail.com').strip()
            test_subject = "✅ Divya Trading Co. - SMTP Test Email"
            test_body = f"""
            <h3>SMTP Test Email from Divya Trading Co. Website</h3>
            <p>If you are receiving this, your email configuration is working properly!</p>
            <p>Timestamp: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            """
            success, msg = send_email(test_subject, test_target, test_body, app.config)
            if success:
                flash(f'Test email dispatched to {test_target}. Status: {msg}', 'success')
            else:
                flash(f'Test email failed: {msg}', 'danger')
                
        return redirect(url_for('admin_settings'))
        
    settings_records = SiteSetting.query.all()
    settings = {s.key: s.value for s in settings_records}
    email_logs = list(reversed(EMAIL_ACTIVITY_LOGS[-30:]))
    
    # Parse hero badges for admin builder
    import json
    hero_badges_list = []
    hero_json = settings.get('hero_brands_json')
    if hero_json:
        try:
            hero_badges_list = json.loads(hero_json)
        except Exception:
            hero_badges_list = []
    if not hero_badges_list:
        raw_brands = settings.get('hero_brands', 'STORMAC, STORK, ICHINOSE, REGGIANI, HARISH, ZIMMER, STOVEC')
        for b in [x.strip() for x in raw_brands.split(',') if x.strip()]:
            matched_make = MachineMake.query.filter(MachineMake.name.ilike(f"%{b}%")).first()
            hero_badges_list.append({
                'name': b,
                'url': url_for('products', machine=matched_make.slug) if matched_make else url_for('products', q=b)
            })
            
    return render_template(
        'admin/settings.html',
        settings=settings,
        email_logs=email_logs,
        hero_badges_list=hero_badges_list
    )


if __name__ == '__main__':
    print("==================================================")
    print("DIVYA TRADING CO. - Precision Machine Spares B2B")
    print("Catalog & Inquiry System Running at: http://127.0.0.1:5000")
    print("Admin Portal: http://127.0.0.1:5000/admin/login (admin / admin123)")
    print("Customer Portal: http://127.0.0.1:5000/login")
    print("==================================================")
    app.run(debug=True, port=5000)

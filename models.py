from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class Category(db.Model):
    __tablename__ = 'categories'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    slug = db.Column(db.String(140), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    image = db.Column(db.String(255), nullable=True)
    order_index = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    products = db.relationship('Product', backref='category', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'image': self.image,
            'order_index': self.order_index,
            'product_count': len(self.products)
        }


class MachineMake(db.Model):
    __tablename__ = 'machine_makes'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    slug = db.Column(db.String(140), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    products = db.relationship('Product', backref='machine_make', lazy=True)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'slug': self.slug,
            'description': self.description,
            'product_count': len(self.products)
        }


class Product(db.Model):
    __tablename__ = 'products'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    part_number = db.Column(db.String(100), nullable=False, index=True)
    slug = db.Column(db.String(220), nullable=False, unique=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    machine_make_id = db.Column(db.Integer, db.ForeignKey('machine_makes.id'), nullable=True)
    
    # 2-Tier Description System
    short_description = db.Column(db.String(350), nullable=True)  # 1-2 lines for home & catalog cards
    description = db.Column(db.Text, nullable=True)  # Long comprehensive technical description for detail page
    
    specifications = db.Column(db.Text, nullable=True)
    repeat_sizes = db.Column(db.String(255), nullable=True)
    material = db.Column(db.String(150), nullable=True)
    image_url = db.Column(db.String(255), nullable=True)
    is_featured = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True, index=True)
    # stock_status: 'in_stock', 'out_of_stock', 'made_to_order'
    stock_status = db.Column(db.String(30), default='in_stock', index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'part_number': self.part_number,
            'slug': self.slug,
            'category_id': self.category_id,
            'category_name': self.category.name if self.category else '',
            'machine_make_id': self.machine_make_id,
            'machine_make_name': self.machine_make.name if self.machine_make else 'All Makes',
            'short_description': self.short_description or (self.description[:110] + '...' if self.description else ''),
            'description': self.description or '',
            'specifications': self.specifications,
            'repeat_sizes': self.repeat_sizes,
            'material': self.material,
            'image_url': self.image_url or '/static/images/hero_parts.jpg',
            'is_featured': self.is_featured,
            'is_active': self.is_active,
            'stock_status': self.stock_status or 'in_stock',
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }


class CustomerUser(db.Model):
    __tablename__ = 'customer_users'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    company_name = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(150), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(50), nullable=False)
    country = db.Column(db.String(100), default='India')
    city = db.Column(db.String(100), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    inquiries = db.relationship('Inquiry', backref='customer_user', lazy=True, order_by='desc(Inquiry.id)')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'company_name': self.company_name,
            'email': self.email,
            'phone': self.phone,
            'country': self.country,
            'city': self.city,
            'created_at': self.created_at.strftime('%Y-%m-%d') if self.created_at else ''
        }


class Inquiry(db.Model):
    __tablename__ = 'inquiries'
    
    id = db.Column(db.Integer, primary_key=True)
    inquiry_number = db.Column(db.String(50), unique=True, nullable=False, index=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customer_users.id'), nullable=True)
    customer_name = db.Column(db.String(150), nullable=False)
    company_name = db.Column(db.String(200), nullable=True)
    email = db.Column(db.String(150), nullable=False, index=True)
    phone = db.Column(db.String(50), nullable=False)
    country = db.Column(db.String(100), default='India')
    machine_model = db.Column(db.String(150), nullable=True)
    message = db.Column(db.Text, nullable=True)
    
    # Status: 'new', 'contacted', 'quoted', 'completed', 'cancelled'
    status = db.Column(db.String(30), default='new', index=True)
    
    # Quotation Response Details from Admin
    quote_amount = db.Column(db.String(100), nullable=True)  # e.g. "$1,850.00 / ₹1,55,000"
    delivery_timeline = db.Column(db.String(150), nullable=True)  # e.g. "3-5 Business Days"
    payment_terms = db.Column(db.String(200), nullable=True)  # e.g. "50% advance, balance against BL"
    quote_valid_until = db.Column(db.String(100), nullable=True)  # e.g. "30 Days from issue"
    admin_notes = db.Column(db.Text, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    items = db.relationship('InquiryItem', backref='inquiry', lazy=True, cascade='all, delete-orphan')
    messages = db.relationship('InquiryMessage', backref='inquiry', lazy=True, cascade='all, delete-orphan', order_by='InquiryMessage.created_at.asc()')

    def to_dict(self):
        return {
            'id': self.id,
            'inquiry_number': self.inquiry_number,
            'customer_id': self.customer_id,
            'customer_name': self.customer_name,
            'company_name': self.company_name,
            'email': self.email,
            'phone': self.phone,
            'country': self.country,
            'machine_model': self.machine_model,
            'message': self.message,
            'status': self.status,
            'quote_amount': self.quote_amount,
            'delivery_timeline': self.delivery_timeline,
            'payment_terms': self.payment_terms,
            'quote_valid_until': self.quote_valid_until,
            'admin_notes': self.admin_notes,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else '',
            'items': [item.to_dict() for item in self.items],
            'messages': [msg.to_dict() for msg in self.messages]
        }


class InquiryItem(db.Model):
    __tablename__ = 'inquiry_items'
    
    id = db.Column(db.Integer, primary_key=True)
    inquiry_id = db.Column(db.Integer, db.ForeignKey('inquiries.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=True)
    product_name = db.Column(db.String(200), nullable=False)
    part_number = db.Column(db.String(100), nullable=True)
    quantity = db.Column(db.Integer, default=1)
    notes = db.Column(db.String(255), nullable=True)

    product = db.relationship('Product')

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'product_name': self.product_name,
            'part_number': self.part_number,
            'quantity': self.quantity,
            'notes': self.notes,
            'image_url': self.product.image_url if self.product and self.product.image_url else '/static/images/hero_parts.jpg'
        }


class InquiryMessage(db.Model):
    __tablename__ = 'inquiry_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    inquiry_id = db.Column(db.Integer, db.ForeignKey('inquiries.id'), nullable=False)
    sender_type = db.Column(db.String(20), nullable=False)  # 'customer' or 'admin'
    sender_name = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'sender_type': self.sender_type,
            'sender_name': self.sender_name,
            'message': self.message,
            'created_at': self.created_at.strftime('%Y-%m-%d %H:%M') if self.created_at else ''
        }


class AdminUser(db.Model):
    __tablename__ = 'admin_users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    view_password = db.Column(db.String(100), nullable=True)  # Viewable password hint for superadmin management
    role = db.Column(db.String(30), default='superadmin')  # 'superadmin', 'sales_manager', 'product_editor'
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.view_password = password

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_superadmin(self):
        return self.role == 'superadmin'

    def get_role_display(self):
        roles = {
            'superadmin': 'Super Administrator',
            'sales_manager': 'Sales & Quotes Manager',
            'product_editor': 'Catalog & Product Editor'
        }
        return roles.get(self.role, self.role.title())


class SiteSetting(db.Model):
    __tablename__ = 'site_settings'
    
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(100), unique=True, nullable=False)
    value = db.Column(db.Text, nullable=True)
    description = db.Column(db.String(255), nullable=True)

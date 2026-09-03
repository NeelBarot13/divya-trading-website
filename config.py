import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    # Stable Persistent Secret Key
    SECRET_KEY = os.environ.get('SECRET_KEY', 'divya-trading-co-fixed-secret-key-2026-prod-auth-v2')
    
    # 1-Hour Strict Automatic Session Expiration Configuration (3600 seconds)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=1)
    SESSION_COOKIE_NAME = 'dtc_auth_session'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    SESSION_COOKIE_SECURE = False
    SESSION_REFRESH_EACH_REQUEST = True
    
    # Database Configuration: PostgreSQL (Render) / MySQL / Persistent SQLite
    DATABASE_URL = os.environ.get('DATABASE_URL')
    
    # Check if Render persistent disk exists at /var/data
    RENDER_DATA_DIR = '/var/data'
    if os.path.exists(RENDER_DATA_DIR) and os.path.isdir(RENDER_DATA_DIR):
        DEFAULT_SQLITE_PATH = os.path.join(RENDER_DATA_DIR, 'divya_trading.db')
    else:
        DEFAULT_SQLITE_PATH = os.path.join(BASE_DIR, 'divya_trading.db')

    if DATABASE_URL:
        # Render PostgreSQL uses postgres:// which SQLAlchemy requires as postgresql://
        if DATABASE_URL.startswith('postgres://'):
            DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)
        SQLALCHEMY_DATABASE_URI = DATABASE_URL
    elif os.environ.get('USE_MYSQL', 'false').lower() in ('true', '1', 'yes'):
        MYSQL_USER = os.environ.get('MYSQL_USER', 'root')
        MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD', '')
        MYSQL_HOST = os.environ.get('MYSQL_HOST', 'localhost')
        MYSQL_PORT = os.environ.get('MYSQL_PORT', '3306')
        MYSQL_DB = os.environ.get('MYSQL_DB', 'divya_trading_db')
        if MYSQL_PASSWORD:
            SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
        else:
            SQLALCHEMY_DATABASE_URI = f"mysql+pymysql://{MYSQL_USER}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    else:
        # Default SQLite database
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{DEFAULT_SQLITE_PATH}"
        
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Upload settings
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB max upload
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp', 'gif', 'svg'}
    
    # SMTP / Email Configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ('true', '1')
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'false').lower() in ('true', '1')
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', '')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'divya.trading06@gmail.com')
    ADMIN_NOTIFICATION_EMAIL = os.environ.get('ADMIN_NOTIFICATION_EMAIL', 'divya.trading06@gmail.com,neelbarot585@gmail.com')

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret')
    db_url = os.environ.get('DATABASE_URL', '').strip()
    # Render provides postgres:// or postgresql:// but we use pg8000 driver
    if db_url.startswith('postgres://'):
        db_url = db_url.replace('postgres://', 'postgresql+pg8000://', 1)
    elif db_url.startswith('postgresql://'):
        db_url = db_url.replace('postgresql://', 'postgresql+pg8000://', 1)
    elif db_url.startswith('postgresql+pg8000://'):
        pass  # already correct
    elif not db_url:
        # Fallback so `gunicorn wsgi:app` doesn't crash when DATABASE_URL is unset
        db_url = 'sqlite:///kirana.db'
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')
    SHOP_WHATSAPP_NUMBER = os.environ.get('SHOP_WHATSAPP_NUMBER', '')
    MIN_ORDER_AMOUNT = int(os.environ.get('MIN_ORDER_AMOUNT', 100))

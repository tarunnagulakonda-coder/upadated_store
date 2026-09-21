import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'default_secret')
    db_url = os.environ.get('DATABASE_URL', '')
    # Render provides postgresql:// but SQLAlchemy needs postgresql+pg8000:// for pg8000 driver
    if db_url.startswith('postgresql://'):
        db_url = db_url.replace('postgresql://', 'postgresql+pg8000://', 1)
    SQLALCHEMY_DATABASE_URI = db_url
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD', 'admin')
    SHOP_WHATSAPP_NUMBER = os.environ.get('SHOP_WHATSAPP_NUMBER', '')

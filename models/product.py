from datetime import datetime
from models import db

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    subcategory_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    image_url = db.Column(db.String(255))
    expiry_date = db.Column(db.String(20))
    price = db.Column(db.Float, nullable=False)
    unit = db.Column(db.String(50))
    stock = db.Column(db.String(50), default="Available")
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    category = db.relationship('Category', foreign_keys=[category_id], backref=db.backref('products', lazy=True))
    subcategory = db.relationship('Category', foreign_keys=[subcategory_id], backref=db.backref('sub_products', lazy=True))

    @property
    def image_src(self):
        """Template-ready image src (None when no image).

        Handles legacy bare filenames, "uploads/..." paths and future
        absolute Cloudinary/object-storage URLs.
        """
        try:
            from utils.product_images import resolve_product_image_src
        except ImportError:
            if not self.image_url:
                return None
            value = (self.image_url or '').strip()
            if not value:
                return None
            if value.startswith(('http://', 'https://', 'data:')):
                return value
            normalized = value.replace('\\', '/').lstrip('/')
            return normalized if normalized.startswith('uploads/') else f'uploads/{normalized}'
        return resolve_product_image_src(self.image_url)

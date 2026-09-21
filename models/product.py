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

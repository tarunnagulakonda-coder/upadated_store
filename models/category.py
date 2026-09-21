from datetime import datetime
from models import db

class Category(db.Model):
    __tablename__ = 'categories'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    icon = db.Column(db.String(50))
    parent_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    subcategories = db.relationship('Category', 
                                    backref=db.backref('parent', remote_side=[id]),
                                    cascade="all, delete-orphan")
